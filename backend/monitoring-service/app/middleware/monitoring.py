#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 监控中间件

提供请求监控和性能追踪功能
"""

import time
import asyncio
from typing import Callable, Optional, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge

from app.core.logging import get_logger
from app.core.security import get_client_ip
from app.core.cache import get_cache_manager
from app.middleware.request_id import get_request_id

logger = get_logger(__name__)

# Prometheus指标
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

request_size = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

response_size = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """监控中间件"""
    
    def __init__(
        self,
        app,
        enable_prometheus: bool = True,
        enable_detailed_logging: bool = True,
        slow_request_threshold: float = 1.0,
        skip_paths: Optional[set] = None
    ):
        """
        初始化监控中间件
        
        Args:
            app: FastAPI应用实例
            enable_prometheus: 是否启用Prometheus指标
            enable_detailed_logging: 是否启用详细日志
            slow_request_threshold: 慢请求阈值（秒）
            skip_paths: 跳过监控的路径集合
        """
        super().__init__(app)
        self.enable_prometheus = enable_prometheus
        self.enable_detailed_logging = enable_detailed_logging
        self.slow_request_threshold = slow_request_threshold
        self.skip_paths = skip_paths or {"/health", "/ready", "/live", "/metrics"}
        self.cache_manager = get_cache_manager()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 跳过特定路径的监控
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        start_time = time.time()
        request_id = get_request_id()
        client_ip = get_client_ip(request)
        
        # 增加活跃请求计数
        if self.enable_prometheus:
            active_requests.inc()
        
        # 记录请求大小
        request_size_bytes = 0
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                request_size_bytes = int(content_length)
            except ValueError:
                pass
        
        # 获取端点信息
        endpoint = self._get_endpoint_name(request)
        method = request.method
        
        try:
            # 记录请求开始
            if self.enable_detailed_logging:
                logger.info(
                    f"Request started",
                    extra={
                        'request_id': request_id,
                        'method': method,
                        'endpoint': endpoint,
                        'client_ip': client_ip,
                        'user_agent': request.headers.get('user-agent', ''),
                        'request_size': request_size_bytes
                    }
                )
            
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            duration = time.time() - start_time
            status_code = response.status_code
            
            # 获取响应大小
            response_size_bytes = 0
            if hasattr(response, 'headers') and 'content-length' in response.headers:
                try:
                    response_size_bytes = int(response.headers['content-length'])
                except ValueError:
                    pass
            
            # 更新Prometheus指标
            if self.enable_prometheus:
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code
                ).inc()
                
                request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                if request_size_bytes > 0:
                    request_size.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(request_size_bytes)
                
                if response_size_bytes > 0:
                    response_size.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(response_size_bytes)
                
                active_requests.dec()
            
            # 记录请求完成
            log_level = "warning" if duration > self.slow_request_threshold else "info"
            log_message = f"Request completed{' (SLOW)' if duration > self.slow_request_threshold else ''}"
            
            if self.enable_detailed_logging:
                getattr(logger, log_level)(
                    log_message,
                    extra={
                        'request_id': request_id,
                        'method': method,
                        'endpoint': endpoint,
                        'status_code': status_code,
                        'duration': round(duration, 3),
                        'client_ip': client_ip,
                        'request_size': request_size_bytes,
                        'response_size': response_size_bytes
                    }
                )
            
            # 记录性能指标到缓存
            await self._record_performance_metrics(
                endpoint, method, duration, status_code, request_size_bytes, response_size_bytes
            )
            
            # 检查异常状态码
            if status_code >= 400:
                await self._record_error_metrics(endpoint, method, status_code, client_ip)
            
            return response
            
        except Exception as e:
            # 处理异常
            duration = time.time() - start_time
            
            if self.enable_prometheus:
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=500
                ).inc()
                
                request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                active_requests.dec()
            
            # 记录异常
            logger.error(
                f"Request failed with exception",
                extra={
                    'request_id': request_id,
                    'method': method,
                    'endpoint': endpoint,
                    'duration': round(duration, 3),
                    'client_ip': client_ip,
                    'error': str(e)
                },
                exc_info=True
            )
            
            # 记录错误指标
            await self._record_error_metrics(endpoint, method, 500, client_ip)
            
            raise
    
    def _get_endpoint_name(self, request: Request) -> str:
        """获取端点名称"""
        # 尝试从路由获取端点名称
        if hasattr(request, 'scope') and 'route' in request.scope:
            route = request.scope['route']
            if hasattr(route, 'path'):
                return route.path
        
        # 回退到URL路径
        path = request.url.path
        
        # 简化路径（移除ID等动态部分）
        path_parts = path.split('/')
        simplified_parts = []
        
        for part in path_parts:
            if part.isdigit():
                simplified_parts.append('{id}')
            elif len(part) == 36 and '-' in part:  # UUID
                simplified_parts.append('{uuid}')
            else:
                simplified_parts.append(part)
        
        return '/'.join(simplified_parts)
    
    async def _record_performance_metrics(self, endpoint: str, method: str, duration: float, 
                                        status_code: int, request_size: int, response_size: int):
        """记录性能指标到缓存"""
        try:
            current_time = int(time.time())
            minute_key = current_time // 60  # 按分钟聚合
            
            # 性能指标键
            perf_key = f"metrics:performance:{endpoint}:{method}:{minute_key}"
            
            # 获取现有指标
            existing_metrics = await self.cache_manager.get(perf_key)
            if existing_metrics is None:
                metrics = {
                    'count': 0,
                    'total_duration': 0,
                    'min_duration': float('inf'),
                    'max_duration': 0,
                    'status_codes': {},
                    'total_request_size': 0,
                    'total_response_size': 0
                }
            else:
                metrics = existing_metrics
            
            # 更新指标
            metrics['count'] += 1
            metrics['total_duration'] += duration
            metrics['min_duration'] = min(metrics['min_duration'], duration)
            metrics['max_duration'] = max(metrics['max_duration'], duration)
            metrics['total_request_size'] += request_size
            metrics['total_response_size'] += response_size
            
            # 状态码统计
            status_key = str(status_code)
            metrics['status_codes'][status_key] = metrics['status_codes'].get(status_key, 0) + 1
            
            # 保存指标（保存5分钟）
            await self.cache_manager.set(perf_key, metrics, expire=300)
            
        except Exception as e:
            logger.error(f"Failed to record performance metrics: {e}", exc_info=True)
    
    async def _record_error_metrics(self, endpoint: str, method: str, status_code: int, client_ip: str):
        """记录错误指标"""
        try:
            current_time = int(time.time())
            minute_key = current_time // 60
            
            # 错误指标键
            error_key = f"metrics:errors:{endpoint}:{method}:{minute_key}"
            
            # 获取现有错误指标
            existing_errors = await self.cache_manager.get(error_key)
            if existing_errors is None:
                errors = {
                    'total_errors': 0,
                    'status_codes': {},
                    'client_ips': {}
                }
            else:
                errors = existing_errors
            
            # 更新错误指标
            errors['total_errors'] += 1
            
            status_key = str(status_code)
            errors['status_codes'][status_key] = errors['status_codes'].get(status_key, 0) + 1
            
            errors['client_ips'][client_ip] = errors['client_ips'].get(client_ip, 0) + 1
            
            # 保存错误指标（保存5分钟）
            await self.cache_manager.set(error_key, errors, expire=300)
            
        except Exception as e:
            logger.error(f"Failed to record error metrics: {e}", exc_info=True)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(
        self,
        app,
        memory_threshold: int = 100 * 1024 * 1024,  # 100MB
        cpu_threshold: float = 80.0,  # 80%
        check_interval: int = 60  # 60秒
    ):
        """
        初始化性能监控中间件
        
        Args:
            app: FastAPI应用实例
            memory_threshold: 内存使用阈值（字节）
            cpu_threshold: CPU使用阈值（百分比）
            check_interval: 检查间隔（秒）
        """
        super().__init__(app)
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        self.check_interval = check_interval
        self.last_check = 0
        self.cache_manager = get_cache_manager()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 定期检查系统性能
        current_time = time.time()
        if current_time - self.last_check > self.check_interval:
            await self._check_system_performance()
            self.last_check = current_time
        
        return await call_next(request)
    
    async def _check_system_performance(self):
        """检查系统性能"""
        try:
            import psutil
            
            # 获取内存使用情况
            memory = psutil.virtual_memory()
            memory_used = memory.used
            memory_percent = memory.percent
            
            # 获取CPU使用情况
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 获取磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 记录性能指标
            performance_data = {
                'timestamp': int(time.time()),
                'memory': {
                    'used': memory_used,
                    'percent': memory_percent,
                    'available': memory.available
                },
                'cpu': {
                    'percent': cpu_percent
                },
                'disk': {
                    'used': disk.used,
                    'percent': disk_percent,
                    'free': disk.free
                }
            }
            
            # 保存到缓存
            perf_key = f"system:performance:{int(time.time() // 60)}"
            await self.cache_manager.set(perf_key, performance_data, expire=3600)
            
            # 检查阈值并记录警告
            if memory_used > self.memory_threshold:
                logger.warning(
                    f"High memory usage detected",
                    extra={
                        'memory_used': memory_used,
                        'memory_percent': memory_percent,
                        'threshold': self.memory_threshold
                    }
                )
            
            if cpu_percent > self.cpu_threshold:
                logger.warning(
                    f"High CPU usage detected",
                    extra={
                        'cpu_percent': cpu_percent,
                        'threshold': self.cpu_threshold
                    }
                )
            
            if disk_percent > 90:  # 磁盘使用超过90%
                logger.warning(
                    f"High disk usage detected",
                    extra={
                        'disk_percent': disk_percent,
                        'disk_used': disk.used,
                        'disk_free': disk.free
                    }
                )
            
        except ImportError:
            logger.warning("psutil not available, skipping system performance check")
        except Exception as e:
            logger.error(f"Failed to check system performance: {e}", exc_info=True)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志中间件

处理请求日志记录和性能监控。
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import json

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    日志中间件类
    
    记录所有HTTP请求的详细信息，包括请求时间、响应时间、状态码等。
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求日志
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应对象
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 记录请求信息
        logger.info(
            f"请求开始 - ID: {request_id}, "
            f"方法: {request.method}, "
            f"路径: {request.url.path}, "
            f"查询参数: {dict(request.query_params)}, "
            f"客户端IP: {client_ip}, "
            f"用户代理: {request.headers.get('user-agent', 'Unknown')}"
        )
        
        # 记录请求体（仅对POST/PUT/PATCH请求）
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._log_request_body(request, request_id)
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # 记录响应信息
            logger.info(
                f"请求完成 - ID: {request_id}, "
                f"状态码: {response.status_code}, "
                f"处理时间: {process_time:.4f}s"
            )
            
            # 记录慢请求
            if process_time > 1.0:  # 超过1秒的请求
                logger.warning(
                    f"慢请求警告 - ID: {request_id}, "
                    f"路径: {request.url.path}, "
                    f"处理时间: {process_time:.4f}s"
                )
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误信息
            logger.error(
                f"请求失败 - ID: {request_id}, "
                f"错误: {str(e)}, "
                f"处理时间: {process_time:.4f}s",
                exc_info=True
            )
            
            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": "内部服务器错误",
                    "request_id": request_id,
                    "timestamp": time.time()
                },
                headers={"X-Request-ID": request_id}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实IP地址
        
        Args:
            request: HTTP请求对象
            
        Returns:
            str: 客户端IP地址
        """
        # 检查代理头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        return request.client.host if request.client else "unknown"
    
    async def _log_request_body(self, request: Request, request_id: str) -> None:
        """
        记录请求体内容
        
        Args:
            request: HTTP请求对象
            request_id: 请求ID
        """
        try:
            # 获取内容类型
            content_type = request.headers.get("content-type", "")
            
            # 只记录JSON和表单数据
            if "application/json" in content_type:
                body = await request.body()
                if body:
                    try:
                        json_body = json.loads(body)
                        # 过滤敏感信息
                        filtered_body = self._filter_sensitive_data(json_body)
                        logger.debug(
                            f"请求体 - ID: {request_id}, "
                            f"内容: {json.dumps(filtered_body, ensure_ascii=False)}"
                        )
                    except json.JSONDecodeError:
                        logger.debug(
                            f"请求体 - ID: {request_id}, "
                            f"内容: 无效的JSON格式"
                        )
            elif "application/x-www-form-urlencoded" in content_type:
                logger.debug(
                    f"请求体 - ID: {request_id}, "
                    f"内容类型: 表单数据"
                )
            
        except Exception as e:
            logger.warning(f"记录请求体失败 - ID: {request_id}, 错误: {e}")
    
    def _filter_sensitive_data(self, data: dict) -> dict:
        """
        过滤敏感数据
        
        Args:
            data: 原始数据
            
        Returns:
            dict: 过滤后的数据
        """
        sensitive_keys = {
            "password", "token", "secret", "key", "auth",
            "credential", "private", "confidential"
        }
        
        filtered = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                filtered[key] = "[FILTERED]"
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
            elif isinstance(value, list):
                filtered[key] = [
                    self._filter_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered[key] = value
        
        return filtered


def setup_logging_middleware(app: FastAPI) -> None:
    """
    设置日志中间件
    
    Args:
        app: FastAPI应用实例
    """
    try:
        # 添加日志中间件
        app.middleware("http")(LoggingMiddleware(app))
        
        logger.info("日志中间件设置完成")
        
    except Exception as e:
        logger.error(f"设置日志中间件失败: {e}")
        raise


def get_request_id(request: Request) -> str:
    """
    获取请求ID
    
    Args:
        request: HTTP请求对象
        
    Returns:
        str: 请求ID
    """
    return getattr(request.state, "request_id", "unknown")
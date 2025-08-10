#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 日志配置

结构化日志配置和管理
"""

import os
import sys
import json
import logging
import logging.config
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from .config import settings


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hostname = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        # 基础日志信息
        log_entry = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.thread,
            'hostname': self.hostname,
            'service': 'monitoring-service'
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # 从record中提取自定义字段
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'extra_fields'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为彩色文本"""
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 格式化时间
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建日志消息
        log_message = (
            f"{color}[{timestamp}] {record.levelname:8} "
            f"{record.name}:{record.lineno} - {record.getMessage()}{reset}"
        )
        
        # 添加异常信息
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"
        
        return log_message


class ContextFilter(logging.Filter):
    """上下文过滤器 - 添加请求上下文信息"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加上下文信息到日志记录"""
        # 尝试获取请求上下文
        try:
            from contextvars import copy_context
            context = copy_context()
            
            # 添加请求ID（如果存在）
            request_id = context.get('request_id', None)
            if request_id:
                record.request_id = request_id
            
            # 添加用户ID（如果存在）
            user_id = context.get('user_id', None)
            if user_id:
                record.user_id = user_id
            
            # 添加IP地址（如果存在）
            client_ip = context.get('client_ip', None)
            if client_ip:
                record.client_ip = client_ip
                
        except Exception:
            # 如果获取上下文失败，继续处理
            pass
        
        return True


class SensitiveDataFilter(logging.Filter):
    """敏感数据过滤器 - 过滤敏感信息"""
    
    SENSITIVE_PATTERNS = [
        'password', 'passwd', 'pwd', 'secret', 'key', 'token',
        'authorization', 'auth', 'credential', 'api_key'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤敏感数据"""
        message = record.getMessage().lower()
        
        # 检查是否包含敏感信息
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # 替换敏感信息
                record.msg = self._mask_sensitive_data(str(record.msg))
                break
        
        return True
    
    def _mask_sensitive_data(self, message: str) -> str:
        """掩码敏感数据"""
        import re
        
        # 掩码密码等敏感信息
        patterns = [
            (r'(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\',}]+)', r'\1=***'),
            (r'(secret|key|token)\s*[=:]\s*["\']?([^\s"\',}]+)', r'\1=***'),
            (r'(authorization|auth)\s*[=:]\s*["\']?([^\s"\',}]+)', r'\1=***'),
        ]
        
        for pattern, replacement in patterns:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        
        return message


def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    if settings.LOG_FILE:
        log_dir = Path(settings.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # 根据配置选择格式化器
    if settings.LOG_FORMAT.lower() == 'json':
        formatter_class = JSONFormatter
        formatter_args = {}
    else:
        formatter_class = ColoredFormatter if sys.stdout.isatty() else logging.Formatter
        formatter_args = {
            'fmt': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    
    # 日志配置
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                '()': formatter_class,
                **formatter_args
            },
            'json': {
                '()': JSONFormatter
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'filters': {
            'context': {
                '()': ContextFilter
            },
            'sensitive': {
                '()': SensitiveDataFilter
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': settings.LOG_LEVEL,
                'formatter': 'default',
                'filters': ['context', 'sensitive'],
                'stream': sys.stdout
            }
        },
        'loggers': {
            # 应用日志
            'app': {
                'level': settings.LOG_LEVEL,
                'handlers': ['console'],
                'propagate': False
            },
            # FastAPI日志
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            # SQLAlchemy日志
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False
            },
            # Redis日志
            'redis': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': settings.LOG_LEVEL,
            'handlers': ['console']
        }
    }
    
    # 添加文件处理器（如果配置了日志文件）
    if settings.LOG_FILE:
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': settings.LOG_LEVEL,
            'formatter': 'json',
            'filters': ['context', 'sensitive'],
            'filename': settings.LOG_FILE,
            'maxBytes': settings.LOG_MAX_SIZE,
            'backupCount': settings.LOG_BACKUP_COUNT,
            'encoding': 'utf-8'
        }
        
        # 为所有日志器添加文件处理器
        for logger_config in config['loggers'].values():
            logger_config['handlers'].append('file')
        config['root']['handlers'].append('file')
    
    # 应用配置
    logging.config.dictConfig(config)
    
    # 设置第三方库日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # 记录启动信息
    logger = logging.getLogger('app.core.logging')
    logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}, Format: {settings.LOG_FORMAT}")
    if settings.LOG_FILE:
        logger.info(f"Log file: {settings.LOG_FILE}")


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(f"app.{name}")


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器 - 添加额外上下文"""
    
    def process(self, msg, kwargs):
        """处理日志消息"""
        # 添加额外字段到record
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        kwargs['extra'].update(self.extra)
        return msg, kwargs


def get_context_logger(name: str, **context) -> LoggerAdapter:
    """获取带上下文的日志器"""
    logger = get_logger(name)
    return LoggerAdapter(logger, context)


# 日志装饰器
def log_function_call(logger: logging.Logger = None, level: int = logging.INFO):
    """函数调用日志装饰器"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            
            # 记录函数调用
            logger.log(
                level,
                f"Calling {func.__name__}",
                extra={
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功完成
                execution_time = time.time() - start_time
                logger.log(
                    level,
                    f"Completed {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'execution_time': execution_time,
                        'status': 'success'
                    }
                )
                
                return result
                
            except Exception as e:
                # 记录异常
                execution_time = time.time() - start_time
                logger.error(
                    f"Error in {func.__name__}: {e}",
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'execution_time': execution_time,
                        'status': 'error',
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            
            # 记录函数调用
            logger.log(
                level,
                f"Calling {func.__name__}",
                extra={
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            )
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功完成
                execution_time = time.time() - start_time
                logger.log(
                    level,
                    f"Completed {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'execution_time': execution_time,
                        'status': 'success'
                    }
                )
                
                return result
                
            except Exception as e:
                # 记录异常
                execution_time = time.time() - start_time
                logger.error(
                    f"Error in {func.__name__}: {e}",
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'execution_time': execution_time,
                        'status': 'error',
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 性能日志
def log_performance(threshold: float = 1.0, logger: logging.Logger = None):
    """性能日志装饰器"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > threshold:
                logger.warning(
                    f"Slow function execution: {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'execution_time': execution_time,
                        'threshold': threshold,
                        'performance_issue': True
                    }
                )
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > threshold:
                logger.warning(
                    f"Slow function execution: {func.__name__}",
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'execution_time': execution_time,
                        'threshold': threshold,
                        'performance_issue': True
                    }
                )
            
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 审计日志
def audit_log(action: str, resource: str = None, logger: logging.Logger = None):
    """审计日志装饰器"""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger('audit')
            
            # 尝试获取用户信息
            user_id = None
            for arg in args:
                if hasattr(arg, 'id'):
                    user_id = getattr(arg, 'id', None)
                    break
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功的审计事件
                logger.info(
                    f"Audit: {action}",
                    extra={
                        'audit': True,
                        'action': action,
                        'resource': resource,
                        'user_id': user_id,
                        'function': func.__name__,
                        'status': 'success'
                    }
                )
                
                return result
                
            except Exception as e:
                # 记录失败的审计事件
                logger.warning(
                    f"Audit: {action} failed",
                    extra={
                        'audit': True,
                        'action': action,
                        'resource': resource,
                        'user_id': user_id,
                        'function': func.__name__,
                        'status': 'failed',
                        'error': str(e)
                    }
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger('audit')
            
            # 尝试获取用户信息
            user_id = None
            for arg in args:
                if hasattr(arg, 'id'):
                    user_id = getattr(arg, 'id', None)
                    break
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功的审计事件
                logger.info(
                    f"Audit: {action}",
                    extra={
                        'audit': True,
                        'action': action,
                        'resource': resource,
                        'user_id': user_id,
                        'function': func.__name__,
                        'status': 'success'
                    }
                )
                
                return result
                
            except Exception as e:
                # 记录失败的审计事件
                logger.warning(
                    f"Audit: {action} failed",
                    extra={
                        'audit': True,
                        'action': action,
                        'resource': resource,
                        'user_id': user_id,
                        'function': func.__name__,
                        'status': 'failed',
                        'error': str(e)
                    }
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 日志工具函数
def log_dict(logger: logging.Logger, level: int, message: str, data: Dict[str, Any]):
    """记录字典数据"""
    logger.log(level, message, extra={'data': data})


def log_exception(logger: logging.Logger, message: str, exc: Exception):
    """记录异常信息"""
    logger.error(
        message,
        extra={
            'exception_type': type(exc).__name__,
            'exception_message': str(exc)
        },
        exc_info=True
    )


# 初始化日志（如果还未初始化）
if not logging.getLogger().handlers:
    setup_logging()
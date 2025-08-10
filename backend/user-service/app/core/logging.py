#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 日志配置模块

提供统一的日志配置和管理
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

from .config import settings


def setup_logging() -> None:
    """
    设置日志配置
    """
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 日志配置
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": log_dir / "user-service.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": log_dir / "user-service-error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "cashup": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            }
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file", "error_file"]
        }
    }
    
    # 在生产环境中添加JSON格式日志
    if not settings.DEBUG:
        logging_config["handlers"]["json_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": log_dir / "user-service.json.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "encoding": "utf-8"
        }
        logging_config["loggers"]["cashup"]["handlers"].append("json_file")
    
    # 应用日志配置
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(f"cashup.{name}")


class LoggerMixin:
    """
    日志记录器混入类
    
    为类提供日志记录功能
    """
    
    @property
    def logger(self) -> logging.Logger:
        """
        获取当前类的日志记录器
        
        Returns:
            logging.Logger: 日志记录器实例
        """
        return get_logger(self.__class__.__name__)


# 预定义的日志记录器
api_logger = get_logger("api")
auth_logger = get_logger("auth")
db_logger = get_logger("database")
redis_logger = get_logger("redis")
service_logger = get_logger("service")
security_logger = get_logger("security")


def log_function_call(func_name: str, args: tuple = (), kwargs: dict = None) -> None:
    """
    记录函数调用日志
    
    Args:
        func_name: 函数名称
        args: 位置参数
        kwargs: 关键字参数
    """
    kwargs = kwargs or {}
    logger = get_logger("function_call")
    logger.debug(f"调用函数: {func_name}, 参数: args={args}, kwargs={kwargs}")


def log_api_request(method: str, path: str, user_id: str = None, ip: str = None) -> None:
    """
    记录API请求日志
    
    Args:
        method: HTTP方法
        path: 请求路径
        user_id: 用户ID
        ip: 客户端IP
    """
    api_logger.info(f"API请求: {method} {path}", extra={
        "method": method,
        "path": path,
        "user_id": user_id,
        "client_ip": ip
    })


def log_auth_event(event: str, user_id: str = None, username: str = None, success: bool = True, details: dict = None) -> None:
    """
    记录认证事件日志
    
    Args:
        event: 事件类型
        user_id: 用户ID
        username: 用户名
        success: 是否成功
        details: 额外详情
    """
    details = details or {}
    level = logging.INFO if success else logging.WARNING
    auth_logger.log(level, f"认证事件: {event}", extra={
        "event": event,
        "user_id": user_id,
        "username": username,
        "success": success,
        "details": details
    })


def log_security_event(event: str, severity: str = "INFO", user_id: str = None, ip: str = None, details: dict = None) -> None:
    """
    记录安全事件日志
    
    Args:
        event: 事件描述
        severity: 严重程度 (INFO, WARNING, ERROR, CRITICAL)
        user_id: 用户ID
        ip: 客户端IP
        details: 额外详情
    """
    details = details or {}
    level = getattr(logging, severity.upper(), logging.INFO)
    security_logger.log(level, f"安全事件: {event}", extra={
        "event": event,
        "severity": severity,
        "user_id": user_id,
        "client_ip": ip,
        "details": details
    })
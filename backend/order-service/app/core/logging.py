#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务日志配置

配置结构化日志记录
"""

import logging
import logging.config
import sys
from typing import Dict, Any
from pathlib import Path
import json
from datetime import datetime

from .config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """
    JSON格式日志格式化器
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为JSON格式
        
        Args:
            record: 日志记录
            
        Returns:
            str: JSON格式的日志字符串
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "service": "order-service",
            "version": settings.APP_VERSION
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'order_id'):
            log_entry["order_id"] = record.order_id
        
        if hasattr(record, 'exchange'):
            log_entry["exchange"] = record.exchange
        
        if hasattr(record, 'symbol'):
            log_entry["symbol"] = record.symbol
        
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms
        
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = record.status_code
        
        if hasattr(record, 'method'):
            log_entry["method"] = record.method
        
        if hasattr(record, 'path'):
            log_entry["path"] = record.path
        
        if hasattr(record, 'ip'):
            log_entry["ip"] = record.ip
        
        if hasattr(record, 'user_agent'):
            log_entry["user_agent"] = record.user_agent
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    彩色控制台日志格式化器
    """
    
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
        """
        格式化日志记录为彩色格式
        
        Args:
            record: 日志记录
            
        Returns:
            str: 彩色格式的日志字符串
        """
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 基础格式
        log_format = (
            f"{color}[{record.levelname:8}]{reset} "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} "
            f"| {record.name:20} | {record.funcName:15} | "
            f"{record.getMessage()}"
        )
        
        # 添加额外信息
        extras = []
        if hasattr(record, 'request_id'):
            extras.append(f"req_id={record.request_id}")
        if hasattr(record, 'user_id'):
            extras.append(f"user_id={record.user_id}")
        if hasattr(record, 'order_id'):
            extras.append(f"order_id={record.order_id}")
        if hasattr(record, 'duration_ms'):
            extras.append(f"duration={record.duration_ms}ms")
        
        if extras:
            log_format += f" [{', '.join(extras)}]"
        
        # 添加异常信息
        if record.exc_info:
            log_format += f"\n{self.formatException(record.exc_info)}"
        
        return log_format


def get_logging_config() -> Dict[str, Any]:
    """
    获取日志配置
    
    Returns:
        Dict[str, Any]: 日志配置字典
    """
    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "colored": {
                "()": ColoredFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "colored" if sys.stdout.isatty() else "json",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/order-service.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/order-service-error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/order-service-access.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            # 应用日志
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
                "propagate": False
            },
            # 访问日志
            "app.access": {
                "level": "INFO",
                "handlers": ["access_file"],
                "propagate": False
            },
            # 订单相关日志
            "app.orders": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # 交易所相关日志
            "app.exchange": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # 数据库日志
            "app.database": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # SQLAlchemy日志
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # HTTP客户端日志
            "httpx": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # Uvicorn日志
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["access_file"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console", "error_file"]
        }
    }
    
    return config


def setup_logging():
    """
    设置日志配置
    """
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # 设置第三方库日志级别
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger = logging.getLogger("app")
    logger.info("Logging configuration initialized")


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(f"app.{name}")


class LoggerAdapter(logging.LoggerAdapter):
    """
    日志适配器，用于添加上下文信息
    """
    
    def process(self, msg, kwargs):
        """
        处理日志消息，添加额外信息
        
        Args:
            msg: 日志消息
            kwargs: 关键字参数
            
        Returns:
            tuple: 处理后的消息和关键字参数
        """
        # 添加额外字段到日志记录
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs


def get_context_logger(name: str, **context) -> LoggerAdapter:
    """
    获取带上下文的日志记录器
    
    Args:
        name: 日志记录器名称
        **context: 上下文信息
        
    Returns:
        LoggerAdapter: 带上下文的日志记录器
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)


# 预定义的日志记录器
app_logger = get_logger("app")
order_logger = get_logger("orders")
exchange_logger = get_logger("exchange")
database_logger = get_logger("database")
access_logger = get_logger("access")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易服务日志配置

统一配置应用日志系统
"""

import logging
import logging.config
from typing import Dict, Any

from .config import settings


def setup_logging() -> None:
    """
    设置应用日志配置
    
    配置日志格式、级别和输出目标
    """
    # 日志配置字典
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed" if settings.DEBUG else "default",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": "logs/trading-service.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/trading-service-error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "cashup.trading": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"] if not settings.DEBUG else ["console"],
                "propagate": False
            },
            "cashup.trading.middleware": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"] if not settings.DEBUG else ["console"],
                "propagate": False
            },
            "cashup.trading.performance": {
                "level": "WARNING",
                "handlers": ["console", "file"] if not settings.DEBUG else ["console"],
                "propagate": False
            },
            "cashup.trading.ratelimit": {
                "level": "WARNING",
                "handlers": ["console", "file"] if not settings.DEBUG else ["console"],
                "propagate": False
            },
            "cashup.trading.orders": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"] if not settings.DEBUG else ["console"],
                "propagate": False
            },
            "cashup.trading.positions": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"] if not settings.DEBUG else ["console"],
                "propagate": False
            },
            "cashup.trading.risk": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"] if not settings.DEBUG else ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console"]
        }
    }
    
    # 创建日志目录
    import os
    os.makedirs("logs", exist_ok=True)
    
    # 应用日志配置
    logging.config.dictConfig(logging_config)
    
    # 设置第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    # 记录日志系统启动
    logger = logging.getLogger("cashup.trading")
    logger.info("Trading service logging system initialized")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Debug mode: {settings.DEBUG}")


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(f"cashup.trading.{name}")
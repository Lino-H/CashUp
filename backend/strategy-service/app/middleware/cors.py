#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORS中间件配置

处理跨域资源共享(CORS)设置。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


def setup_cors(app: FastAPI) -> None:
    """
    设置CORS中间件
    
    Args:
        app: FastAPI应用实例
    """
    try:
        # 添加CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=settings.allowed_methods,
            allow_headers=settings.allowed_headers,
            expose_headers=[
                "X-Total-Count",
                "X-Page-Count",
                "X-Current-Page",
                "X-Per-Page",
                "X-Request-ID"
            ],
            max_age=600  # 预检请求缓存时间（秒）
        )
        
        logger.info("CORS中间件设置完成")
        logger.debug(f"允许的源: {settings.allowed_origins}")
        logger.debug(f"允许的方法: {settings.allowed_methods}")
        logger.debug(f"允许的头部: {settings.allowed_headers}")
        
    except Exception as e:
        logger.error(f"设置CORS中间件失败: {e}")
        raise
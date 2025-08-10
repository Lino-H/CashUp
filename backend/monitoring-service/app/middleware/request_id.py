#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 请求ID中间件

为每个请求生成唯一ID，用于日志追踪
"""

import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from contextvars import ContextVar

from app.core.logging import get_logger

logger = get_logger(__name__)

# 请求ID上下文变量
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件"""
    
    def __init__(self, app, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 从请求头获取请求ID，如果没有则生成新的
        request_id = request.headers.get(self.header_name)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # 设置请求ID到上下文变量
        request_id_var.set(request_id)
        
        # 将请求ID添加到请求状态
        request.state.request_id = request_id
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 将请求ID添加到响应头
            response.headers[self.header_name] = request_id
            
            return response
            
        except Exception as e:
            logger.error(
                f"Request processing failed",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'url': str(request.url),
                    'error': str(e)
                },
                exc_info=True
            )
            raise


def get_request_id() -> str:
    """获取当前请求ID"""
    return request_id_var.get()
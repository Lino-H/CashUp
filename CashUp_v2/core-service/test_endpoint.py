#!/usr/bin/env python3
"""
测试端点 - 用于调试请求体解析问题
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="测试API")

class TestRequest(BaseModel):
    username: str
    password: str

@app.post("/test/login")
async def test_login(request: TestRequest):
    """测试登录端点"""
    return {
        "message": "请求解析成功",
        "username": request.username,
        "password_length": len(request.password)
    }

@app.get("/test/health")
async def test_health():
    """测试健康检查"""
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
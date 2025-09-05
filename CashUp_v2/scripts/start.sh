#!/bin/bash

# CashUp v2 启动脚本

set -e

echo "🚀 启动 CashUp v2..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查Docker Compose是否可用
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Docker Compose未安装"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs data backups strategies/templates strategies/examples strategies/custom ssl

# 设置权限
chmod +x scripts/*.sh

# 加载环境变量
if [ -f .env ]; then
    echo "🔧 加载环境变量..."
    export $(cat .env | xargs)
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 构建并启动服务
echo "🏗️ 构建服务镜像..."
docker-compose build --no-cache

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 运行健康检查
echo "🏥 运行健康检查..."
./scripts/health-check.sh

echo "✅ CashUp v2 启动完成！"
echo "🌐 前端地址: http://localhost:3000"
echo "📚 API文档: http://localhost:8001/docs"
echo "📊 系统状态: http://localhost:8001/health"
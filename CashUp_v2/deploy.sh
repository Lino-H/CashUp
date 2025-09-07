#!/bin/bash

# 生产环境部署脚本
echo "🚀 开始部署 CashUp 生产环境..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装"
    exit 1
fi

# 停止现有的服务
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.prod.yml down --remove-orphans

# 构建镜像
echo "🔨 构建服务镜像..."
docker-compose -f docker-compose.prod.yml build --no-cache

# 启动服务
echo "🚀 启动生产环境服务..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

# 健康检查
echo "🏥 执行健康检查..."
docker-compose -f docker-compose.prod.yml exec core-service curl -f http://localhost:8001/health || echo "❌ 核心服务健康检查失败"
docker-compose -f docker-compose.prod.yml exec trading-engine curl -f http://localhost:8002/health || echo "❌ 交易引擎健康检查失败"
docker-compose -f docker-compose.prod.yml exec strategy-platform curl -f http://localhost:8003/health || echo "❌ 策略平台健康检查失败"
docker-compose -f docker-compose.prod.yml exec notification-service curl -f http://localhost:8004/health || echo "❌ 通知服务健康检查失败"

echo "✅ 生产环境部署完成！"
echo "🌐 前端地址: http://localhost"
echo "📖 API文档: http://localhost/docs (各服务文档端口)"
echo "🔧 管理命令: docker-compose -f docker-compose.prod.yml [up|down|logs|ps]"
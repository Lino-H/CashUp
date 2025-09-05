#!/bin/bash

# CashUp v2 健康检查脚本

set -e

echo "🏥 执行健康检查..."

# 检查核心服务
echo "📡 检查核心服务..."
curl -f http://localhost:8001/health || echo "❌ 核心服务不可用"

# 检查交易引擎
echo "📈 检查交易引擎..."
curl -f http://localhost:8002/health || echo "❌ 交易引擎不可用"

# 检查策略平台
echo "🎯 检查策略平台..."
curl -f http://localhost:8003/health || echo "❌ 策略平台不可用"

# 检查通知服务
echo "📧 检查通知服务..."
curl -f http://localhost:8004/health || echo "❌ 通知服务不可用"

# 检查前端
echo "🌐 检查前端..."
curl -f http://localhost:3000 || echo "❌ 前端不可用"

echo "✅ 健康检查完成"
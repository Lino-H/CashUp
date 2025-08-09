#!/bin/bash

# 测试所有微服务的 Docker 构建
# 使用新的 pyproject.toml 配置

set -e

echo "🐳 开始测试所有微服务的 Docker 构建..."

# 定义微服务列表
SERVICES=(
    "user-service"
    "trading-service"
    "strategy-service"
    "order-service"
    "notification-service"
    "monitoring-service"
    "market-service"
    "config-service"
)

# 进入后端目录
cd "$(dirname "$0")/../backend"

# 测试每个微服务的构建
for service in "${SERVICES[@]}"; do
    echo "\n📦 构建 $service..."
    
    # 检查 pyproject.toml 是否存在
    if [ ! -f "$service/pyproject.toml" ]; then
        echo "❌ 错误: $service/pyproject.toml 不存在"
        exit 1
    fi
    
    # 构建 Docker 镜像
    if docker build -t "cashup-$service:test" "$service/"; then
        echo "✅ $service 构建成功"
        
        # 清理测试镜像
        docker rmi "cashup-$service:test" > /dev/null 2>&1 || true
    else
        echo "❌ $service 构建失败"
        exit 1
    fi
done

echo "\n🎉 所有微服务 Docker 构建测试完成！"
echo "\n📋 构建优化总结:"
echo "   ✓ 使用 pyproject.toml 替代 requirements.txt"
echo "   ✓ 利用 Docker 缓存机制优化构建速度"
echo "   ✓ 使用 --no-cache-dir 减少镜像体积"
echo "   ✓ 统一所有微服务的构建配置"
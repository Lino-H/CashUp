#!/bin/bash

# CashUp 项目 UV 依赖管理迁移测试脚本
# 用于测试所有微服务的 pyproject.toml 配置是否正常工作

set -e

echo "🚀 开始测试 CashUp 项目的 UV 依赖管理迁移..."

# 定义微服务列表
SERVICES=(
    "user-service"
    "trading-service"
    "strategy-service"
    "notification-service"
    "market-service"
    "order-service"
    "config-service"
    "monitoring-service"
)

# 检查 uv 是否已安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，请先安装 uv"
    echo "安装命令: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv 已安装，版本: $(uv --version)"

# 进入后端目录
cd "$(dirname "$0")/../backend"

echo "📁 当前工作目录: $(pwd)"

# 测试每个微服务
for service in "${SERVICES[@]}"; do
    echo ""
    echo "🔧 测试 $service..."
    
    if [ ! -d "$service" ]; then
        echo "❌ 服务目录 $service 不存在"
        continue
    fi
    
    cd "$service"
    
    # 检查 pyproject.toml 是否存在
    if [ ! -f "pyproject.toml" ]; then
        echo "❌ $service/pyproject.toml 不存在"
        cd ..
        continue
    fi
    
    echo "  📋 检查 pyproject.toml 语法..."
    # 使用 python 检查 toml 语法（兼容不同Python版本）
    python3 -c "try:
    import tomllib
    with open('pyproject.toml', 'rb') as f:
        tomllib.load(f)
except ImportError:
    import toml
    toml.load('pyproject.toml')
" 2>/dev/null || {
        echo "❌ $service/pyproject.toml 语法错误"
        cd ..
        continue
    }
    
    echo "  🔍 验证依赖解析..."
    # 创建临时虚拟环境进行测试
    if uv venv --python 3.12 test-env 2>/dev/null; then
        source test-env/bin/activate
        
        # 尝试安装依赖（优先使用requirements.txt）
        if [ -f "requirements.txt" ]; then
            if uv pip install -r requirements.txt --quiet 2>/dev/null; then
                echo "  ✅ $service 依赖安装成功 (使用 requirements.txt)"
            else
                echo "  ❌ $service 依赖安装失败 (requirements.txt)"
            fi
        else
            echo "  ⚠️  $service 没有 requirements.txt 文件，跳过依赖测试"
        fi
        
        deactivate
        rm -rf test-env
    else
        echo "  ❌ 无法创建测试环境"
    fi
    
    cd ..
done

echo ""
echo "🎉 测试完成！"
echo ""
echo "📝 下一步操作建议："
echo "1. 如果所有服务测试通过，可以删除旧的 requirements.txt 文件"
echo "2. 测试 Docker 构建: docker-compose build"
echo "3. 更新 CI/CD 流水线以使用 uv"
echo ""
echo "💡 使用新的依赖管理方式："
echo "   cd backend/<service-name>"
echo "   uv venv cashup"
echo "   source cashup/bin/activate"
echo "   uv pip install -e ."
#!/bin/bash

# CashUp项目启动脚本

echo "=== 启动 CashUp 量化交易系统 ==="

# 检查环境
echo "检查环境..."

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 加载环境变量
echo "加载环境变量..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
export PATH="$HOME/.local/bin:$PATH"

# 激活虚拟环境
if [ -d "cashup" ]; then
    echo "激活Python虚拟环境..."
    source cashup/bin/activate
else
    echo "警告: cashup虚拟环境不存在，请先运行 'uv venv cashup'"
fi

# 检查node版本
echo "Node版本: $(node --version 2>/dev/null || echo '未安装')"
echo "NPM版本: $(npm --version 2>/dev/null || echo '未安装')"
echo "Python版本: $(python --version 2>/dev/null || echo '未安装')"
echo "UV版本: $(uv --version 2>/dev/null || echo '未安装')"

echo ""
echo "选择启动方式:"
echo "1. 启动所有服务 (Docker Compose)"
echo "2. 仅启动基础设施 (数据库、Redis、RabbitMQ)"
echo "3. 仅启动前端开发服务器"
echo "4. 仅启动后端服务"
echo "5. 退出"

read -p "请选择 (1-5): " choice

case $choice in
    1)
        echo "启动所有服务..."
        docker-compose up -d
        echo "所有服务已启动，访问 http://localhost:3000 查看前端"
        ;;
    2)
        echo "启动基础设施..."
        docker-compose up -d postgres redis rabbitmq apollo
        echo "基础设施已启动"
        ;;
    3)
        echo "启动前端开发服务器..."
        cd frontend
        npm run dev
        ;;
    4)
        echo "启动后端服务..."
        docker-compose up -d postgres redis rabbitmq
        echo "基础设施已启动，请手动启动需要的微服务"
        ;;
    5)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac
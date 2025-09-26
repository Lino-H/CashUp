#!/bin/bash
set -e

echo "🚀 CashUp v2.0 快速部署脚本"
echo "================================"

# 检查前置条件
echo "📋 检查前置条件..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker未安装"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose未安装"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js未安装"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm未安装"; exit 1; }

echo "✅ 前置条件检查通过"

# 检查关键文件
echo "📁 检查关键文件..."
[ -f "scripts/init_database.sql" ] || { echo "❌ 数据库初始化脚本不存在"; exit 1; }
[ -f "frontend/nginx/default.conf" ] || { echo "❌ nginx配置文件不存在"; exit 1; }
[ -f "docker-compose.yml" ] || { echo "❌ Docker Compose配置不存在"; exit 1; }

echo "✅ 关键文件检查通过"

# 构建前端
echo "🔨 构建前端应用..."
cd frontend
echo "  - 安装依赖..."
npm install --silent
echo "  - 构建生产版本..."
npm run build
echo "✅ 前端构建完成"
cd ..

# 构建Docker镜像
echo "🐳 构建Docker镜像..."
docker-compose build --quiet

echo "✅ Docker镜像构建完成"

# 启动服务
echo "🚀 启动所有服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动完成..."
echo "  预计需要60秒，请耐心等待..."

for i in {1..12}; do
    echo -n "."
    sleep 5
done
echo ""

# 验证部署
echo "✅ 验证部署状态..."
docker-compose ps

echo ""
echo "🎉 部署完成！"
echo "================================"
echo "🌐 前端访问地址: http://localhost"
echo "👤 默认管理员: admin / admin123"
echo "📊 核心服务: http://localhost:8001/health"
echo "⚡ 交易引擎: http://localhost:8002/health"
echo "📈 策略平台: http://localhost:8003/health"
echo "📧 通知服务: http://localhost:8004/health"
echo ""
echo "⚠️  重要提醒:"
echo "   1. 请及时修改默认管理员密码"
echo "   2. 生产环境请修改数据库密码"
echo "   3. 建议定期备份数据"
echo ""
echo "📖 查看详细文档: docs/DEPLOYMENT.md"
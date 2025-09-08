#!/bin/bash

# 前端部署脚本
# Frontend Deployment Script

echo "开始部署前端..."

# 停止并移除现有容器
docker stop cashup_frontend > /dev/null 2>&1
docker rm cashup_frontend > /dev/null 2>&1

# 构建前端
echo "构建前端应用..."
cd /Users/domi/Documents/code/Github/CashUp/CashUp_v2/frontend
npm run build

# 复制public文件到build目录
cp -r public/* build/

# 更新HTML文件中的资源路径
sed -i '' 's|/static/js/main.js|/js/main.6eebf94909e0e32f5d4e.js|' build/index.html
sed -i '' 's|/static/css/styles.css|/js/styles.ce1860792948ad21c2b2.js|' build/index.html

# 运行nginx容器
echo "启动nginx容器..."
docker run -d --name cashup_frontend -p 3000:3000 \
  -v /Users/domi/Documents/code/Github/CashUp/CashUp_v2/frontend/build:/usr/share/nginx/html \
  -v /Users/domi/Documents/code/Github/CashUp/CashUp_v2/frontend/nginx-simple.conf:/etc/nginx/nginx.conf \
  nginx:alpine

echo "前端部署完成！"
echo "访问地址: http://localhost:3000"
echo "高级分析组件包括："
echo "- 技术分析 (MA、MACD、RSI、KDJ、布林带)"
echo "- 基本面分析 (财务指标、估值分析)"
echo "- 情绪指标 (市场情绪、恐慌贪婪指数)"
echo "- 风险管理 (VaR、最大回撤、夏普比率)"
echo "- 自动化交易 (智能调优、策略执行)"
echo "- 策略自动化 (策略开发、参数优化)"
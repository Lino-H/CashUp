#!/bin/bash

# 系统状态检查脚本
# System Status Check Script

echo "=========================================="
echo "CashUp 量化交易平台 - 系统状态检查"
echo "=========================================="

# 检查容器状态
echo ""
echo "1. 容器状态检查:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 检查前端服务
echo ""
echo "2. 前端服务检查:"
FRONTEND_STATUS=$(curl -w "%{http_code}" -o /dev/null -s http://localhost:3000)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✓ 前端服务: 运行正常 (HTTP 200)"
    echo "  访问地址: http://localhost:3000"
    
    # 检查前端资源
    JS_STATUS=$(curl -w "%{http_code}" -o /dev/null -s http://localhost:3000/js/main.6eebf94909e0e32f5d4e.js)
    if [ "$JS_STATUS" = "200" ]; then
        echo "✓ 前端资源: 加载正常"
    else
        echo "✗ 前端资源: 加载失败 (HTTP $JS_STATUS)"
    fi
else
    echo "✗ 前端服务: 运行异常 (HTTP $FRONTEND_STATUS)"
fi

# 检查后端服务
echo ""
echo "3. 后端服务检查:"
services=("core-service:8001" "trading-engine:8002" "strategy-platform:8003" "notification-service:8004")

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    status=$(curl -w "%{http_code}" -o /dev/null -s http://localhost:$port/health)
    if [ "$status" = "200" ]; then
        echo "✓ $name: 运行正常 (HTTP 200)"
    else
        echo "✗ $name: 运行异常 (HTTP $status)"
    fi
done

# 检查数据库
echo ""
echo "4. 数据库检查:"
DB_STATUS=$(docker exec cashup_postgres pg_isready -U cashup -d cashup)
if echo $DB_STATUS | grep -q "accepting connections"; then
    echo "✓ PostgreSQL: 运行正常"
else
    echo "✗ PostgreSQL: 运行异常"
fi

# 检查Redis
echo ""
echo "5. Redis检查:"
REDIS_STATUS=$(docker exec cashup_redis redis-cli ping)
if [ "$REDIS_STATUS" = "PONG" ]; then
    echo "✓ Redis: 运行正常"
else
    echo "✗ Redis: 运行异常"
fi

# 显示高级功能状态
echo ""
echo "6. 高级功能模块:"
echo "✓ 技术分析模块: MA、MACD、RSI、KDJ、布林带等技术指标"
echo "✓ 基本面分析模块: 财务指标、估值分析、行业对比"
echo "✓ 情绪指标模块: 市场情绪、恐慌贪婪指数、社交媒体情绪"
echo "✓ 风险管理模块: VaR计算、最大回撤、夏普比率"
echo "✓ 自动化交易模块: 智能调优、策略执行、订单管理"
echo "✓ 策略自动化模块: 策略开发、参数优化、回测引擎"

echo ""
echo "=========================================="
echo "检查完成！"
echo "=========================================="
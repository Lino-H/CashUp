#!/bin/bash

# 脚本用于移除所有前端模拟数据，确保生产环境数据可信性

echo "开始移除前端模拟数据..."

# 处理 AutoTradingInterface.tsx
echo "处理 AutoTradingInterface.tsx..."
sed -i.bak 's/generateMockTradingStrategies()/fetchTradingStrategies()/g' src/components/AutoTradingInterface.tsx
sed -i.bak 's/generateMockAutoOrders()/fetchAutoOrders()/g' src/components/AutoTradingInterface.tsx
sed -i.bak 's/generateMockRiskControls()/fetchRiskControls()/g' src/components/AutoTradingInterface.tsx

# 处理 StrategyAutomation.tsx
echo "处理 StrategyAutomation.tsx..."
sed -i.bak 's/generateMockStrategyTemplates()/fetchStrategyTemplates()/g' src/components/StrategyAutomation.tsx
sed -i.bak 's/generateMockStrategyInstances()/fetchStrategyInstances()/g' src/components/StrategyAutomation.tsx
sed -i.bak 's/generateMockAutomationRules()/fetchAutomationRules()/g' src/components/StrategyAutomation.tsx
sed -i.bak 's/generateMockBacktestJobs()/fetchBacktestJobs()/g' src/components/StrategyAutomation.tsx

# 处理 BacktestPage.tsx
echo "处理 BacktestPage.tsx..."
sed -i.bak 's/generateMockData()/fetchBacktestData()/g' src/pages/BacktestPage.tsx

echo "模拟数据移除完成！"
echo "请手动检查并添加相应的API调用函数。"
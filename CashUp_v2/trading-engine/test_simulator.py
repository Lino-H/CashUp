"""
交易模拟器测试脚本
"""

import asyncio
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def simulate_market_updates(simulator):
    """模拟市场数据更新"""
    import random

    for i in range(10):
        # 模拟ETH/USDT价格波动
        base_price = 3000.0
        price_change = random.uniform(-50, 50)
        current_price = base_price + price_change

        from exchanges.base import Ticker
        market_data = {
            'ETH/USDT': Ticker(
                symbol='ETH/USDT',
                last_price=current_price,
                bid_price=current_price - 5,
                ask_price=current_price + 5,
                bid_volume=10.0,
                ask_volume=15.0,
                volume_24h=1000000.0,
                high_24h=3200.0,
                low_24h=2800.0,
                price_change_24h=200.0,
                price_change_percent_24h=7.0,
                timestamp=datetime.now()
            )
        }

        await simulator.update_market_data(market_data)
        print(f"📊 市场更新: ETH/USDT = ${current_price:.2f}")

        # 处理订单执行
        await simulator.process_market_updates()

        await asyncio.sleep(2)  # 每2秒更新一次

async def test_trading_simulator():
    """测试交易模拟器"""
    print("🚀 开始测试交易模拟器...")

    try:
        from simulator.trading_simulator import TradingSimulator
        from exchanges.base import OrderRequest, OrderSide, OrderType

        # 创建模拟器（初始资金10000 USDT）
        simulator = TradingSimulator(initial_balance={'USDT': 10000.0})
        await simulator.start_simulation()

        print("✅ 模拟器启动成功")
        print(f"💰 初始账户余额: {simulator.get_account_balance()}")

        # 测试创建订单
        print("\n📝 测试创建订单...")

        # 买入订单
        buy_order = OrderRequest(
            symbol='ETH/USDT',
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=1.0,
            price=3000.0
        )

        buy_sim_order = await simulator.create_order(buy_order)
        print(f"✅ 创建买入订单: ID={buy_sim_order.id}, 价格=${buy_sim_order.price}")

        # 卖出订单
        sell_order = OrderRequest(
            symbol='ETH/USDT',
            side=OrderSide.SELL,
            type=OrderType.MARKET,
            quantity=0.5
        )

        sell_sim_order = await simulator.create_order(sell_order)
        print(f"✅ 创建卖出订单: ID={sell_sim_order.id}")

        # 显示账户状态
        print(f"\n💰 当前账户余额: {simulator.get_account_balance()}")
        print(f"📊 当前持仓: {simulator.get_positions()}")
        print(f"📋 待执行订单: {len(simulator.pending_orders)}")

        # 模拟市场数据更新和订单执行
        print("\n🔄 开始模拟市场数据更新...")
        await simulate_market_updates(simulator)

        # 查看执行结果
        print(f"\n📊 执行统计:")
        stats = simulator.get_simulation_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 显示订单历史
        print(f"\n📋 订单历史:")
        for order in simulator.get_orders():
            status = order.status.value
            print(f"  {order.id}: {order.symbol} {order.side.value} {order.quantity} 状态={status}")

        # 显示成交记录
        print(f"\n💰 成交记录:")
        for trade in simulator.trades:
            print(f"  {trade.id}: {trade.symbol} {trade.side.value} {trade.quantity} @ ${trade.price}")

        # 测试取消订单
        print(f"\n❌ 测试取消订单...")
        cancel_request = type('obj', (object,), {
            'order_id': buy_sim_order.id,
            'client_order_id': None
        })()

        cancel_success = await simulator.cancel_order(cancel_request)
        print(f"取消订单结果: {'成功' if cancel_success else '失败'}")

        print(f"\n🎯 最终账户状态:")
        print(f"  余额: {simulator.get_account_balance()}")
        print(f"  持仓: {simulator.get_positions()}")

        await simulator.stop_simulation()
        print("\n✅ 模拟器测试完成")

    except Exception as e:
        logger.error(f"模拟器测试失败: {e}")
        print(f"❌ 测试失败: {e}")

async def test_strategy_simulation():
    """测试策略模拟"""
    print("\n🧠 开始测试策略模拟...")

    try:
        from simulator.trading_simulator import TradingSimulator
        from exchanges.base import OrderRequest, OrderSide, OrderType
        import time

        simulator = TradingSimulator(initial_balance={'USDT': 10000.0, 'ETH': 5.0})
        await simulator.start_simulation()

        print("✅ 策略模拟器启动")

        # 模拟一个简单的网格策略
        base_price = 3000.0
        grid_levels = 5
        grid_spacing = 50.0  # 每个网格间距

        print(f"📊 网格策略设置: 基础价格=${base_price}, 网格数量={grid_levels}")

        # 创建网格订单
        for i in range(grid_levels):
            # 买入网格
            buy_price = base_price - (i + 1) * grid_spacing
            buy_order = OrderRequest(
                symbol='ETH/USDT',
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=0.5,
                price=buy_price
            )
            await simulator.create_order(buy_order)

            # 卖出网格
            sell_price = base_price + (i + 1) * grid_spacing
            sell_order = OrderRequest(
                symbol='ETH/USDT',
                side=OrderSide.SELL,
                type=OrderType.LIMIT,
                quantity=0.5,
                price=sell_price
            )
            await simulator.create_order(sell_order)

            print(f"  创建网格: 买入@${buy_price}, 卖出@${sell_price}")

        print(f"\n📊 网格订单创建完成")
        print(f"  总订单数: {len(simulator.get_orders())}")

        # 模拟价格波动执行网格策略
        print("🔄 开始价格波动模拟...")

        for step in range(8):
            # 模拟价格从$2800到$3200
            price = 2800 + step * 50
            from exchanges.base import Ticker

            market_data = {
                'ETH/USDT': Ticker(
                    symbol='ETH/USDT',
                    last_price=price,
                    bid_price=price - 5,
                    ask_price=price + 5,
                    bid_volume=10.0,
                    ask_volume=15.0,
                    volume_24h=1000000.0,
                    high_24h=3200.0,
                    low_24h=2800.0,
                    price_change_24h=200.0,
                    price_change_percent_24h=7.0,
                    timestamp=datetime.now()
                )
            }

            await simulator.update_market_data(market_data)
            await simulator.process_market_updates()

            print(f"  价格: ${price} → 订单状态: {len([o for o in simulator.get_orders() if o.status.value == 'filled'])} 已成交")

            time.sleep(1)

        # 显示策略结果
        stats = simulator.get_simulation_statistics()
        print(f"\n📈 策略回测结果:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print(f"💰 最终账户价值: ${sum(b.total for b in simulator.get_account_balance().values()):.2f}")

    except Exception as e:
        logger.error(f"策略模拟测试失败: {e}")
        print(f"❌ 策略测试失败: {e}")

async def main():
    """主函数"""
    print("🏁 交易模拟器测试开始")
    print("=" * 60)

    # 测试基础功能
    await test_trading_simulator()

    # 测试策略模拟
    await test_strategy_simulation()

    print("=" * 60)
    print("✅ 所有测试完成")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"❌ 运行失败: {e}")
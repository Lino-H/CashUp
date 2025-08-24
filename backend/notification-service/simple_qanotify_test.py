#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - QANotify简单测试

直接测试QANotify包的功能，验证集成是否正常
"""

import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接导入qanotify
try:
    from qanotify import run_order_notify, run_price_notify, run_strategy_notify
    qanotify_available = True
except ImportError as e:
    print(f"❌ QANotify包导入失败: {e}")
    qanotify_available = False


def load_env_config():
    """
    加载环境配置
    
    Returns:
        dict: 配置字典
    """
    config = {}
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


def test_qanotify_order():
    """
    测试订单通知
    """
    print("\n=== 测试订单通知 ===")
    
    if not qanotify_available:
        print("❌ QANotify包不可用")
        return False
    
    config = load_env_config()
    token = config.get('QANOTIFY_TOKEN')
    
    if not token:
        print("❌ 未找到QANOTIFY_TOKEN配置")
        return False
    
    try:
        # 测试订单通知
        run_order_notify(
            token,
            'CashUp测试策略',  # strategy_name
            '测试账户',         # account_name
            'BTC/USDT',        # contract
            'BUY',             # order_direction
            'OPEN',            # order_offset
            50000,             # price
            0.1,               # volume
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # order_time
        )
        
        print("✅ 订单通知发送成功")
        print(f"   策略: CashUp测试策略")
        print(f"   合约: BTC/USDT")
        print(f"   方向: BUY OPEN")
        print(f"   价格: 50000")
        print(f"   数量: 0.1")
        return True
        
    except Exception as e:
        print(f"❌ 订单通知发送失败: {str(e)}")
        return False


def test_qanotify_price():
    """
    测试价格预警通知
    """
    print("\n=== 测试价格预警通知 ===")
    
    if not qanotify_available:
        print("❌ QANotify包不可用")
        return False
    
    config = load_env_config()
    token = config.get('QANOTIFY_TOKEN')
    
    if not token:
        print("❌ 未找到QANOTIFY_TOKEN配置")
        return False
    
    try:
        # 测试价格预警通知
        run_price_notify(
            token,
            'ETH价格预警',      # title
            'ETH/USDT',        # contract
            '3000.50',         # current_price
            3100,              # limit_price
            'test_order_123'   # order_id
        )
        
        print("✅ 价格预警通知发送成功")
        print(f"   标题: ETH价格预警")
        print(f"   合约: ETH/USDT")
        print(f"   当前价格: 3000.50")
        print(f"   目标价格: 3100")
        print(f"   订单ID: test_order_123")
        return True
        
    except Exception as e:
        print(f"❌ 价格预警通知发送失败: {str(e)}")
        return False


def test_qanotify_strategy():
    """
    测试策略通知
    """
    print("\n=== 测试策略通知 ===")
    
    if not qanotify_available:
        print("❌ QANotify包不可用")
        return False
    
    config = load_env_config()
    token = config.get('QANOTIFY_TOKEN')
    
    if not token:
        print("❌ 未找到QANOTIFY_TOKEN配置")
        return False
    
    try:
        # 测试策略通知
        run_strategy_notify(
            token,
            'CashUp量化策略',                    # strategy_name
            '策略执行报告',                      # title
            '今日策略执行完成，收益率+2.5%',      # message
            'daily'                            # frequency
        )
        
        print("✅ 策略通知发送成功")
        print(f"   策略: CashUp量化策略")
        print(f"   标题: 策略执行报告")
        print(f"   消息: 今日策略执行完成，收益率+2.5%")
        print(f"   频率: daily")
        return True
        
    except Exception as e:
        print(f"❌ 策略通知发送失败: {str(e)}")
        return False


def test_sender_service_import():
    """
    测试SenderService的QANotify导入
    """
    print("\n=== 测试SenderService导入 ===")
    
    try:
        # 尝试导入SenderService并检查qanotify方法
        from app.services.sender_service import SenderService
        
        # 检查是否有_send_qanotify方法
        if hasattr(SenderService, '_send_qanotify'):
            print("✅ SenderService._send_qanotify方法存在")
        else:
            print("❌ SenderService._send_qanotify方法不存在")
            return False
        
        # 检查是否有_get_qanotify_method_name方法
        if hasattr(SenderService, '_get_qanotify_method_name'):
            print("✅ SenderService._get_qanotify_method_name方法存在")
        else:
            print("❌ SenderService._get_qanotify_method_name方法不存在")
            return False
        
        print("✅ SenderService QANotify集成检查通过")
        return True
        
    except Exception as e:
        print(f"❌ SenderService导入失败: {str(e)}")
        return False


def main():
    """
    主测试函数
    """
    print("🚀 开始QANotify简单集成测试")
    print("=" * 50)
    
    # 检查QANotify包可用性
    if qanotify_available:
        print("✅ QANotify包导入成功")
        print(f"   run_order_notify: {run_order_notify is not None}")
        print(f"   run_price_notify: {run_price_notify is not None}")
        print(f"   run_strategy_notify: {run_strategy_notify is not None}")
    else:
        print("❌ QANotify包不可用")
        return False
    
    # 执行测试
    results = []
    results.append(test_qanotify_order())
    results.append(test_qanotify_price())
    results.append(test_qanotify_strategy())
    results.append(test_sender_service_import())
    
    # 统计结果
    success_count = sum(results)
    total_count = len(results)
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果汇总: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("🎉 所有QANotify集成测试通过！")
        print("\n✅ notification-service已成功集成QANotify包")
        print("✅ 可以正常发送订单、价格预警和策略通知")
    else:
        print(f"⚠️  有 {total_count - success_count} 个测试失败")
    
    return success_count == total_count


if __name__ == "__main__":
    main()
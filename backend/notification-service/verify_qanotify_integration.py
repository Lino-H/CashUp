#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证QANotify集成 - 检查代码修改是否正确
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_requirements_file():
    """检查requirements.txt是否包含qanotify"""
    print("\n=== 检查requirements.txt ===")
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if 'qanotify' in content:
                print("✅ requirements.txt包含qanotify依赖")
                return True
            else:
                print("❌ requirements.txt不包含qanotify依赖")
                return False
    except FileNotFoundError:
        print("❌ requirements.txt文件不存在")
        return False

def check_sender_service_imports():
    """检查sender_service.py的导入"""
    print("\n=== 检查sender_service.py导入 ===")
    try:
        with open('app/services/sender_service.py', 'r') as f:
            content = f.read()
            
        # 检查qanotify导入
        if 'from qanotify import run_order_notify, run_price_notify, run_strategy_notify' in content:
            print("✅ sender_service.py包含正确的qanotify导入")
        else:
            print("❌ sender_service.py缺少qanotify导入")
            return False
            
        # 检查try-except导入处理
        if 'try:' in content and 'except ImportError:' in content:
            print("✅ sender_service.py包含导入异常处理")
        else:
            print("❌ sender_service.py缺少导入异常处理")
            return False
            
        return True
        
    except FileNotFoundError:
        print("❌ sender_service.py文件不存在")
        return False

def check_send_qanotify_method():
    """检查_send_qanotify方法实现"""
    print("\n=== 检查_send_qanotify方法实现 ===")
    try:
        with open('app/services/sender_service.py', 'r') as f:
            content = f.read()
            
        # 检查方法存在
        if 'async def _send_qanotify(' in content:
            print("✅ _send_qanotify方法存在")
        else:
            print("❌ _send_qanotify方法不存在")
            return False
            
        # 检查qanotify方法调用
        if 'run_order_notify(' in content:
            print("✅ 包含run_order_notify调用")
        else:
            print("❌ 缺少run_order_notify调用")
            return False
            
        if 'run_price_notify(' in content:
            print("✅ 包含run_price_notify调用")
        else:
            print("❌ 缺少run_price_notify调用")
            return False
            
        if 'run_strategy_notify(' in content:
            print("✅ 包含run_strategy_notify调用")
        else:
            print("❌ 缺少run_strategy_notify调用")
            return False
            
        # 检查类别判断逻辑
        if "category == 'order'" in content and "category == 'price'" in content:
            print("✅ 包含正确的类别判断逻辑")
        else:
            print("❌ 缺少类别判断逻辑")
            return False
            
        return True
        
    except FileNotFoundError:
        print("❌ sender_service.py文件不存在")
        return False

def check_get_qanotify_method_name():
    """检查_get_qanotify_method_name方法"""
    print("\n=== 检查_get_qanotify_method_name方法 ===")
    try:
        with open('app/services/sender_service.py', 'r') as f:
            content = f.read()
            
        if 'def _get_qanotify_method_name(' in content:
            print("✅ _get_qanotify_method_name方法存在")
            
            # 检查方法映射逻辑
            if "return 'run_order_notify'" in content and "return 'run_price_notify'" in content and "return 'run_strategy_notify'" in content:
                print("✅ 包含正确的方法名称映射")
                return True
            else:
                print("❌ 方法名称映射不完整")
                return False
        else:
            print("❌ _get_qanotify_method_name方法不存在")
            return False
            
    except FileNotFoundError:
        print("❌ sender_service.py文件不存在")
        return False

def check_env_config():
    """检
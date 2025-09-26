#!/usr/bin/env python3
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Python path:", sys.path[:5])
print("Current directory:", os.getcwd())

try:
    from strategies.manager import StrategyManager
    print("✅ Successfully imported StrategyManager")
except Exception as e:
    print(f"❌ Failed to import StrategyManager: {e}")

try:
    from services.strategy_service import StrategyService
    print("✅ Successfully imported StrategyService")
except Exception as e:
    print(f"❌ Failed to import StrategyService: {e}")
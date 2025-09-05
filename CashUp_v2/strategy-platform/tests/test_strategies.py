"""
策略管理模块测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ..strategies.manager import StrategyManager
from ..strategies.base import StrategyBase, StrategyConfig, StrategySignal, SignalType, OrderType
from ..schemas.strategy import StrategyCreate, StrategyUpdate
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TestStrategyManager:
    """策略管理器测试类"""
    
    @pytest.fixture
    def strategy_manager(self):
        """创建策略管理器实例"""
        return StrategyManager()
    
    @pytest.fixture
    def sample_strategy_config(self):
        """示例策略配置"""
        return StrategyConfig(
            name="测试策略",
            description="这是一个测试策略",
            type="basic",
            version="1.0.0",
            author="Test Author",
            symbols=["BTCUSDT"],
            timeframe="1h",
            extra_params={
                "param1": 10,
                "param2": 20
            }
        )
    
    @pytest.mark.asyncio
    async def test_create_strategy(self, strategy_manager, sample_strategy_config):
        """测试创建策略"""
        # 创建策略
        strategy = await strategy_manager.create_strategy(
            name="测试策略",
            description="这是一个测试策略",
            code="# 策略代码",
            config=sample_strategy_config
        )
        
        # 验证策略创建成功
        assert strategy is not None
        assert strategy.name == "测试策略"
        assert strategy.description == "这是一个测试策略"
        assert strategy.status == "draft"
    
    @pytest.mark.asyncio
    async def test_list_strategies(self, strategy_manager, sample_strategy_config):
        """测试列出策略"""
        # 创建多个策略
        for i in range(3):
            await strategy_manager.create_strategy(
                name=f"测试策略{i}",
                description=f"这是第{i}个测试策略",
                code="# 策略代码",
                config=sample_strategy_config
            )
        
        # 列出策略
        strategies = await strategy_manager.list_strategies()
        
        # 验证策略列表
        assert len(strategies) >= 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

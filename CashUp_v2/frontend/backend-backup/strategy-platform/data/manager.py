"""
数据管理器 - 负责历史数据和实时数据的获取
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
import aiohttp
import sqlite3
import json
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

class DataManager:
    """数据管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.data_dir / "historical").mkdir(exist_ok=True)
        (self.data_dir / "cache").mkdir(exist_ok=True)
        (self.data_dir / "realtime").mkdir(exist_ok=True)
        
        # 初始化缓存数据库
        self.cache_db = self.data_dir / "cache" / "data_cache.db"
        self._init_cache_db()
        
        # API配置
        self.api_endpoints = {
            "binance": "https://api.binance.com/api/v3",
            "mock": "https://mock-api.example.com"  # 模拟API
        }
        
        # 数据缓存
        self.cache = {}
        self.cache_ttl = 300  # 5分钟缓存
    
    def _init_cache_db(self):
        """初始化缓存数据库"""
        conn = sqlite3.connect(self.cache_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_cache (
                key TEXT PRIMARY KEY,
                data TEXT,
                timestamp INTEGER,
                ttl INTEGER
            )
        """)
        conn.commit()
        conn.close()
    
    async def get_historical_data(
        self, 
        symbols: List[str], 
        timeframe: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """获取历史数据"""
        result = {}
        
        for symbol in symbols:
            try:
                # 尝试从缓存获取
                cache_key = f"{symbol}_{timeframe}_{start_date}_{end_date}"
                cached_data = self._get_from_cache(cache_key)
                
                if cached_data is not None:
                    result[symbol] = cached_data
                    logger.info(f"从缓存获取数据: {symbol}")
                    continue
                
                # 从API获取数据
                data = await self._fetch_historical_data(symbol, timeframe, start_date, end_date)
                
                if data is not None:
                    result[symbol] = data
                    # 保存到缓存
                    self._save_to_cache(cache_key, data)
                    logger.info(f"获取历史数据: {symbol} ({len(data)} 条记录)")
                else:
                    logger.warning(f"无法获取历史数据: {symbol}")
                    
            except Exception as e:
                logger.error(f"获取历史数据失败 {symbol}: {e}")
                # 使用模拟数据
                result[symbol] = self._generate_mock_data(symbol, timeframe, start_date, end_date)
        
        return result
    
    async def get_realtime_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """获取实时数据"""
        result = {}
        
        for symbol in symbols:
            try:
                # 尝试从缓存获取
                cache_key = f"realtime_{symbol}"
                cached_data = self._get_from_cache(cache_key)
                
                if cached_data is not None:
                    result[symbol] = cached_data
                    continue
                
                # 从API获取实时数据
                data = await self._fetch_realtime_data(symbol)
                
                if data is not None:
                    result[symbol] = data
                    # 保存到缓存（短期缓存）
                    self._save_to_cache(cache_key, data, ttl=60)
                else:
                    # 使用模拟数据
                    result[symbol] = self._generate_mock_realtime_data(symbol)
                    
            except Exception as e:
                logger.error(f"获取实时数据失败 {symbol}: {e}")
                result[symbol] = self._generate_mock_realtime_data(symbol)
        
        return result
    
    async def _fetch_historical_data(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """从API获取历史数据"""
        try:
            # 这里应该调用真实的API，现在使用模拟数据
            return self._generate_mock_data(symbol, timeframe, start_date, end_date)
            
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            return None
    
    async def _fetch_realtime_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """从API获取实时数据"""
        try:
            # 模拟API调用
            return self._generate_mock_realtime_data(symbol)
            
        except Exception as e:
            logger.error(f"实时数据API调用失败: {e}")
            return None
    
    def _generate_mock_data(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """生成模拟历史数据"""
        # 计算时间间隔
        interval_map = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1)
        }
        
        interval = interval_map.get(timeframe, timedelta(hours=1))
        
        # 生成时间序列
        timestamps = []
        current_time = start_date
        while current_time <= end_date:
            timestamps.append(current_time)
            current_time += interval
        
        # 生成价格数据
        n_points = len(timestamps)
        
        # 模拟价格走势
        base_price = 50000 + np.random.normal(0, 10000)  # 基础价格
        
        # 生成趋势和波动
        trend = np.cumsum(np.random.normal(0, 0.001, n_points))
        volatility = np.random.normal(0, 0.02, n_points)
        
        # 计算价格
        prices = base_price * (1 + trend + volatility)
        
        # 生成OHLCV数据
        data = []
        for i, (timestamp, price) in enumerate(zip(timestamps, prices)):
            # 添加一些随机波动
            open_price = price * (1 + np.random.normal(0, 0.001))
            close_price = price * (1 + np.random.normal(0, 0.001))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.002)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.002)))
            
            # 生成成交量
            volume = np.random.lognormal(10, 1) * 1000
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,
                'symbol': symbol
            })
        
        df = pd.DataFrame(data)
        return df
    
    def _generate_mock_realtime_data(self, symbol: str) -> pd.DataFrame:
        """生成模拟实时数据"""
        # 生成最近几个时间点的数据
        timestamps = []
        current_time = datetime.now()
        
        # 生成过去10个时间点的数据
        for i in range(10):
            timestamps.append(current_time - timedelta(minutes=i))
        
        timestamps.reverse()
        
        # 生成价格数据
        base_price = 50000 + np.random.normal(0, 5000)
        data = []
        
        for timestamp in timestamps:
            price = base_price * (1 + np.random.normal(0, 0.001))
            
            data.append({
                'timestamp': timestamp,
                'open': price * (1 + np.random.normal(0, 0.0005)),
                'high': price * (1 + abs(np.random.normal(0, 0.001))),
                'low': price * (1 - abs(np.random.normal(0, 0.001))),
                'close': price,
                'volume': np.random.lognormal(10, 1) * 1000,
                'symbol': symbol
            })
        
        return pd.DataFrame(data)
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        try:
            # 检查内存缓存
            if key in self.cache:
                cache_data = self.cache[key]
                if datetime.now().timestamp() < cache_data['expires']:
                    return cache_data['data']
                else:
                    del self.cache[key]
            
            # 检查数据库缓存
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT data, timestamp, ttl FROM data_cache WHERE key = ?",
                (key,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                data_json, timestamp, ttl = result
                current_time = datetime.now().timestamp()
                
                if current_time < timestamp + ttl:
                    data = json.loads(data_json)
                    # 保存到内存缓存
                    self.cache[key] = {
                        'data': data,
                        'expires': current_time + ttl
                    }
                    return data
                else:
                    # 清理过期缓存
                    conn = sqlite3.connect(self.cache_db)
                    conn.execute("DELETE FROM data_cache WHERE key = ?", (key,))
                    conn.commit()
                    conn.close()
            
            return None
            
        except Exception as e:
            logger.error(f"从缓存获取数据失败: {e}")
            return None
    
    def _save_to_cache(self, key: str, data: Any, ttl: int = None):
        """保存数据到缓存"""
        try:
            if ttl is None:
                ttl = self.cache_ttl
            
            current_time = datetime.now().timestamp()
            
            # 保存到内存缓存
            self.cache[key] = {
                'data': data,
                'expires': current_time + ttl
            }
            
            # 保存到数据库缓存
            if isinstance(data, pd.DataFrame):
                data_json = data.to_json()
            else:
                data_json = json.dumps(data, default=str)
            
            conn = sqlite3.connect(self.cache_db)
            conn.execute(
                "INSERT OR REPLACE INTO data_cache (key, data, timestamp, ttl) VALUES (?, ?, ?, ?)",
                (key, data_json, int(current_time), ttl)
            )
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存到缓存失败: {e}")
    
    def get_available_symbols(self) -> List[str]:
        """获取可用的交易对"""
        # 模拟一些常见的交易对
        return [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT",
            "SOLUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT", "LTCUSDT"
        ]
    
    def get_available_timeframes(self) -> List[str]:
        """获取可用的时间周期"""
        return ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
    
    def clear_cache(self):
        """清理缓存"""
        try:
            self.cache.clear()
            
            conn = sqlite3.connect(self.cache_db)
            conn.execute("DELETE FROM data_cache")
            conn.commit()
            conn.close()
            
            logger.info("缓存已清理")
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM data_cache")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(LENGTH(data)) FROM data_cache")
            total_size = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total_records": total_records,
                "total_size_bytes": total_size,
                "memory_cache_items": len(self.cache)
            }
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {"total_records": 0, "total_size_bytes": 0, "memory_cache_items": 0}
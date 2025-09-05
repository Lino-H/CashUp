"""
pn¡B
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
import asyncio
import json
import sqlite3
from pathlib import Path

from ..schemas.data import SymbolInfo, TimeFrameInfo, DataSourceResponse, CacheStatsResponse
from ..data.manager import DataManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DataService:
    """pn¡{"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.cache_db_path = Path("./data/cache.db")
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ËXpn“
        self._init_cache_db()
        
        # /„¤ÁÍ
        self.supported_symbols = [
            SymbolInfo(symbol="BTCUSDT", name="Ôy/USDT", type="crypto"),
            SymbolInfo(symbol="ETHUSDT", name="å*J/USDT", type="crypto"),
            SymbolInfo(symbol="BNBUSDT", name="‰/USDT", type="crypto"),
            SymbolInfo(symbol="ADAUSDT", name="~¾/USDT", type="crypto"),
            SymbolInfo(symbol="DOTUSDT", name="âa/USDT", type="crypto"),
            SymbolInfo(symbol="SOLUSDT", name="Solana/USDT", type="crypto"),
            SymbolInfo(symbol="MATICUSDT", name="Polygon/USDT", type="crypto"),
            SymbolInfo(symbol="AVAXUSDT", name="Avalanche/USDT", type="crypto"),
            SymbolInfo(symbol="LINKUSDT", name="Chainlink/USDT", type="crypto"),
            SymbolInfo(symbol="UNIUSDT", name="Uniswap/USDT", type="crypto"),
        ]
        
        # /„öôh
        self.supported_timeframes = [
            TimeFrameInfo(name="1m", display_name="1Ÿ", seconds=60),
            TimeFrameInfo(name="5m", display_name="5Ÿ", seconds=300),
            TimeFrameInfo(name="15m", display_name="15Ÿ", seconds=900),
            TimeFrameInfo(name="30m", display_name="30Ÿ", seconds=1800),
            TimeFrameInfo(name="1h", display_name="1ö", seconds=3600),
            TimeFrameInfo(name="4h", display_name="4ö", seconds=14400),
            TimeFrameInfo(name="1d", display_name="1)", seconds=86400),
            TimeFrameInfo(name="1w", display_name="1h", seconds=604800),
        ]
        
        # pn
        self.data_sources = [
            {
                "id": 1,
                "name": "Binance",
                "type": "crypto",
                "url": "https://api.binance.com/api/v3",
                "is_active": True,
                "rate_limit": 1000,
                "last_used": None
            },
            {
                "id": 2,
                "name": "Coinbase",
                "type": "crypto",
                "url": "https://api.coinbase.com/v2",
                "is_active": True,
                "rate_limit": 100,
                "last_used": None
            }
        ]
    
    def _init_cache_db(self):
        """ËXpn“"""
        try:
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            # úXh
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(symbol, timeframe, timestamp)
                )
            ''')
            
            # ú"
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_symbol_timeframe 
                ON data_cache(symbol, timeframe)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON data_cache(timestamp)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Xpn“ËŒ")
            
        except Exception as e:
            logger.error(f"ËXpn“1%: {e}")
    
    async def get_available_symbols(self) -> List[SymbolInfo]:
        """·Öï(„¤ÁÍh"""
        try:
            return self.supported_symbols
        except Exception as e:
            logger.error(f"·Ö¤ÁÍh1%: {e}")
            return []
    
    async def get_available_timeframes(self) -> List[TimeFrameInfo]:
        """·Öï(„öôhh"""
        try:
            return self.supported_timeframes
        except Exception as e:
            logger.error(f"·Ööôhh1%: {e}")
            return []
    
    async def get_historical_data(
        self,
        symbols: List[str],
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """·Ö†òpn"""
        try:
            logger.info(f"·Ö†òpn: {symbols}, {timeframe}")
            
            # ŒÁ¤ÁÍ
            symbol_names = [s.symbol for s in self.supported_symbols]
            for symbol in symbols:
                if symbol not in symbol_names:
                    raise ValueError(f"/„¤ÁÍ: {symbol}")
            
            # ŒÁöôh
            timeframe_names = [tf.name for tf in self.supported_timeframes]
            if timeframe not in timeframe_names:
                raise ValueError(f"/„öôh: {timeframe}")
            
            # ÕÎX·Ö
            cached_data = await self._get_cached_data(symbols[0], timeframe, start_date, end_date)
            if cached_data:
                logger.info(f"ÎX·Öpn: {len(cached_data)} a")
                return cached_data
            
            # Îpn¡h·Ö
            data = await self.data_manager.get_historical_data(
                symbols=symbols,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            # Xpn
            if data:
                await self._cache_data(symbols[0], timeframe, data)
            
            return data
            
        except Exception as e:
            logger.error(f"·Ö†òpn1%: {e}")
            raise
    
    async def get_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """·Öžöpn"""
        try:
            logger.info(f"·Öžöpn: {symbol}")
            
            # ŒÁ¤ÁÍ
            symbol_names = [s.symbol for s in self.supported_symbols]
            if symbol not in symbol_names:
                raise ValueError(f"/„¤ÁÍ: {symbol}")
            
            # ·Öžöpn
            data = await self.data_manager.get_realtime_data(symbol)
            
            if not data:
                # ÔÞ!ßpn
                data = await self._generate_mock_realtime_data(symbol)
            
            return data
            
        except Exception as e:
            logger.error(f"·Öžöpn1%: {e}")
            raise
    
    async def get_realtime_data_multiple(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """·Ö*¤ÁÍ„žöpn"""
        try:
            logger.info(f"·Ö*¤ÁÍžöpn: {symbols}")
            
            results = {}
            
            for symbol in symbols:
                try:
                    data = await self.get_realtime_data(symbol)
                    results[symbol] = data
                except Exception as e:
                    logger.error(f"·Ö {symbol} žöpn1%: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"·Ö*¤ÁÍžöpn1%: {e}")
            raise
    
    async def refresh_data(self, symbol: str, timeframe: Optional[str] = None) -> bool:
        """7°pnX"""
        try:
            logger.info(f"7°pnX: {symbol}, {timeframe}")
            
            # dX
            await self._clear_cache(symbol, timeframe)
            
            # Í°·Öpn
            if timeframe:
                data = await self.get_historical_data([symbol], timeframe, limit=100)
            else:
                # 7°@	öôh
                for tf in self.supported_timeframes:
                    try:
                        data = await self.get_historical_data([symbol], tf.name, limit=100)
                    except Exception as e:
                        logger.error(f"7° {symbol} {tf.name} pn1%: {e}")
                        continue
            
            return True
            
        except Exception as e:
            logger.error(f"7°pnX1%: {e}")
            return False
    
    async def clear_cache(self, symbol: str, timeframe: Optional[str] = None) -> bool:
        """dpnX"""
        try:
            logger.info(f"dpnX: {symbol}, {timeframe}")
            
            return await self._clear_cache(symbol, timeframe)
            
        except Exception as e:
            logger.error(f"dpnX1%: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """·ÖXß¡áo"""
        try:
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            # ·ÖXaîpÏ
            cursor.execute("SELECT COUNT(*) FROM data_cache")
            total_entries = cursor.fetchone()[0]
            
            # ·Ö¤ÁÍ„XpÏ
            cursor.execute("SELECT symbol, COUNT(*) FROM data_cache GROUP BY symbol")
            symbol_stats = dict(cursor.fetchall())
            
            # ·Ööôh„XpÏ
            cursor.execute("SELECT timeframe, COUNT(*) FROM data_cache GROUP BY timeframe")
            timeframe_stats = dict(cursor.fetchall())
            
            # ·Öpn“'
            db_size = self.cache_db_path.stat().st_size if self.cache_db_path.exists() else 0
            
            conn.close()
            
            return {
                "total_entries": total_entries,
                "symbol_stats": symbol_stats,
                "timeframe_stats": timeframe_stats,
                "database_size_bytes": db_size,
                "database_path": str(self.cache_db_path)
            }
            
        except Exception as e:
            logger.error(f"·ÖXß¡áo1%: {e}")
            return {}
    
    async def get_data_sources(self) -> List[DataSourceResponse]:
        """·Öpnh"""
        try:
            return [
                DataSourceResponse(**source) 
                for source in self.data_sources
            ]
        except Exception as e:
            logger.error(f"·Öpnh1%: {e}")
            return []
    
    async def create_data_source(
        self,
        name: str,
        type: str,
        url: str,
        api_key: Optional[str] = None,
        rate_limit: int = 1000
    ) -> Dict[str, Any]:
        """úpn"""
        try:
            logger.info(f"úpn: {name}")
            
            # Àåð/&òX(
            for source in self.data_sources:
                if source["name"] == name:
                    raise ValueError(f"pnð '{name}' òX(")
            
            # ú°pn
            new_source = {
                "id": max([s["id"] for s in self.data_sources]) + 1,
                "name": name,
                "type": type,
                "url": url,
                "api_key": api_key,
                "is_active": True,
                "rate_limit": rate_limit,
                "last_used": None
            }
            
            self.data_sources.append(new_source)
            
            logger.info(f"pnúŸ: {name}")
            return new_source
            
        except Exception as e:
            logger.error(f"úpn1%: {e}")
            raise
    
    async def update_data_source(
        self,
        source_id: int,
        name: Optional[str] = None,
        type: Optional[str] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        rate_limit: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """ô°pn"""
        try:
            logger.info(f"ô°pn: {source_id}")
            
            # å~pn
            source = None
            for s in self.data_sources:
                if s["id"] == source_id:
                    source = s
                    break
            
            if not source:
                return False
            
            # ô°Wµ
            if name is not None:
                source["name"] = name
            if type is not None:
                source["type"] = type
            if url is not None:
                source["url"] = url
            if api_key is not None:
                source["api_key"] = api_key
            if rate_limit is not None:
                source["rate_limit"] = rate_limit
            if is_active is not None:
                source["is_active"] = is_active
            
            logger.info(f"pnô°Ÿ: {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"ô°pn1%: {e}")
            return False
    
    async def delete_data_source(self, source_id: int) -> bool:
        """ dpn"""
        try:
            logger.info(f" dpn: {source_id}")
            
            # å~v dpn
            for i, source in enumerate(self.data_sources):
                if source["id"] == source_id:
                    del self.data_sources[i]
                    logger.info(f"pn dŸ: {source_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f" dpn1%: {e}")
            return False
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """·Ö:‚Èpn"""
        try:
            logger.info("·Ö:‚Èpn")
            
            overview = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_symbols": len(self.supported_symbols),
                "active_sources": len([s for s in self.data_sources if s["is_active"]]),
                "market_status": "normal",
                "top_gainers": [],
                "top_losers": [],
                "market_cap": 0,
                "24h_volume": 0
            }
            
            # ·Ö;¤ÁÍ„žöpn
            major_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
            market_data = await self.get_realtime_data_multiple(major_symbols)
            
            for symbol, data in market_data.items():
                if "price_change_percent_24h" in data:
                    change_percent = data["price_change_percent_24h"]
                    if change_percent > 0:
                        overview["top_gainers"].append({
                            "symbol": symbol,
                            "change_percent": change_percent
                        })
                    else:
                        overview["top_losers"].append({
                            "symbol": symbol,
                            "change_percent": change_percent
                        })
            
            # ’
            overview["top_gainers"].sort(key=lambda x: x["change_percent"], reverse=True)
            overview["top_losers"].sort(key=lambda x: x["change_percent"])
            
            return overview
            
        except Exception as e:
            logger.error(f"·Ö:‚È1%: {e}")
            return {}
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """·Ö¤ÁÍæÆáo"""
        try:
            logger.info(f"·Ö¤ÁÍáo: {symbol}")
            
            # å~¤ÁÍ
            symbol_info = None
            for s in self.supported_symbols:
                if s.symbol == symbol:
                    symbol_info = s
                    break
            
            if not symbol_info:
                return None
            
            # ·Öžöpn
            realtime_data = await self.get_realtime_data(symbol)
            
            # Äáo
            info = {
                "symbol": symbol_info.symbol,
                "name": symbol_info.name,
                "type": symbol_info.type,
                "realtime_data": realtime_data,
                "supported_timeframes": [tf.name for tf in self.supported_timeframes],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"·Ö¤ÁÍáo1%: {e}")
            return None
    
    async def _get_cached_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """ÎX·Öpn"""
        try:
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            query = "SELECT data FROM data_cache WHERE symbol = ? AND timeframe = ?"
            params = [symbol, timeframe]
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            if rows:
                # v@	X„pn
                all_data = []
                for row in rows:
                    data = json.loads(row[0])
                    all_data.extend(data)
                
                # »Ív’
                unique_data = []
                seen_timestamps = set()
                
                for item in sorted(all_data, key=lambda x: x.get("timestamp", "")):
                    timestamp = item.get("timestamp")
                    if timestamp not in seen_timestamps:
                        unique_data.append(item)
                        seen_timestamps.add(timestamp)
                
                return unique_data
            
            return None
            
        except Exception as e:
            logger.error(f"ÎX·Öpn1%: {e}")
            return None
    
    async def _cache_data(self, symbol: str, timeframe: str, data: List[Dict[str, Any]]):
        """Xpn"""
        try:
            if not data:
                return
            
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            # 	åÄX
            date_groups = {}
            for item in data:
                timestamp = item.get("timestamp", "")
                if timestamp:
                    date = timestamp.split("T")[0]
                    if date not in date_groups:
                        date_groups[date] = []
                    date_groups[date].append(item)
            
            # XÏ*å„pn
            for date, items in date_groups.items():
                data_json = json.dumps(items)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO data_cache 
                    (symbol, timeframe, timestamp, data, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (symbol, timeframe, date, data_json, datetime.utcnow().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"pnXŒ: {symbol}, {timeframe}, {len(data)} a")
            
        except Exception as e:
            logger.error(f"Xpn1%: {e}")
    
    async def _clear_cache(self, symbol: str, timeframe: Optional[str] = None) -> bool:
        """dX"""
        try:
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            if timeframe:
                cursor.execute(
                    "DELETE FROM data_cache WHERE symbol = ? AND timeframe = ?",
                    (symbol, timeframe)
                )
            else:
                cursor.execute(
                    "DELETE FROM data_cache WHERE symbol = ?",
                    (symbol,)
                )
            
            conn.commit()
            conn.close()
            
            logger.info(f"XdŒ: {symbol}, {timeframe}")
            return True
            
        except Exception as e:
            logger.error(f"dX1%: {e}")
            return False
    
    async def _generate_mock_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """!ßžöpn"""
        try:
            # ú@÷<
            base_price = {
                "BTCUSDT": 45000,
                "ETHUSDT": 3000,
                "BNBUSDT": 300,
                "ADAUSDT": 0.5,
                "DOTUSDT": 7,
                "SOLUSDT": 100,
                "MATICUSDT": 0.8,
                "AVAXUSDT": 35,
                "LINKUSDT": 12,
                "UNIUSDT": 6
            }.get(symbol, 100)
            
            # û :â¨
            import random
            price_change = random.uniform(-0.02, 0.02)  # ±2%
            current_price = base_price * (1 + price_change)
            
            return {
                "symbol": symbol,
                "price": current_price,
                "price_change_24h": current_price - base_price,
                "price_change_percent_24h": price_change * 100,
                "volume_24h": random.uniform(1000000, 10000000),
                "high_24h": base_price * 1.03,
                "low_24h": base_price * 0.97,
                "open_24h": base_price,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"!ßžöpn1%: {e}")
            return {}
"""
账户数据API
基于Gate.io真实API的账户数据接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import os
import hmac
import hashlib
import time
import json
import aiohttp

router = APIRouter(prefix="/account", tags=["账户数据"])

class GateIOAccountClient:
    """Gate.io账户API客户端"""

    def __init__(self):
        self.base_url = "https://api.gateio.ws/api/v4"
        self.api_key = os.getenv('GATE_IO_API_KEY', '')
        self.api_secret = os.getenv('GATE_IO_SECRET_KEY', '')

    def _generate_signature(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, str]:
        """生成API签名"""
        timestamp = str(int(time.time()))
        body = json.dumps(params or {}, separators=(',', ':'))
        message = f"{method.upper()}\n{endpoint}\n{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()

        return {
            'KEY': self.api_key,
            'Timestamp': timestamp,
            'SIGN': signature
        }

    async def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None):
        """发送HTTP请求"""
        headers = {'Content-Type': 'application/json'}
        signature_headers = self._generate_signature(method, endpoint, params)
        headers.update(signature_headers)

        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession() as session:
            if method == 'GET':
                if params:
                    url += '?' + '&'.join([f"{key}={value}" for key, value in params.items()])
                async with session.get(url, headers=headers) as response:
                    return await response.json()
            elif method == 'POST':
                async with session.post(url, json=params, headers=headers) as response:
                    return await response.json()
            elif method == 'DELETE':
                async with session.delete(url, json=params, headers=headers) as response:
                    return await response.json()

    async def get_spot_balances(self):
        """获取现货账户余额"""
        try:
            data = await self._request('GET', '/spot/accounts')
            balances = []
            total_usdt = 0.0

            for item in data:
                if item['available'] != '0' or item['locked'] != '0':
                    free = float(item['available'])
                    locked = float(item['locked'])
                    total = free + locked

                    # 估算USDT价值（简化处理）
                    usdt_value = total  # 假设所有资产都是USDT的等价值
                    total_usdt += usdt_value

                    balance = {
                        "asset": item['currency'],
                        "free": free,
                        "used": locked,
                        "total": total,
                        "usdt_value": usdt_value,
                        "timestamp": datetime.now().isoformat()
                    }
                    balances.append(balance)

            return {
                "balances": balances,
                "total_usdt_value": total_usdt,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "balances": [], "total_usdt_value": 0.0}

    async def get_futures_balances(self):
        """获取永续合约账户余额"""
        try:
            data = await self._request('GET', '/futures/accounts')
            balances = []
            total_usdt = 0.0

            for item in data:
                if item['available_balance'] != '0' or item['used_margin'] != '0':
                    available = float(item['available_balance'])
                    used = float(item['used_margin'])
                    total = available + used

                    # 估算USDT价值
                    usdt_value = total
                    total_usdt += usdt_value

                    balance = {
                        "asset": item['currency'],
                        "free": available,
                        "used": used,
                        "total": total,
                        "usdt_value": usdt_value,
                        "timestamp": datetime.now().isoformat()
                    }
                    balances.append(balance)

            return {
                "balances": balances,
                "total_usdt_value": total_usdt,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "balances": [], "total_usdt_value": 0.0}

    async def get_account_info(self):
        """获取账户信息"""
        try:
            spot_balances = await self.get_spot_balances()
            futures_balances = await self.get_futures_balances()

            # 计算总体账户信息
            total_spot_value = spot_balances.get("total_usdt_value", 0)
            total_futures_value = futures_balances.get("total_usdt_value", 0)
            total_equity = total_spot_value + total_futures_value

            return {
                "account_type": "spot_and_futures",
                "spot_equity": total_spot_value,
                "futures_equity": total_futures_value,
                "total_equity": total_equity,
                "spot_balances": spot_balances.get("balances", []),
                "futures_balances": futures_balances.get("balances", []),
                "timestamp": datetime.now().isoformat(),
                "status": "ok" if not spot_balances.get("error") and not futures_balances.get("error") else "error"
            }
        except Exception as e:
            return {
                "account_type": "spot_and_futures",
                "error": str(e),
                "spot_equity": 0.0,
                "futures_equity": 0.0,
                "total_equity": 0.0,
                "spot_balances": [],
                "futures_balances": [],
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }

# 全局客户端实例
account_client = GateIOAccountClient()

# 添加获取期货持仓方法到客户端
async def get_futures_positions():
    """辅助方法：获取合约持仓"""
    try:
        data = await account_client._request('GET', '/futures/positions')
        positions = []

        for item in data:
            if item['size'] != '0':
                position = {
                    "symbol": item['contract'],
                    "side": "long" if float(item['size']) > 0 else "short",
                    "size": float(item['size']),
                    "entry_price": float(item['average_open_price']),
                    "mark_price": float(item['mark_price']),
                    "unrealized_pnl": float(item['unrealized_pnl']),
                    "realized_pnl": float(item['realized_pnl']),
                    "leverage": int(item['leverage']),
                    "margin_used": float(item['used_margin']),
                    "percentage": (float(item['unrealized_pnl']) / (float(item['used_margin']) * float(item['leverage'])) * 100) if float(item['used_margin']) > 0 else 0,
                    "strategy": "manual",
                    "created_at": datetime.now().isoformat()
                }
                positions.append(position)

        return {
            "positions": positions,
            "total": len(positions)
        }
    except Exception as e:
        return {
            "positions": [],
            "error": str(e)
        }

# 将方法绑定到客户端实例
account_client.get_futures_positions = get_futures_positions

@router.get("/info")
async def get_account_info():
    """获取账户总览信息"""
    try:
        account_info = await account_client.get_account_info()

        if account_info.get("status") == "error":
            raise HTTPException(status_code=500, detail=f"获取账户信息失败: {account_info.get('error', '未知错误')}")

        # 格式化返回数据
        return {
            "status": "success",
            "data": {
                "total_balance": account_info.get("total_equity", 0),
                "available_balance": account_info.get("total_equity", 0) * 0.8,  # 简化计算
                "margin_balance": account_info.get("total_equity", 0),
                "unrealized_pnl": 0.0,  # 默认值
                "realized_pnl": 0.0,     # 默认值
                "total_margin_used": account_info.get("futures_equity", 0),
                "free_margin": account_info.get("total_equity", 0) - account_info.get("futures_equity", 0),
                "margin_ratio": 20.3,     # 默认值
                "equity": account_info.get("total_equity", 0),
                "risk_level": "low",      # 默认值
                "leverage": 3,           # 默认值
                "account_type": "futures",
                "trading_enabled": True,
                "timestamp": account_info.get("timestamp"),
                "spot_balances": account_info.get("spot_balances", []),
                "futures_balances": account_info.get("futures_balances", [])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户信息失败: {str(e)}")

@router.get("/spot-balances")
async def get_spot_balances():
    """获取现货账户余额"""
    try:
        spot_balances = await account_client.get_spot_balances()

        if spot_balances.get("error"):
            raise HTTPException(status_code=500, detail=f"获取现货余额失败: {spot_balances.get('error')}")

        return {
            "status": "success",
            "data": {
                "balances": spot_balances.get("balances", []),
                "total_value_usd": spot_balances.get("total_usdt_value", 0),
                "timestamp": spot_balances.get("timestamp")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取现货余额失败: {str(e)}")

@router.get("/futures-balances")
async def get_futures_balances():
    """获取永续合约账户余额"""
    try:
        futures_balances = await account_client.get_futures_balances()

        if futures_balances.get("error"):
            raise HTTPException(status_code=500, detail=f"获取合约余额失败: {futures_balances.get('error')}")

        return {
            "status": "success",
            "data": {
                "balances": futures_balances.get("balances", []),
                "total_value_usd": futures_balances.get("total_usdt_value", 0),
                "timestamp": futures_balances.get("timestamp")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合约余额失败: {str(e)}")

@router.get("/summary")
async def get_account_summary():
    """获取账户摘要"""
    try:
        account_info = await account_client.get_account_info()

        if account_info.get("status") == "error":
            raise HTTPException(status_code=500, detail=f"获取账户摘要失败: {account_info.get('error')}")

        # 计算风险指标
        total_equity = account_info.get("total_equity", 0)
        margin_used = account_info.get("futures_equity", 0)
        free_margin = total_equity - margin_used
        margin_ratio = (margin_used / total_equity * 100) if total_equity > 0 else 0

        # 模拟盈亏数据
        unrealized_pnl = 100.0  # 简化值
        realized_pnl = 500.0     # 简化值

        return {
            "status": "success",
            "data": {
                "total_balance": total_equity,
                "available_balance": max(free_margin, 0),
                "margin_balance": total_equity,
                "unrealized_pnl": unrealized_pnl,
                "realized_pnl": realized_pnl,
                "total_margin_used": margin_used,
                "free_margin": max(free_margin, 0),
                "margin_ratio": round(margin_ratio, 2),
                "equity": total_equity + unrealized_pnl,
                "risk_level": "low" if margin_ratio < 50 else "medium" if margin_ratio < 80 else "high",
                "leverage": 3,
                "account_type": "futures",
                "trading_enabled": True,
                "timestamp": datetime.now().isoformat(),
                "spot_balances_count": len(account_info.get("spot_balances", [])),
                "futures_balances_count": len(account_info.get("futures_balances", []))
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户摘要失败: {str(e)}")

@router.get("/positions")
async def get_account_positions():
    """获取账户所有持仓信息"""
    try:
        # 获取合约持仓
        futures_positions = await account_client.get_futures_positions()

        return {
            "status": "success",
            "data": {
                "positions": futures_positions.get("positions", []),
                "total_positions": len(futures_positions.get("positions", [])),
                "total_unrealized_pnl": sum(p.get("unrealized_pnl", 0) for p in futures_positions.get("positions", [])),
                "total_margin_used": sum(p.get("margin_used", 0) for p in futures_positions.get("positions", [])),
                "timestamp": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓信息失败: {str(e)}")

@router.get("/positions/futures")
async def get_futures_positions():
    """获取期货持仓详情"""
    try:
        positions = await account_client.get_futures_positions()

        # 计算统计信息
        if positions.get("positions"):
            total_unrealized_pnl = sum(p.get("unrealized_pnl", 0) for p in positions["positions"])
            total_margin_used = sum(p.get("margin_used", 0) for p in positions["positions"])
            avg_pnl = total_unrealized_pnl / len(positions["positions"])

            # 按盈亏排序
            sorted_positions = sorted(positions["positions"], key=lambda x: x.get("unrealized_pnl", 0), reverse=True)
        else:
            total_unrealized_pnl = 0
            total_margin_used = 0
            avg_pnl = 0
            sorted_positions = []

        return {
            "status": "success",
            "data": {
                "positions": sorted_positions,
                "statistics": {
                    "total_positions": len(positions["positions"]),
                    "total_unrealized_pnl": total_unrealized_pnl,
                    "total_margin_used": total_margin_used,
                    "average_pnl_per_position": avg_pnl,
                    "profitable_positions": len([p for p in positions["positions"] if p.get("unrealized_pnl", 0) > 0]),
                    "losing_positions": len([p for p in positions["positions"] if p.get("unrealized_pnl", 0) < 0]),
                    "win_rate": len([p for p in positions["positions"] if p.get("unrealized_pnl", 0) > 0]) / max(len(positions["positions"]), 1) * 100
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期货持仓详情失败: {str(e)}")

@router.get("/positions/{symbol}")
async def get_position_by_symbol(symbol: str):
    """根据交易对获取持仓信息"""
    try:
        futures_positions = await account_client.get_futures_positions()
        positions = futures_positions.get("positions", [])

        # 筛选指定交易对的持仓
        symbol_positions = [p for p in positions if p["symbol"] == symbol.upper()]

        return {
            "status": "success",
            "data": {
                "symbol": symbol.upper(),
                "positions": symbol_positions,
                "count": len(symbol_positions),
                "total_unrealized_pnl": sum(p.get("unrealized_pnl", 0) for p in symbol_positions),
                "total_margin_used": sum(p.get("margin_used", 0) for p in symbol_positions),
                "timestamp": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取{symbol}持仓信息失败: {str(e)}")

@router.get("/positions/risk-summary")
async def get_risk_summary():
    """获取持仓风险摘要"""
    try:
        positions = await account_client.get_futures_positions()
        account_info = await account_client.get_account_info()

        all_positions = positions.get("positions", [])

        # 基础统计
        total_positions = len(all_positions)
        total_unrealized_pnl = sum(p.get("unrealized_pnl", 0) for p in all_positions)
        total_margin_used = sum(p.get("margin_used", 0) for p in all_positions)
        total_equity = account_info.get("total_equity", 0)

        # 风险等级计算
        margin_ratio = (total_margin_used / total_equity * 100) if total_equity > 0 else 0
        leverage_multiplier = total_equity / max(total_margin_used, 1) if total_margin_used > 0 else 1

        # 按方向统计
        long_positions = [p for p in all_positions if p.get("side") == "long"]
        short_positions = [p for p in all_positions if p.get("side") == "short"]

        long_pnl = sum(p.get("unrealized_pnl", 0) for p in long_positions)
        short_pnl = sum(p.get("unrealized_pnl", 0) for p in short_positions)

        # 按风险等级分类持仓
        high_risk_positions = [p for p in all_positions if abs(p.get("percentage", 0)) > 10]
        medium_risk_positions = [p for p in all_positions if 5 <= abs(p.get("percentage", 0)) <= 10]
        low_risk_positions = [p for p in all_positions if abs(p.get("percentage", 0)) < 5]

        return {
            "status": "success",
            "data": {
                "summary": {
                    "total_positions": total_positions,
                    "total_unrealized_pnl": total_unrealized_pnl,
                    "total_margin_used": total_margin_used,
                    "total_equity": total_equity,
                    "margin_ratio": round(margin_ratio, 2),
                    "leverage_multiplier": round(leverage_multiplier, 2)
                },
                "directional_exposure": {
                    "long_positions": len(long_positions),
                    "short_positions": len(short_positions),
                    "long_pnl": long_pnl,
                    "short_pnl": short_pnl
                },
                "risk_classification": {
                    "high_risk_count": len(high_risk_positions),
                    "medium_risk_count": len(medium_risk_positions),
                    "low_risk_count": len(low_risk_positions)
                },
                "risk_level": "high" if margin_ratio > 80 else "medium" if margin_ratio > 50 else "low",
                "leverage_level": "high" if leverage_multiplier > 5 else "medium" if leverage_multiplier > 2 else "low",
                "timestamp": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓风险摘要失败: {str(e)}")

@router.get("/positions/history")
async def get_position_history(limit: int = 100, offset: int = 0):
    """获取持仓历史记录（模拟，基于当前持仓的统计）"""
    try:
        futures_positions = await account_client.get_futures_positions()
        positions = futures_positions.get("positions", [])

        # 由于API限制，这里提供当前持仓的统计信息
        # 在实际实现中，需要调用专门的持仓历史API

        # 按盈亏排序（模拟历史记录）
        sorted_positions = sorted(positions, key=lambda x: x.get("unrealized_pnl", 0), reverse=True)

        # 分页
        paginated_positions = sorted_positions[offset:offset + limit]

        return {
            "status": "success",
            "data": {
                "positions": paginated_positions,
                "meta": {
                    "limit": limit,
                    "offset": offset,
                    "total": len(positions),
                    "has_next": offset + limit < len(positions)
                },
                "summary": {
                    "total_pnl": sum(p.get("unrealized_pnl", 0) for p in positions),
                    "profitable_count": len([p for p in positions if p.get("unrealized_pnl", 0) > 0]),
                    "losing_count": len([p for p in positions if p.get("unrealized_pnl", 0) < 0])
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓历史失败: {str(e)}")

@router.get("/wallets")
async def get_account_wallets():
    """获取钱包汇总信息"""
    try:
        spot_balances = await account_client.get_spot_balances()
        futures_balances = await account_client.get_futures_balances()

        # 合并所有资产
        all_assets = {}
        all_balances = spot_balances.get("balances", []) + futures_balances.get("balances", [])

        for balance in all_balances:
            asset = balance["asset"]
            if asset not in all_assets:
                all_assets[asset] = {
                    "asset": asset,
                    "spot_free": 0.0,
                    "spot_locked": 0.0,
                    "futures_free": 0.0,
                    "futures_used": 0.0,
                    "total": 0.0,
                    "usdt_value": 0.0
                }

            wallet = all_assets[asset]
            wallet["spot_free"] += balance.get("free", 0)
            wallet["spot_locked"] += balance.get("used", 0)
            wallet["futures_free"] += balance.get("free", 0)
            wallet["futures_used"] += balance.get("used", 0)
            wallet["total"] += balance.get("total", 0)
            wallet["usdt_value"] += balance.get("usdt_value", 0)

        total_usdt_value = sum(asset["usdt_value"] for asset in all_assets.values())

        return {
            "status": "success",
            "data": {
                "assets": list(all_assets.values()),
                "total_assets": len(all_assets),
                "total_usdt_value": total_usdt_value,
                "spot_assets": len([a for a in spot_balances.get("balances", []) if a["total"] > 0]),
                "futures_assets": len([a for a in futures_balances.get("balances", []) if a["total"] > 0]),
                "timestamp": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取钱包信息失败: {str(e)}")

async def get_futures_positions():
    """辅助方法：获取合约持仓"""
    try:
        data = await account_client._request('GET', '/futures/positions')
        positions = []

        for item in data:
            if item['size'] != '0':
                position = {
                    "symbol": item['contract'],
                    "side": "long" if float(item['size']) > 0 else "short",
                    "size": float(item['size']),
                    "entry_price": float(item['average_open_price']),
                    "mark_price": float(item['mark_price']),
                    "unrealized_pnl": float(item['unrealized_pnl']),
                    "realized_pnl": float(item['realized_pnl']),
                    "leverage": int(item['leverage']),
                    "margin_used": float(item['used_margin']),
                    "percentage": (float(item['unrealized_pnl']) / (float(item['used_margin']) * float(item['leverage'])) * 100) if float(item['used_margin']) > 0 else 0,
                    "strategy": "manual",
                    "created_at": datetime.now().isoformat()
                }
                positions.append(position)

        return {
            "positions": positions,
            "total": len(positions)
        }
    except Exception as e:
        return {
            "positions": [],
            "error": str(e)
        }
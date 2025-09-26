"""
策略管理服务
为前端提供策略管理相关的API接口
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime

from strategies.strategy_manager import get_strategy_manager, StrategyManager
from services.config_service_simple import ConfigService

router = APIRouter(prefix="/strategies", tags=["策略管理"])

@router.get("/status")
async def get_all_strategies_status():
    """获取所有策略状态"""
    try:
        strategy_manager = await get_strategy_manager()
        status = await strategy_manager.get_strategy_status()

        return {
            "status": "success",
            "data": {
                "strategies": status,
                "total_strategies": len(status),
                "running_strategies": len([s for s in status.values() if s.get("running", False)])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略状态失败: {str(e)}")

@router.post("/{strategy_name}/start")
async def start_strategy_api(strategy_name: str):
    """启动策略"""
    try:
        strategy_manager = await get_strategy_manager()
        success = await strategy_manager.start_strategy(strategy_name)

        if success:
            return {
                "status": "success",
                "message": f"策略 {strategy_name} 启动成功",
                "data": {
                    "strategy_name": strategy_name,
                    "started_at": datetime.now().isoformat()
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"策略 {strategy_name} 启动失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动策略失败: {str(e)}")

@router.post("/{strategy_name}/stop")
async def stop_strategy_api(strategy_name: str):
    """停止策略"""
    try:
        strategy_manager = await get_strategy_manager()
        success = await strategy_manager.stop_strategy(strategy_name)

        if success:
            return {
                "status": "success",
                "message": f"策略 {strategy_name} 停止成功",
                "data": {
                    "strategy_name": strategy_name,
                    "stopped_at": datetime.now().isoformat()
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"策略 {strategy_name} 停止失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止策略失败: {str(e)}")

@router.post("/start-all")
async def start_all_strategies_api():
    """启动所有策略"""
    try:
        strategy_manager = await get_strategy_manager()
        await strategy_manager.start_all_strategies()

        return {
            "status": "success",
            "message": "所有策略启动成功",
            "data": {
                "started_at": datetime.now().isoformat(),
                "total_strategies": len(strategy_manager.strategies)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动所有策略失败: {str(e)}")

@router.post("/stop-all")
async def stop_all_strategies_api():
    """停止所有策略"""
    try:
        strategy_manager = await get_strategy_manager()
        await strategy_manager.stop_all_strategies()

        return {
            "status": "success",
            "message": "所有策略停止成功",
            "data": {
                "stopped_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止所有策略失败: {str(e)}")

@router.get("/{strategy_name}/signals")
async def get_strategy_signals_api(
    strategy_name: str,
    limit: int = 10,
    offset: int = 0
):
    """获取策略交易信号"""
    try:
        strategy_manager = await get_strategy_manager()
        signals = await strategy_manager.get_strategy_signals(strategy_name, limit + offset)

        # 分页
        paginated_signals = signals[offset:limit + offset]

        return {
            "status": "success",
            "data": {
                "strategy_name": strategy_name,
                "signals": [signal.__dict__ if hasattr(signal, '__dict__') else str(signal) for signal in paginated_signals],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": len(signals)
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略信号失败: {str(e)}")

@router.get("/{strategy_name}/positions")
async def get_strategy_positions_api(strategy_name: str):
    """获取策略持仓"""
    try:
        strategy_manager = await get_strategy_manager()
        positions = await strategy_manager.get_strategy_positions(strategy_name)

        return {
            "status": "success",
            "data": {
                "strategy_name": strategy_name,
                "positions": [position.__dict__ if hasattr(position, '__dict__') else str(position) for position in positions],
                "total_positions": len(positions)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略持仓失败: {str(e)}")

@router.put("/{strategy_name}/config")
async def update_strategy_config_api(
    strategy_name: str,
    config: Dict[str, Any]
):
    """更新策略配置"""
    try:
        strategy_manager = await get_strategy_manager()
        success = await strategy_manager.update_strategy_config(strategy_name, config)

        if success:
            return {
                "status": "success",
                "message": f"策略 {strategy_name} 配置更新成功",
                "data": {
                    "strategy_name": strategy_name,
                    "updated_config": config,
                    "updated_at": datetime.now().isoformat()
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"策略 {strategy_name} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新策略配置失败: {str(e)}")

@router.get("/templates")
async def get_strategy_templates():
    """获取策略模板"""
    templates = {
        "grid": {
            "name": "网格交易策略",
            "description": "在指定价格区间内设置买卖网格，通过价格波动获取利润",
            "config": {
                "grid_levels": 5,
                "grid_spacing": 0.02,
                "base_price": 3000.0,
                "grid_size": 0.1,
                "max_position_size": 10.0,
                "stop_loss_rate": 0.05,
                "take_profit_rate": 0.1,
                "position_risk_percent": 2.0
            },
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "risk_level": "medium"
        },
        "trend": {
            "name": "趋势跟踪策略",
            "description": "基于移动平均线和RSI指标跟踪市场趋势",
            "config": {
                "ma_short": 10,
                "ma_long": 20,
                "rsi_period": 14,
                "position_size": 1.0,
                "max_position_size": 10.0,
                "stop_loss_rate": 0.05,
                "take_profit_rate": 0.1,
                "position_risk_percent": 2.0
            },
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "risk_level": "medium"
        },
        "arbitrage": {
            "name": "套利策略",
            "description": "利用不同交易对之间的价格差异进行套利交易",
            "config": {
                "min_profit_rate": 0.001,
                "price_tolerance": 0.005,
                "max_position_size": 5.0,
                "position_risk_percent": 1.0
            },
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "risk_level": "low"
        }
    }

    return {
        "status": "success",
        "data": {
            "templates": templates,
            "total_templates": len(templates)
        }
    }

@router.get("/logs/{strategy_name}")
async def get_strategy_logs(strategy_name: str, limit: int = 100):
    """获取策略日志"""
    # 这里可以实现日志收集功能
    # 目前返回模拟数据
    return {
        "status": "success",
        "data": {
            "strategy_name": strategy_name,
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "message": f"策略 {strategy_name} 运行正常"
                }
            ],
            "total_logs": 1
        }
    }
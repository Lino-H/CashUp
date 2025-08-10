from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

from shared.exchanges import get_exchange_manager, ExchangeInfo, ExchangeType
from ..core.exchange_pool import exchange_pool

router = APIRouter()


class ExchangeInfoResponse(BaseModel):
    """交易所信息响应"""
    name: str
    display_name: str
    supported_types: List[str]
    api_version: str
    testnet_available: bool
    rate_limits: Dict[str, int]
    description: str


class ExchangeConnectionRequest(BaseModel):
    """交易所连接请求"""
    exchange_name: str
    api_key: str
    api_secret: str
    testnet: bool = False


class ExchangeConnectionResponse(BaseModel):
    """交易所连接响应"""
    success: bool
    message: str
    exchange_info: ExchangeInfoResponse


class ActiveConnectionResponse(BaseModel):
    """活跃连接响应"""
    connection_key: str
    exchange_name: str
    display_name: str


@router.get("/available", response_model=List[ExchangeInfoResponse])
async def get_available_exchanges():
    """获取所有可用的交易所列表"""
    try:
        manager = get_exchange_manager()
        exchanges = manager.get_available_exchanges()
        
        return [
            ExchangeInfoResponse(
                name=exchange.name,
                display_name=exchange.display_name,
                supported_types=[t.value for t in exchange.supported_types],
                api_version=exchange.api_version,
                testnet_available=exchange.testnet_available,
                rate_limits=exchange.rate_limits,
                description=exchange.description
            )
            for exchange in exchanges
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易所列表失败: {str(e)}")


@router.get("/available/{exchange_name}", response_model=ExchangeInfoResponse)
async def get_exchange_info(exchange_name: str):
    """获取指定交易所信息"""
    try:
        manager = get_exchange_manager()
        exchange_info = manager.get_exchange_info(exchange_name)
        
        if not exchange_info:
            raise HTTPException(status_code=404, detail=f"交易所 '{exchange_name}' 不存在")
        
        return ExchangeInfoResponse(
            name=exchange_info.name,
            display_name=exchange_info.display_name,
            supported_types=[t.value for t in exchange_info.supported_types],
            api_version=exchange_info.api_version,
            testnet_available=exchange_info.testnet_available,
            rate_limits=exchange_info.rate_limits,
            description=exchange_info.description
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易所信息失败: {str(e)}")


@router.get("/by-type/{exchange_type}", response_model=List[ExchangeInfoResponse])
async def get_exchanges_by_type(exchange_type: str):
    """根据交易类型获取支持的交易所"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        manager = get_exchange_manager()
        exchanges = manager.get_exchanges_by_type(ex_type)
        
        return [
            ExchangeInfoResponse(
                name=exchange.name,
                display_name=exchange.display_name,
                supported_types=[t.value for t in exchange.supported_types],
                api_version=exchange.api_version,
                testnet_available=exchange.testnet_available,
                rate_limits=exchange.rate_limits,
                description=exchange.description
            )
            for exchange in exchanges
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易所列表失败: {str(e)}")


@router.post("/connect", response_model=ExchangeConnectionResponse)
async def connect_exchange(request: ExchangeConnectionRequest):
    """连接到指定交易所"""
    try:
        # 验证交易所是否存在
        manager = get_exchange_manager()
        if not manager.is_exchange_available(request.exchange_name):
            raise HTTPException(status_code=404, detail=f"交易所 '{request.exchange_name}' 不存在")
        
        # 创建连接
        exchange = await exchange_pool.pool.get_exchange(
            request.exchange_name,
            request.api_key,
            request.api_secret,
            request.testnet
        )
        
        exchange_info = exchange.get_exchange_info()
        
        return ExchangeConnectionResponse(
            success=True,
            message=f"成功连接到 {exchange_info.display_name}",
            exchange_info=ExchangeInfoResponse(
                name=exchange_info.name,
                display_name=exchange_info.display_name,
                supported_types=[t.value for t in exchange_info.supported_types],
                api_version=exchange_info.api_version,
                testnet_available=exchange_info.testnet_available,
                rate_limits=exchange_info.rate_limits,
                description=exchange_info.description
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接交易所失败: {str(e)}")


@router.get("/connections", response_model=List[ActiveConnectionResponse])
async def get_active_connections():
    """获取活跃的交易所连接"""
    try:
        connections = exchange_pool.pool.get_active_connections()
        
        return [
            ActiveConnectionResponse(
                connection_key=key,
                exchange_name=key.split(":")[0],
                display_name=display_name
            )
            for key, display_name in connections.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取连接列表失败: {str(e)}")


@router.delete("/disconnect/{exchange_name}")
async def disconnect_exchange(exchange_name: str, api_key: str, testnet: bool = False):
    """断开指定的交易所连接"""
    try:
        success = await exchange_pool.pool.close_exchange(exchange_name, api_key, testnet)
        
        if success:
            return {"success": True, "message": f"已断开 {exchange_name} 连接"}
        else:
            raise HTTPException(status_code=404, detail="连接不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"断开连接失败: {str(e)}")


@router.get("/status")
async def get_exchange_service_status():
    """获取交易所服务状态"""
    try:
        manager = get_exchange_manager()
        
        return {
            "service": "Exchange Service",
            "status": "running",
            "available_exchanges": manager.get_exchange_names(),
            "active_connections": exchange_pool.pool.get_connection_count(),
            "supported_types": [t.value for t in ExchangeType]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务状态失败: {str(e)}")
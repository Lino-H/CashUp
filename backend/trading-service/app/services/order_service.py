#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务

提供订单管理相关的业务逻辑
"""

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus, OrderType, OrderSide
from app.models.trade import Trade
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderFilter, OrderResponse,
    OrderListResponse, OrderSummary, BatchOrderCreate
)
from app.core.redis import RedisManager
from app.services.balance_service import BalanceService
from app.services.position_service import PositionService

logger = logging.getLogger("order_service")


class OrderService:
    """
    订单服务类
    
    提供订单的创建、更新、取消、查询等功能
    """
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
        self.balance_service = BalanceService(redis_manager)
        self.position_service = PositionService(redis_manager)
    
    async def create_order(self, db: AsyncSession, user_id: int, order_data: OrderCreate) -> OrderResponse:
        """
        创建订单
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            order_data: 订单数据
            
        Returns:
            OrderResponse: 创建的订单
            
        Raises:
            ValueError: 订单数据无效
            Exception: 创建失败
        """
        try:
            # 验证订单数据
            await self._validate_order_data(db, user_id, order_data)
            
            # 检查余额是否充足
            await self._check_balance_sufficient(db, user_id, order_data)
            
            # 解析交易对
            base_asset, quote_asset = self._parse_symbol(order_data.symbol)
            
            # 创建订单对象
            order = Order(
                user_id=user_id,
                order_id=self._generate_order_id(),
                client_order_id=order_data.client_order_id,
                symbol=order_data.symbol,
                base_asset=base_asset,
                quote_asset=quote_asset,
                order_type=order_data.order_type,
                side=order_data.side,
                status=OrderStatus.NEW,
                time_in_force=order_data.time_in_force,
                quantity=order_data.quantity,
                price=order_data.price,
                stop_price=order_data.stop_price,
                iceberg_qty=order_data.iceberg_qty,
                strategy_id=order_data.strategy_id,
                strategy_name=order_data.strategy_name,
                notes=order_data.notes,
            )
            
            # 保存到数据库
            db.add(order)
            await db.commit()
            await db.refresh(order)
            
            # 冻结相关资产
            await self._freeze_order_assets(db, order)
            
            # 缓存订单信息
            await self._cache_order(order)
            
            # 发布订单创建事件
            await self._publish_order_event(order, "created")
            
            logger.info(f"订单创建成功: user_id={user_id}, order_id={order.order_id}")
            
            return OrderResponse.from_orm(order)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建订单失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def update_order(self, db: AsyncSession, user_id: int, order_id: str, order_data: OrderUpdate) -> OrderResponse:
        """
        更新订单
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            order_id: 订单ID
            order_data: 更新数据
            
        Returns:
            OrderResponse: 更新后的订单
            
        Raises:
            ValueError: 订单不存在或无法更新
        """
        try:
            # 获取订单
            order = await self._get_order_by_id(db, user_id, order_id)
            if not order:
                raise ValueError(f"订单不存在: {order_id}")
            
            # 检查订单状态
            if order.status not in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]:
                raise ValueError(f"订单状态不允许更新: {order.status}")
            
            # 更新订单字段
            if order_data.quantity is not None:
                order.quantity = order_data.quantity
            if order_data.price is not None:
                order.price = order_data.price
            if order_data.stop_price is not None:
                order.stop_price = order_data.stop_price
            if order_data.time_in_force is not None:
                order.time_in_force = order_data.time_in_force
            if order_data.notes is not None:
                order.notes = order_data.notes
            
            order.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(order)
            
            # 更新缓存
            await self._cache_order(order)
            
            # 发布订单更新事件
            await self._publish_order_event(order, "updated")
            
            logger.info(f"订单更新成功: order_id={order_id}")
            
            return OrderResponse.from_orm(order)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新订单失败: order_id={order_id}, error={str(e)}")
            raise
    
    async def cancel_order(self, db: AsyncSession, user_id: int, order_id: str, reason: Optional[str] = None) -> OrderResponse:
        """
        取消订单
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            order_id: 订单ID
            reason: 取消原因
            
        Returns:
            OrderResponse: 取消后的订单
            
        Raises:
            ValueError: 订单不存在或无法取消
        """
        try:
            # 获取订单
            order = await self._get_order_by_id(db, user_id, order_id)
            if not order:
                raise ValueError(f"订单不存在: {order_id}")
            
            # 检查订单状态
            if order.status not in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]:
                raise ValueError(f"订单状态不允许取消: {order.status}")
            
            # 更新订单状态
            order.status = OrderStatus.CANCELLED
            order.cancel_reason = reason
            order.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(order)
            
            # 解冻相关资产
            await self._unfreeze_order_assets(db, order)
            
            # 更新缓存
            await self._cache_order(order)
            
            # 发布订单取消事件
            await self._publish_order_event(order, "cancelled")
            
            logger.info(f"订单取消成功: order_id={order_id}, reason={reason}")
            
            return OrderResponse.from_orm(order)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"取消订单失败: order_id={order_id}, error={str(e)}")
            raise
    
    async def get_order(self, db: AsyncSession, user_id: int, order_id: str) -> Optional[OrderResponse]:
        """
        获取订单详情
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            order_id: 订单ID
            
        Returns:
            Optional[OrderResponse]: 订单详情
        """
        order = await self._get_order_by_id(db, user_id, order_id)
        if order:
            return OrderResponse.from_orm(order)
        return None
    
    async def list_orders(self, db: AsyncSession, user_id: int, filter_params: OrderFilter) -> OrderListResponse:
        """
        获取订单列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            filter_params: 过滤参数
            
        Returns:
            OrderListResponse: 订单列表
        """
        try:
            # 构建查询条件
            conditions = [Order.user_id == user_id]
            
            if filter_params.symbol:
                conditions.append(Order.symbol == filter_params.symbol)
            if filter_params.order_type:
                conditions.append(Order.order_type == filter_params.order_type)
            if filter_params.side:
                conditions.append(Order.side == filter_params.side)
            if filter_params.status:
                conditions.append(Order.status == filter_params.status)
            if filter_params.strategy_id:
                conditions.append(Order.strategy_id == filter_params.strategy_id)
            if filter_params.start_time:
                conditions.append(Order.created_at >= filter_params.start_time)
            if filter_params.end_time:
                conditions.append(Order.created_at <= filter_params.end_time)
            if filter_params.min_quantity:
                conditions.append(Order.quantity >= filter_params.min_quantity)
            if filter_params.max_quantity:
                conditions.append(Order.quantity <= filter_params.max_quantity)
            if filter_params.min_price:
                conditions.append(Order.price >= filter_params.min_price)
            if filter_params.max_price:
                conditions.append(Order.price <= filter_params.max_price)
            
            # 查询总数
            count_query = select(func.count(Order.id)).where(and_(*conditions))
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # 查询订单列表
            offset = (filter_params.page - 1) * filter_params.size
            query = (
                select(Order)
                .where(and_(*conditions))
                .order_by(desc(Order.created_at))
                .offset(offset)
                .limit(filter_params.size)
            )
            
            result = await db.execute(query)
            orders = result.scalars().all()
            
            # 计算分页信息
            pages = (total + filter_params.size - 1) // filter_params.size
            
            return OrderListResponse(
                orders=[OrderResponse.from_orm(order) for order in orders],
                total=total,
                page=filter_params.page,
                size=filter_params.size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"获取订单列表失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_order_summary(self, db: AsyncSession, user_id: int) -> OrderSummary:
        """
        获取订单摘要
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            OrderSummary: 订单摘要
        """
        try:
            # 查询订单统计
            query = (
                select(
                    func.count(Order.id).label('total_orders'),
                    func.count(Order.id).filter(Order.status.in_([OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED])).label('active_orders'),
                    func.count(Order.id).filter(Order.status == OrderStatus.FILLED).label('completed_orders'),
                    func.count(Order.id).filter(Order.status == OrderStatus.CANCELLED).label('cancelled_orders'),
                    func.sum(Order.executed_quantity).label('total_volume'),
                    func.sum(Order.executed_quantity * Order.avg_price).label('total_value'),
                )
                .where(Order.user_id == user_id)
            )
            
            result = await db.execute(query)
            stats = result.first()
            
            # 计算平均执行时间
            avg_execution_time = None
            execution_query = (
                select(func.avg(func.extract('epoch', Order.executed_at - Order.created_at)))
                .where(and_(Order.user_id == user_id, Order.executed_at.isnot(None)))
            )
            execution_result = await db.execute(execution_query)
            avg_execution_time = execution_result.scalar()
            
            return OrderSummary(
                total_orders=stats.total_orders or 0,
                active_orders=stats.active_orders or 0,
                completed_orders=stats.completed_orders or 0,
                cancelled_orders=stats.cancelled_orders or 0,
                total_volume=stats.total_volume or Decimal('0'),
                total_value=stats.total_value or Decimal('0'),
                avg_execution_time=avg_execution_time
            )
            
        except Exception as e:
            logger.error(f"获取订单摘要失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def batch_create_orders(self, db: AsyncSession, user_id: int, batch_data: BatchOrderCreate) -> Dict[str, Any]:
        """
        批量创建订单
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            batch_data: 批量订单数据
            
        Returns:
            Dict[str, Any]: 批量创建结果
        """
        success_orders = []
        failed_orders = []
        
        for order_data in batch_data.orders:
            try:
                order_response = await self.create_order(db, user_id, order_data)
                success_orders.append(order_response)
            except Exception as e:
                failed_orders.append({
                    "order_data": order_data.dict(),
                    "error": str(e)
                })
        
        return {
            "success_orders": success_orders,
            "failed_orders": failed_orders,
            "total_count": len(batch_data.orders),
            "success_count": len(success_orders),
            "failed_count": len(failed_orders)
        }
    
    async def execute_order(self, db: AsyncSession, order_id: str, executed_quantity: Decimal, executed_price: Decimal) -> bool:
        """
        执行订单（部分或全部）
        
        Args:
            db: 数据库会话
            order_id: 订单ID
            executed_quantity: 执行数量
            executed_price: 执行价格
            
        Returns:
            bool: 是否执行成功
        """
        try:
            # 获取订单
            query = select(Order).where(Order.order_id == order_id)
            result = await db.execute(query)
            order = result.scalar_one_or_none()
            
            if not order:
                logger.error(f"订单不存在: {order_id}")
                return False
            
            # 检查订单状态
            if order.status not in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]:
                logger.error(f"订单状态不允许执行: {order.status}")
                return False
            
            # 更新订单执行信息
            order.executed_quantity += executed_quantity
            order.remaining_quantity = order.quantity - order.executed_quantity
            
            # 计算平均价格
            if order.avg_price is None:
                order.avg_price = executed_price
            else:
                total_value = (order.executed_quantity - executed_quantity) * order.avg_price + executed_quantity * executed_price
                order.avg_price = total_value / order.executed_quantity
            
            # 更新订单状态
            if order.remaining_quantity <= 0:
                order.status = OrderStatus.FILLED
                order.executed_at = datetime.utcnow()
            else:
                order.status = OrderStatus.PARTIALLY_FILLED
            
            order.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(order)
            
            # 更新持仓
            await self.position_service.update_position_from_trade(
                db, order.user_id, order.symbol, order.side.value, executed_quantity, executed_price
            )
            
            # 更新缓存
            await self._cache_order(order)
            
            # 发布订单执行事件
            await self._publish_order_event(order, "executed")
            
            logger.info(f"订单执行成功: order_id={order_id}, quantity={executed_quantity}, price={executed_price}")
            
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"执行订单失败: order_id={order_id}, error={str(e)}")
            return False
    
    # 私有方法
    
    async def _validate_order_data(self, db: AsyncSession, user_id: int, order_data: OrderCreate) -> None:
        """
        验证订单数据
        """
        # 验证交易对
        if not self._is_valid_symbol(order_data.symbol):
            raise ValueError(f"无效的交易对: {order_data.symbol}")
        
        # 验证价格和数量
        if order_data.quantity <= 0:
            raise ValueError("订单数量必须大于0")
        
        if order_data.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            if not order_data.price or order_data.price <= 0:
                raise ValueError("限价订单必须指定有效价格")
        
        if order_data.order_type in [OrderType.STOP_MARKET, OrderType.STOP_LIMIT]:
            if not order_data.stop_price or order_data.stop_price <= 0:
                raise ValueError("止损订单必须指定有效止损价格")
    
    async def _check_balance_sufficient(self, db: AsyncSession, user_id: int, order_data: OrderCreate) -> None:
        """
        检查余额是否充足
        """
        base_asset, quote_asset = self._parse_symbol(order_data.symbol)
        
        if order_data.side == OrderSide.BUY:
            # 买入需要计价资产
            required_amount = order_data.quantity * (order_data.price or Decimal('0'))
            asset = quote_asset
        else:
            # 卖出需要基础资产
            required_amount = order_data.quantity
            asset = base_asset
        
        # 检查余额
        balance = await self.balance_service.get_balance(db, user_id, asset)
        if not balance or balance.available_balance < required_amount:
            raise ValueError(f"余额不足: 需要 {required_amount} {asset}")
    
    async def _freeze_order_assets(self, db: AsyncSession, order: Order) -> None:
        """
        冻结订单相关资产
        """
        if order.side == OrderSide.BUY:
            # 买入冻结计价资产
            required_amount = order.quantity * (order.price or Decimal('0'))
            asset = order.quote_asset
        else:
            # 卖出冻结基础资产
            required_amount = order.quantity
            asset = order.base_asset
        
        await self.balance_service.freeze_balance(db, order.user_id, asset, required_amount)
    
    async def _unfreeze_order_assets(self, db: AsyncSession, order: Order) -> None:
        """
        解冻订单相关资产
        """
        if order.side == OrderSide.BUY:
            # 买入解冻计价资产
            remaining_amount = order.remaining_quantity * (order.price or Decimal('0'))
            asset = order.quote_asset
        else:
            # 卖出解冻基础资产
            remaining_amount = order.remaining_quantity
            asset = order.base_asset
        
        await self.balance_service.unfreeze_balance(db, order.user_id, asset, remaining_amount)
    
    async def _get_order_by_id(self, db: AsyncSession, user_id: int, order_id: str) -> Optional[Order]:
        """
        根据ID获取订单
        """
        query = select(Order).where(and_(Order.user_id == user_id, Order.order_id == order_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _cache_order(self, order: Order) -> None:
        """
        缓存订单信息
        """
        try:
            cache_key = f"order:{order.order_id}"
            order_data = {
                "id": order.id,
                "user_id": order.user_id,
                "order_id": order.order_id,
                "symbol": order.symbol,
                "status": order.status.value,
                "side": order.side.value,
                "quantity": str(order.quantity),
                "price": str(order.price) if order.price else None,
                "executed_quantity": str(order.executed_quantity),
                "remaining_quantity": str(order.remaining_quantity),
            }
            await self.redis_manager.set(cache_key, order_data, ttl=3600)
        except Exception as e:
            logger.warning(f"缓存订单失败: order_id={order.order_id}, error={str(e)}")
    
    async def _publish_order_event(self, order: Order, event_type: str) -> None:
        """
        发布订单事件
        """
        try:
            event_data = {
                "event_type": event_type,
                "order_id": order.order_id,
                "user_id": order.user_id,
                "symbol": order.symbol,
                "status": order.status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.redis_manager.publish_order_update(order.user_id, event_data)
        except Exception as e:
            logger.warning(f"发布订单事件失败: order_id={order.order_id}, error={str(e)}")
    
    def _generate_order_id(self) -> str:
        """
        生成订单ID
        """
        return f"ORD_{int(datetime.utcnow().timestamp() * 1000)}_{uuid.uuid4().hex[:8].upper()}"
    
    def _parse_symbol(self, symbol: str) -> tuple[str, str]:
        """
        解析交易对符号
        
        Args:
            symbol: 交易对符号，如 BTCUSDT
            
        Returns:
            tuple[str, str]: (基础资产, 计价资产)
        """
        # 简单的解析逻辑，实际应该根据交易所规则
        if symbol.endswith('USDT'):
            return symbol[:-4], 'USDT'
        elif symbol.endswith('BTC'):
            return symbol[:-3], 'BTC'
        elif symbol.endswith('ETH'):
            return symbol[:-3], 'ETH'
        else:
            # 默认假设最后3个字符是计价资产
            return symbol[:-3], symbol[-3:]
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """
        验证交易对是否有效
        """
        # 简单验证，实际应该查询支持的交易对列表
        return len(symbol) >= 6 and symbol.isalpha()
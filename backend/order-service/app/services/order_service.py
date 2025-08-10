#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务业务逻辑

处理订单的创建、更新、取消等核心业务逻辑
"""

import uuid
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from ..models.order import Order, OrderExecution, OrderStatus, OrderType, OrderSide
from ..schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    OrderCancelRequest, OrderStatusUpdate, OrderExecutionCreate,
    OrderStatistics, OrderFilter
)
from ..core.config import get_settings
from .exchange_client import ExchangeClient
from .notification_service import NotificationService

logger = logging.getLogger(__name__)
settings = get_settings()


class OrderService:
    """
    订单服务类
    
    处理订单的完整生命周期管理
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.exchange_client = ExchangeClient()
        self.notification_service = NotificationService()
    
    async def create_order(self, user_id: uuid.UUID, order_data: OrderCreate) -> OrderResponse:
        """
        创建新订单
        
        Args:
            user_id: 用户ID
            order_data: 订单创建数据
            
        Returns:
            OrderResponse: 创建的订单信息
            
        Raises:
            ValueError: 订单数据验证失败
            Exception: 创建订单失败
        """
        try:
            # 解析交易对
            base_asset, quote_asset = self._parse_symbol(order_data.symbol)
            
            # 创建订单对象
            order = Order(
                user_id=user_id,
                exchange_name=order_data.exchange_name,
                client_order_id=order_data.client_order_id,
                symbol=order_data.symbol,
                base_asset=base_asset,
                quote_asset=quote_asset,
                side=order_data.side,
                type=order_data.type,
                time_in_force=order_data.time_in_force,
                quantity=order_data.quantity,
                price=order_data.price,
                stop_price=order_data.stop_price,
                remaining_quantity=order_data.quantity,
                strategy_id=order_data.strategy_id,
                strategy_name=order_data.strategy_name,
                notes=order_data.notes,
                expires_at=order_data.expires_at,
                status=OrderStatus.PENDING
            )
            
            # 保存到数据库
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(f"Order created: {order.id} for user {user_id}")
            
            # 异步提交到交易所
            await self._submit_order_to_exchange(order)
            
            # 发送通知
            await self.notification_service.send_order_notification(
                user_id=user_id,
                order_id=order.id,
                event_type="order_created",
                message=f"Order {order.id} created successfully"
            )
            
            return await self._order_to_response(order)
            
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> Optional[OrderResponse]:
        """
        获取订单详情
        
        Args:
            user_id: 用户ID
            order_id: 订单ID
            
        Returns:
            Optional[OrderResponse]: 订单信息
        """
        try:
            stmt = select(Order).options(
                selectinload(Order.executions)
            ).where(
                and_(Order.id == order_id, Order.user_id == user_id)
            )
            
            result = await self.db.execute(stmt)
            order = result.scalar_one_or_none()
            
            if not order:
                return None
            
            return await self._order_to_response(order)
            
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {str(e)}")
            raise
    
    async def list_orders(
        self,
        user_id: uuid.UUID,
        filter_params: Optional[OrderFilter] = None,
        page: int = 1,
        size: int = 20
    ) -> OrderListResponse:
        """
        获取订单列表
        
        Args:
            user_id: 用户ID
            filter_params: 过滤条件
            page: 页码
            size: 每页大小
            
        Returns:
            OrderListResponse: 订单列表响应
        """
        try:
            # 构建查询条件
            conditions = [Order.user_id == user_id]
            
            if filter_params:
                if filter_params.exchange_name:
                    conditions.append(Order.exchange_name == filter_params.exchange_name)
                if filter_params.symbol:
                    conditions.append(Order.symbol == filter_params.symbol)
                if filter_params.side:
                    conditions.append(Order.side == filter_params.side)
                if filter_params.type:
                    conditions.append(Order.type == filter_params.type)
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
            
            # 计算总数
            count_stmt = select(func.count(Order.id)).where(and_(*conditions))
            total_result = await self.db.execute(count_stmt)
            total = total_result.scalar()
            
            # 分页查询
            offset = (page - 1) * size
            stmt = select(Order).options(
                selectinload(Order.executions)
            ).where(
                and_(*conditions)
            ).order_by(
                desc(Order.created_at)
            ).offset(offset).limit(size)
            
            result = await self.db.execute(stmt)
            orders = result.scalars().all()
            
            # 转换为响应格式
            order_responses = []
            for order in orders:
                order_response = await self._order_to_response(order)
                order_responses.append(order_response)
            
            pages = (total + size - 1) // size
            
            return OrderListResponse(
                orders=order_responses,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list orders for user {user_id}: {str(e)}")
            raise
    
    async def cancel_order(
        self,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
        cancel_request: Optional[OrderCancelRequest] = None
    ) -> OrderResponse:
        """
        取消订单
        
        Args:
            user_id: 用户ID
            order_id: 订单ID
            cancel_request: 取消请求
            
        Returns:
            OrderResponse: 更新后的订单信息
            
        Raises:
            ValueError: 订单不存在或无法取消
            Exception: 取消订单失败
        """
        try:
            # 获取订单
            stmt = select(Order).where(
                and_(Order.id == order_id, Order.user_id == user_id)
            )
            result = await self.db.execute(stmt)
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            if not order.is_active:
                raise ValueError(f"Order {order_id} is not active and cannot be cancelled")
            
            # 尝试在交易所取消订单
            if order.exchange_order_id:
                try:
                    await self.exchange_client.cancel_order(
                        exchange_name=order.exchange_name,
                        order_id=order.exchange_order_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to cancel order on exchange: {str(e)}")
            
            # 更新订单状态
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.utcnow()
            if cancel_request and cancel_request.reason:
                order.notes = f"{order.notes or ''} Cancelled: {cancel_request.reason}".strip()
            
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(f"Order cancelled: {order.id}")
            
            # 发送通知
            await self.notification_service.send_order_notification(
                user_id=user_id,
                order_id=order.id,
                event_type="order_cancelled",
                message=f"Order {order.id} cancelled successfully"
            )
            
            return await self._order_to_response(order)
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            await self.db.rollback()
            raise
    
    async def update_order_status(self, status_update: OrderStatusUpdate) -> Optional[OrderResponse]:
        """
        更新订单状态（通常由交易所回调触发）
        
        Args:
            status_update: 状态更新数据
            
        Returns:
            Optional[OrderResponse]: 更新后的订单信息
        """
        try:
            # 获取订单
            stmt = select(Order).where(Order.id == status_update.order_id)
            result = await self.db.execute(stmt)
            order = result.scalar_one_or_none()
            
            if not order:
                logger.warning(f"Order {status_update.order_id} not found for status update")
                return None
            
            # 更新订单信息
            order.status = status_update.status
            order.updated_at = status_update.updated_at
            
            if status_update.exchange_order_id:
                order.exchange_order_id = status_update.exchange_order_id
            
            if status_update.filled_quantity is not None:
                order.filled_quantity = status_update.filled_quantity
                order.remaining_quantity = order.quantity - order.filled_quantity
            
            if status_update.remaining_quantity is not None:
                order.remaining_quantity = status_update.remaining_quantity
            
            if status_update.avg_price is not None:
                order.avg_price = status_update.avg_price
            
            if status_update.total_value is not None:
                order.total_value = status_update.total_value
            
            if status_update.fee is not None:
                order.fee = status_update.fee
            
            if status_update.fee_asset:
                order.fee_asset = status_update.fee_asset
            
            if status_update.error_message:
                order.error_message = status_update.error_message
            
            # 设置完成时间
            if order.status == OrderStatus.FILLED and not order.filled_at:
                order.filled_at = datetime.utcnow()
            elif order.status == OrderStatus.SUBMITTED and not order.submitted_at:
                order.submitted_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(f"Order status updated: {order.id} -> {order.status}")
            
            # 发送通知
            await self.notification_service.send_order_notification(
                user_id=order.user_id,
                order_id=order.id,
                event_type="order_updated",
                message=f"Order {order.id} status updated to {order.status}"
            )
            
            return await self._order_to_response(order)
            
        except Exception as e:
            logger.error(f"Failed to update order status: {str(e)}")
            await self.db.rollback()
            raise
    
    async def add_execution(self, execution_data: OrderExecutionCreate) -> OrderResponse:
        """
        添加订单执行记录
        
        Args:
            execution_data: 执行记录数据
            
        Returns:
            OrderResponse: 更新后的订单信息
        """
        try:
            # 获取订单
            stmt = select(Order).where(Order.id == execution_data.order_id)
            result = await self.db.execute(stmt)
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"Order {execution_data.order_id} not found")
            
            # 创建执行记录
            execution = OrderExecution(
                order_id=execution_data.order_id,
                exchange_execution_id=execution_data.exchange_execution_id,
                price=execution_data.price,
                quantity=execution_data.quantity,
                value=execution_data.value,
                fee=execution_data.fee,
                fee_asset=execution_data.fee_asset,
                executed_at=execution_data.executed_at
            )
            
            self.db.add(execution)
            
            # 更新订单成交信息
            order.filled_quantity += execution_data.quantity
            order.remaining_quantity = order.quantity - order.filled_quantity
            
            # 计算平均价格
            if order.total_value:
                order.total_value += execution_data.value
            else:
                order.total_value = execution_data.value
            
            order.avg_price = order.total_value / order.filled_quantity
            
            # 累计手续费
            if execution_data.fee:
                if order.fee:
                    order.fee += execution_data.fee
                else:
                    order.fee = execution_data.fee
                    order.fee_asset = execution_data.fee_asset
            
            # 更新订单状态
            if order.remaining_quantity <= 0:
                order.status = OrderStatus.FILLED
                order.filled_at = datetime.utcnow()
            elif order.filled_quantity > 0:
                order.status = OrderStatus.PARTIAL_FILLED
            
            order.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(f"Execution added to order {order.id}: {execution_data.quantity} @ {execution_data.price}")
            
            return await self._order_to_response(order)
            
        except Exception as e:
            logger.error(f"Failed to add execution: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_order_statistics(self, user_id: uuid.UUID) -> OrderStatistics:
        """
        获取用户订单统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            OrderStatistics: 统计信息
        """
        try:
            # 基础统计
            total_stmt = select(func.count(Order.id)).where(Order.user_id == user_id)
            total_result = await self.db.execute(total_stmt)
            total_orders = total_result.scalar() or 0
            
            # 按状态统计
            active_stmt = select(func.count(Order.id)).where(
                and_(
                    Order.user_id == user_id,
                    Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED])
                )
            )
            active_result = await self.db.execute(active_stmt)
            active_orders = active_result.scalar() or 0
            
            completed_stmt = select(func.count(Order.id)).where(
                and_(Order.user_id == user_id, Order.status == OrderStatus.FILLED)
            )
            completed_result = await self.db.execute(completed_stmt)
            completed_orders = completed_result.scalar() or 0
            
            cancelled_stmt = select(func.count(Order.id)).where(
                and_(Order.user_id == user_id, Order.status == OrderStatus.CANCELLED)
            )
            cancelled_result = await self.db.execute(cancelled_stmt)
            cancelled_orders = cancelled_result.scalar() or 0
            
            failed_stmt = select(func.count(Order.id)).where(
                and_(
                    Order.user_id == user_id,
                    Order.status.in_([OrderStatus.REJECTED, OrderStatus.FAILED, OrderStatus.EXPIRED])
                )
            )
            failed_result = await self.db.execute(failed_stmt)
            failed_orders = failed_result.scalar() or 0
            
            # 交易量统计
            volume_stmt = select(func.sum(Order.filled_quantity)).where(
                and_(Order.user_id == user_id, Order.status == OrderStatus.FILLED)
            )
            volume_result = await self.db.execute(volume_stmt)
            total_volume = volume_result.scalar() or Decimal('0')
            
            value_stmt = select(func.sum(Order.total_value)).where(
                and_(Order.user_id == user_id, Order.status == OrderStatus.FILLED)
            )
            value_result = await self.db.execute(value_stmt)
            total_value = value_result.scalar() or Decimal('0')
            
            # 计算成功率和平均成交率
            success_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0.0
            
            fill_rate_stmt = select(func.avg(Order.filled_quantity / Order.quantity * 100)).where(
                and_(Order.user_id == user_id, Order.filled_quantity > 0)
            )
            fill_rate_result = await self.db.execute(fill_rate_stmt)
            avg_fill_rate = float(fill_rate_result.scalar() or 0.0)
            
            return OrderStatistics(
                total_orders=total_orders,
                active_orders=active_orders,
                completed_orders=completed_orders,
                cancelled_orders=cancelled_orders,
                failed_orders=failed_orders,
                total_volume=total_volume,
                total_value=total_value,
                avg_fill_rate=avg_fill_rate,
                success_rate=success_rate
            )
            
        except Exception as e:
            logger.error(f"Failed to get order statistics for user {user_id}: {str(e)}")
            raise
    
    async def _submit_order_to_exchange(self, order: Order) -> None:
        """
        提交订单到交易所
        
        Args:
            order: 订单对象
        """
        try:
            # 准备订单数据
            order_data = {
                "symbol": order.symbol,
                "side": order.side.value,
                "type": order.type.value,
                "quantity": str(order.quantity),
                "time_in_force": order.time_in_force.value
            }
            
            if order.price:
                order_data["price"] = str(order.price)
            
            if order.stop_price:
                order_data["stop_price"] = str(order.stop_price)
            
            if order.client_order_id:
                order_data["client_order_id"] = order.client_order_id
            
            # 提交到交易所
            exchange_response = await self.exchange_client.create_order(
                exchange_name=order.exchange_name,
                order_data=order_data
            )
            
            # 更新订单信息
            order.exchange_order_id = exchange_response.get("order_id")
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Order submitted to exchange: {order.id} -> {order.exchange_order_id}")
            
        except Exception as e:
            logger.error(f"Failed to submit order to exchange: {str(e)}")
            # 更新订单状态为失败
            order.status = OrderStatus.FAILED
            order.error_message = str(e)
            order.updated_at = datetime.utcnow()
            await self.db.commit()
            raise
    
    def _parse_symbol(self, symbol: str) -> tuple[str, str]:
        """
        解析交易对符号
        
        Args:
            symbol: 交易对符号
            
        Returns:
            tuple[str, str]: (基础资产, 计价资产)
        """
        if "_" in symbol:
            parts = symbol.split("_")
            return parts[0], parts[1]
        elif "/" in symbol:
            parts = symbol.split("/")
            return parts[0], parts[1]
        else:
            # 默认处理方式，可能需要根据具体交易所调整
            if len(symbol) >= 6:
                return symbol[:3], symbol[3:]
            else:
                return symbol[:len(symbol)//2], symbol[len(symbol)//2:]
    
    async def _order_to_response(self, order: Order) -> OrderResponse:
        """
        将订单模型转换为响应格式
        
        Args:
            order: 订单模型
            
        Returns:
            OrderResponse: 订单响应
        """
        # 获取执行记录
        if not hasattr(order, 'executions') or order.executions is None:
            stmt = select(OrderExecution).where(OrderExecution.order_id == order.id)
            result = await self.db.execute(stmt)
            executions = result.scalars().all()
        else:
            executions = order.executions
        
        execution_responses = [
            {
                "id": execution.id,
                "order_id": execution.order_id,
                "exchange_execution_id": execution.exchange_execution_id,
                "price": execution.price,
                "quantity": execution.quantity,
                "value": execution.value,
                "fee": execution.fee,
                "fee_asset": execution.fee_asset,
                "executed_at": execution.executed_at,
                "created_at": execution.created_at
            }
            for execution in executions
        ]
        
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            exchange_name=order.exchange_name,
            exchange_order_id=order.exchange_order_id,
            client_order_id=order.client_order_id,
            symbol=order.symbol,
            base_asset=order.base_asset,
            quote_asset=order.quote_asset,
            side=order.side,
            type=order.type,
            status=order.status,
            time_in_force=order.time_in_force,
            quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
            filled_quantity=order.filled_quantity,
            remaining_quantity=order.remaining_quantity,
            avg_price=order.avg_price,
            total_value=order.total_value,
            fee=order.fee,
            fee_asset=order.fee_asset,
            created_at=order.created_at,
            updated_at=order.updated_at,
            submitted_at=order.submitted_at,
            filled_at=order.filled_at,
            expires_at=order.expires_at,
            strategy_id=order.strategy_id,
            strategy_name=order.strategy_name,
            notes=order.notes,
            error_message=order.error_message,
            is_active=order.is_active,
            is_completed=order.is_completed,
            fill_percentage=order.fill_percentage,
            executions=execution_responses
        )
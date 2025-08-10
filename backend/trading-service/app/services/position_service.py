#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 持仓服务

提供持仓管理相关的业务逻辑
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_

from app.models.position import Position, PositionSide, PositionType
from app.models.trade import Trade
from app.schemas.position import (
    PositionCreate, PositionUpdate, PositionFilter, PositionResponse,
    PositionListResponse, PositionSummary, PositionRisk,
    PositionStatistics, PositionCloseRequest, PositionCloseResponse
)
from app.core.redis import RedisManager

logger = logging.getLogger("position_service")


class PositionService:
    """
    持仓服务类
    
    提供持仓的创建、更新、查询、风险管理等功能
    """
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
    
    async def create_position(self, db: AsyncSession, user_id: int, position_data: PositionCreate) -> PositionResponse:
        """
        创建持仓记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            position_data: 持仓数据
            
        Returns:
            PositionResponse: 创建的持仓记录
            
        Raises:
            ValueError: 持仓记录已存在
        """
        try:
            # 检查持仓是否已存在
            existing_position = await self._get_position_by_symbol_type(db, user_id, position_data.symbol, position_data.position_type)
            if existing_position:
                raise ValueError(f"持仓记录已存在: {position_data.symbol} - {position_data.position_type}")
            
            # 创建持仓对象
            position = Position(
                user_id=user_id,
                symbol=position_data.symbol,
                base_asset=position_data.base_asset,
                quote_asset=position_data.quote_asset,
                position_side=position_data.position_side,
                position_type=position_data.position_type,
                quantity=position_data.quantity,
                available_quantity=position_data.available_quantity or position_data.quantity,
                frozen_quantity=position_data.frozen_quantity or Decimal('0'),
                avg_cost_price=position_data.avg_cost_price,
                last_price=position_data.last_price or position_data.avg_cost_price,
                mark_price=position_data.mark_price or position_data.avg_cost_price,
                strategy_id=position_data.strategy_id,
                strategy_name=position_data.strategy_name,
                leverage=position_data.leverage or Decimal('1'),
                margin_ratio=position_data.margin_ratio or Decimal('0'),
                liquidation_price=position_data.liquidation_price,
                stop_loss_price=position_data.stop_loss_price,
                take_profit_price=position_data.take_profit_price,
                last_update_time=datetime.utcnow(),
                notes=position_data.notes,
            )
            
            # 保存到数据库
            db.add(position)
            await db.commit()
            await db.refresh(position)
            
            # 缓存持仓信息
            await self._cache_position(position)
            
            # 发布持仓事件
            await self._publish_position_event(position, "position_created")
            
            logger.info(f"持仓创建成功: user_id={user_id}, symbol={position_data.symbol}")
            
            return PositionResponse.from_orm(position)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建持仓失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_position(self, db: AsyncSession, user_id: int, position_id: int) -> Optional[PositionResponse]:
        """
        获取持仓信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            position_id: 持仓ID
            
        Returns:
            Optional[PositionResponse]: 持仓信息
        """
        query = select(Position).where(
            and_(
                Position.id == position_id,
                Position.user_id == user_id
            )
        )
        result = await db.execute(query)
        position = result.scalar_one_or_none()
        
        if position:
            return PositionResponse.from_orm(position)
        return None
    
    async def get_position_by_symbol(self, db: AsyncSession, user_id: int, symbol: str, position_type: PositionType = PositionType.SPOT) -> Optional[PositionResponse]:
        """
        根据交易对获取持仓信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            symbol: 交易对
            position_type: 持仓类型
            
        Returns:
            Optional[PositionResponse]: 持仓信息
        """
        position = await self._get_position_by_symbol_type(db, user_id, symbol, position_type)
        if position:
            return PositionResponse.from_orm(position)
        return None
    
    async def list_positions(self, db: AsyncSession, user_id: int, filter_params: PositionFilter) -> PositionListResponse:
        """
        获取持仓列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            filter_params: 过滤参数
            
        Returns:
            PositionListResponse: 持仓列表
        """
        try:
            # 构建查询条件
            conditions = [Position.user_id == user_id]
            
            if filter_params.symbol:
                conditions.append(Position.symbol == filter_params.symbol)
            if filter_params.base_asset:
                conditions.append(Position.base_asset == filter_params.base_asset)
            if filter_params.quote_asset:
                conditions.append(Position.quote_asset == filter_params.quote_asset)
            if filter_params.position_side:
                conditions.append(Position.position_side == filter_params.position_side)
            if filter_params.position_type:
                conditions.append(Position.position_type == filter_params.position_type)
            if filter_params.strategy_id:
                conditions.append(Position.strategy_id == filter_params.strategy_id)
            if filter_params.strategy_name:
                conditions.append(Position.strategy_name == filter_params.strategy_name)
            if filter_params.is_active is not None:
                conditions.append(Position.is_active == filter_params.is_active)
            if filter_params.has_quantity is not None:
                if filter_params.has_quantity:
                    conditions.append(Position.quantity > 0)
                else:
                    conditions.append(Position.quantity == 0)
            if filter_params.min_quantity:
                conditions.append(Position.quantity >= filter_params.min_quantity)
            if filter_params.max_quantity:
                conditions.append(Position.quantity <= filter_params.max_quantity)
            if filter_params.min_value:
                conditions.append(Position.quantity * Position.last_price >= filter_params.min_value)
            if filter_params.max_value:
                conditions.append(Position.quantity * Position.last_price <= filter_params.max_value)
            if filter_params.min_pnl:
                conditions.append(Position.unrealized_pnl >= filter_params.min_pnl)
            if filter_params.max_pnl:
                conditions.append(Position.unrealized_pnl <= filter_params.max_pnl)
            if filter_params.profit_only:
                conditions.append(Position.unrealized_pnl > 0)
            if filter_params.loss_only:
                conditions.append(Position.unrealized_pnl < 0)
            
            # 查询总数
            count_query = select(func.count(Position.id)).where(and_(*conditions))
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # 查询持仓列表
            offset = (filter_params.page - 1) * filter_params.size
            query = (
                select(Position)
                .where(and_(*conditions))
                .order_by(desc(Position.quantity * Position.last_price), desc(Position.last_update_time))
                .offset(offset)
                .limit(filter_params.size)
            )
            
            result = await db.execute(query)
            positions = result.scalars().all()
            
            # 计算分页信息
            pages = (total + filter_params.size - 1) // filter_params.size
            
            return PositionListResponse(
                positions=[PositionResponse.from_orm(position) for position in positions],
                total=total,
                page=filter_params.page,
                size=filter_params.size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"获取持仓列表失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_position_summary(self, db: AsyncSession, user_id: int) -> PositionSummary:
        """
        获取持仓摘要
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            PositionSummary: 持仓摘要
        """
        try:
            # 查询持仓统计
            query = (
                select(
                    func.count(Position.id).label('total_positions'),
                    func.count(Position.id).filter(Position.is_active == True).label('active_positions'),
                    func.count(Position.id).filter(Position.quantity > 0).label('non_zero_positions'),
                    func.sum(Position.quantity * Position.last_price).label('total_position_value'),
                    func.sum(Position.unrealized_pnl).label('total_unrealized_pnl'),
                    func.sum(Position.realized_pnl).label('total_realized_pnl'),
                    func.sum(Position.quantity * Position.last_price).filter(Position.position_type == PositionType.SPOT).label('spot_value'),
                    func.sum(Position.quantity * Position.last_price).filter(Position.position_type == PositionType.MARGIN).label('margin_value'),
                    func.sum(Position.quantity * Position.last_price).filter(Position.position_type == PositionType.FUTURES).label('futures_value'),
                    func.count(Position.id).filter(Position.unrealized_pnl > 0).label('profitable_positions'),
                    func.count(Position.id).filter(Position.unrealized_pnl < 0).label('losing_positions'),
                    func.count(func.distinct(Position.symbol)).label('symbols_held'),
                    func.count(func.distinct(Position.strategy_id)).label('strategies_used'),
                )
                .where(Position.user_id == user_id)
            )
            
            result = await db.execute(query)
            stats = result.first()
            
            # 查询最大持仓
            largest_position_query = (
                select(Position.quantity * Position.last_price, Position.symbol)
                .where(Position.user_id == user_id)
                .order_by(desc(Position.quantity * Position.last_price))
                .limit(1)
            )
            largest_result = await db.execute(largest_position_query)
            largest = largest_result.first()
            
            # 计算盈亏比例
            total_pnl_percentage = Decimal('0')
            if stats.total_position_value and stats.total_position_value > 0:
                total_pnl_percentage = (stats.total_unrealized_pnl or Decimal('0')) / stats.total_position_value * 100
            
            # 计算胜率
            win_rate = Decimal('0')
            if stats.total_positions and stats.total_positions > 0:
                win_rate = Decimal(stats.profitable_positions or 0) / Decimal(stats.total_positions) * 100
            
            return PositionSummary(
                total_positions=stats.total_positions or 0,
                active_positions=stats.active_positions or 0,
                non_zero_positions=stats.non_zero_positions or 0,
                total_position_value=stats.total_position_value or Decimal('0'),
                total_unrealized_pnl=stats.total_unrealized_pnl or Decimal('0'),
                total_realized_pnl=stats.total_realized_pnl or Decimal('0'),
                total_pnl_percentage=total_pnl_percentage,
                spot_value=stats.spot_value or Decimal('0'),
                margin_value=stats.margin_value or Decimal('0'),
                futures_value=stats.futures_value or Decimal('0'),
                profitable_positions=stats.profitable_positions or 0,
                losing_positions=stats.losing_positions or 0,
                win_rate=win_rate,
                symbols_held=stats.symbols_held or 0,
                strategies_used=stats.strategies_used or 0,
                largest_position_value=largest[0] if largest else Decimal('0'),
                largest_position_symbol=largest[1] if largest else None
            )
            
        except Exception as e:
            logger.error(f"获取持仓摘要失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def update_position_from_trade(self, db: AsyncSession, user_id: int, trade: Trade) -> Optional[PositionResponse]:
        """
        根据交易更新持仓
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            trade: 交易记录
            
        Returns:
            Optional[PositionResponse]: 更新后的持仓
        """
        try:
            # 获取或创建持仓
            position = await self._get_position_by_symbol_type(db, user_id, trade.symbol, PositionType.SPOT)
            
            if not position:
                # 创建新持仓
                position_data = PositionCreate(
                    symbol=trade.symbol,
                    base_asset=trade.base_asset,
                    quote_asset=trade.quote_asset,
                    position_side=PositionSide.LONG if trade.side.value == 'BUY' else PositionSide.SHORT,
                    position_type=PositionType.SPOT,
                    quantity=trade.quantity if trade.side.value == 'BUY' else -trade.quantity,
                    avg_cost_price=trade.price,
                    last_price=trade.price
                )
                return await self.create_position(db, user_id, position_data)
            
            # 更新现有持仓
            position.add_trade(trade.quantity, trade.price, trade.side.value)
            position.last_update_time = datetime.utcnow()
            
            await db.commit()
            await db.refresh(position)
            
            # 更新缓存
            await self._cache_position(position)
            
            # 发布持仓事件
            await self._publish_position_event(position, "position_updated")
            
            logger.info(f"持仓更新成功: user_id={user_id}, symbol={trade.symbol}")
            
            return PositionResponse.from_orm(position)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新持仓失败: user_id={user_id}, trade_id={trade.id}, error={str(e)}")
            raise
    
    async def update_position_prices(self, db: AsyncSession, price_data: Dict[str, Dict[str, Decimal]]) -> None:
        """
        批量更新持仓价格
        
        Args:
            db: 数据库会话
            price_data: 价格数据，格式: {symbol: {"last_price": price, "mark_price": price}}
        """
        try:
            for symbol, prices in price_data.items():
                # 查询所有该交易对的持仓
                query = select(Position).where(
                    and_(
                        Position.symbol == symbol,
                        Position.is_active == True
                    )
                )
                result = await db.execute(query)
                positions = result.scalars().all()
                
                for position in positions:
                    position.update_market_data(
                        last_price=prices.get("last_price"),
                        mark_price=prices.get("mark_price")
                    )
                    
                    # 更新缓存
                    await self._cache_position(position)
                    
                    # 发布价格更新事件
                    await self._publish_position_event(position, "position_price_updated")
            
            await db.commit()
            logger.info(f"持仓价格更新成功: {len(price_data)} 个交易对")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新持仓价格失败: error={str(e)}")
            raise
    
    async def close_position(self, db: AsyncSession, user_id: int, close_request: PositionCloseRequest) -> PositionCloseResponse:
        """
        平仓
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            close_request: 平仓请求
            
        Returns:
            PositionCloseResponse: 平仓结果
        """
        try:
            position = await self._get_position_by_symbol_type(db, user_id, close_request.symbol, close_request.position_type)
            if not position:
                raise ValueError(f"持仓不存在: {close_request.symbol}")
            
            if position.quantity == 0:
                raise ValueError("持仓数量为零，无法平仓")
            
            # 计算平仓数量
            close_quantity = close_request.quantity or abs(position.quantity)
            if close_quantity > abs(position.quantity):
                close_quantity = abs(position.quantity)
            
            # 记录平仓前状态
            quantity_before = position.quantity
            value_before = position.position_value
            
            # 计算已实现盈亏
            close_price = close_request.price or position.last_price
            if position.is_long:
                realized_pnl = (close_price - position.avg_cost_price) * close_quantity
            else:
                realized_pnl = (position.avg_cost_price - close_price) * close_quantity
            
            # 更新持仓
            if position.is_long:
                position.quantity -= close_quantity
            else:
                position.quantity += close_quantity
            
            position.realized_pnl += realized_pnl
            position.last_update_time = datetime.utcnow()
            
            # 如果完全平仓，设置为非活跃
            if position.quantity == 0:
                position.is_active = False
                position.close_time = datetime.utcnow()
                position.close_price = close_price
            
            await db.commit()
            await db.refresh(position)
            
            # 更新缓存
            await self._cache_position(position)
            
            # 发布平仓事件
            await self._publish_position_event(position, "position_closed")
            
            close_id = f"CLOSE_{int(datetime.utcnow().timestamp() * 1000)}"
            
            logger.info(f"平仓成功: user_id={user_id}, symbol={close_request.symbol}, quantity={close_quantity}")
            
            return PositionCloseResponse(
                close_id=close_id,
                success=True,
                message="平仓成功",
                quantity_before=quantity_before,
                quantity_after=position.quantity,
                close_quantity=close_quantity,
                close_price=close_price,
                realized_pnl=realized_pnl,
                value_before=value_before,
                value_after=position.position_value,
                close_time=datetime.utcnow(),
                is_fully_closed=position.quantity == 0
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"平仓失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_position_risk(self, db: AsyncSession, user_id: int, position_id: int) -> PositionRisk:
        """
        获取持仓风险信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            position_id: 持仓ID
            
        Returns:
            PositionRisk: 持仓风险信息
        """
        try:
            position = await self.get_position(db, user_id, position_id)
            if not position:
                raise ValueError(f"持仓不存在: {position_id}")
            
            # 计算风险指标
            current_price = position.last_price
            entry_price = position.avg_cost_price
            quantity = abs(position.quantity)
            
            # 价格变动百分比
            price_change_percentage = Decimal('0')
            if entry_price > 0:
                price_change_percentage = (current_price - entry_price) / entry_price * 100
            
            # 未实现盈亏百分比
            unrealized_pnl_percentage = Decimal('0')
            position_value = quantity * entry_price
            if position_value > 0:
                unrealized_pnl_percentage = position.unrealized_pnl / position_value * 100
            
            # 风险等级评估
            risk_level = "LOW"
            if abs(unrealized_pnl_percentage) > 20:
                risk_level = "HIGH"
            elif abs(unrealized_pnl_percentage) > 10:
                risk_level = "MEDIUM"
            
            # 保证金使用率（期货）
            margin_usage_rate = Decimal('0')
            if position.position_type == PositionType.FUTURES and position.margin_ratio > 0:
                margin_usage_rate = position.margin_ratio * 100
            
            # 距离强平价格的百分比
            liquidation_distance_percentage = None
            if position.liquidation_price:
                liquidation_distance_percentage = abs(current_price - position.liquidation_price) / current_price * 100
            
            # 距离止损价格的百分比
            stop_loss_distance_percentage = None
            if position.stop_loss_price:
                stop_loss_distance_percentage = abs(current_price - position.stop_loss_price) / current_price * 100
            
            # 距离止盈价格的百分比
            take_profit_distance_percentage = None
            if position.take_profit_price:
                take_profit_distance_percentage = abs(position.take_profit_price - current_price) / current_price * 100
            
            return PositionRisk(
                position_id=position.id,
                symbol=position.symbol,
                current_price=current_price,
                entry_price=entry_price,
                quantity=quantity,
                position_value=position.position_value,
                unrealized_pnl=position.unrealized_pnl,
                unrealized_pnl_percentage=unrealized_pnl_percentage,
                price_change_percentage=price_change_percentage,
                risk_level=risk_level,
                margin_usage_rate=margin_usage_rate,
                liquidation_price=position.liquidation_price,
                liquidation_distance_percentage=liquidation_distance_percentage,
                stop_loss_price=position.stop_loss_price,
                stop_loss_distance_percentage=stop_loss_distance_percentage,
                take_profit_price=position.take_profit_price,
                take_profit_distance_percentage=take_profit_distance_percentage,
                leverage=position.leverage,
                position_type=position.position_type,
                last_update_time=position.last_update_time
            )
            
        except Exception as e:
            logger.error(f"获取持仓风险失败: user_id={user_id}, position_id={position_id}, error={str(e)}")
            raise
    
    # 私有方法
    
    async def _get_position_by_symbol_type(self, db: AsyncSession, user_id: int, symbol: str, position_type: PositionType) -> Optional[Position]:
        """
        根据交易对和类型获取持仓记录
        """
        query = select(Position).where(
            and_(
                Position.user_id == user_id,
                Position.symbol == symbol,
                Position.position_type == position_type,
                Position.is_active == True
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _cache_position(self, position: Position) -> None:
        """
        缓存持仓信息
        """
        try:
            cache_key = f"position:{position.user_id}:{position.symbol}:{position.position_type.value}"
            position_data = {
                "id": position.id,
                "user_id": position.user_id,
                "symbol": position.symbol,
                "position_type": position.position_type.value,
                "quantity": str(position.quantity),
                "avg_cost_price": str(position.avg_cost_price),
                "last_price": str(position.last_price),
                "unrealized_pnl": str(position.unrealized_pnl),
                "position_value": str(position.position_value),
                "last_update_time": position.last_update_time.isoformat(),
            }
            await self.redis_manager.set(cache_key, position_data, ttl=300)
        except Exception as e:
            logger.warning(f"缓存持仓失败: position_id={position.id}, error={str(e)}")
    
    async def _publish_position_event(self, position: Position, event_type: str) -> None:
        """
        发布持仓事件
        """
        try:
            position_event = {
                "type": event_type,
                "user_id": position.user_id,
                "position_id": position.id,
                "symbol": position.symbol,
                "quantity": str(position.quantity),
                "avg_cost_price": str(position.avg_cost_price),
                "last_price": str(position.last_price),
                "unrealized_pnl": str(position.unrealized_pnl),
                "position_value": str(position.position_value),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 发布到用户频道
            await self.redis_manager.publish_user_position_update(position.user_id, position_event)
            
        except Exception as e:
            logger.warning(f"发布持仓事件失败: position_id={position.id}, error={str(e)}")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易记录服务

提供交易记录管理相关的业务逻辑
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, asc

from app.models.trade import Trade, TradeType
from app.models.order import Order
from app.schemas.trade import (
    TradeCreate, TradeFilter, TradeResponse,
    TradeListResponse, TradeSummary, TradeStatistics
)
from app.core.redis import RedisManager

logger = logging.getLogger("trade_service")


class TradeService:
    """
    交易记录服务类
    
    提供交易记录的创建、查询、统计等功能
    """
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
    
    async def create_trade(self, db: AsyncSession, user_id: int, trade_data: TradeCreate) -> TradeResponse:
        """
        创建交易记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            trade_data: 交易数据
            
        Returns:
            TradeResponse: 创建的交易记录
        """
        try:
            # 验证关联订单
            if trade_data.order_id:
                order_query = select(Order).where(
                    and_(
                        Order.id == trade_data.order_id,
                        Order.user_id == user_id
                    )
                )
                order_result = await db.execute(order_query)
                order = order_result.scalar_one_or_none()
                if not order:
                    raise ValueError(f"关联订单不存在: {trade_data.order_id}")
            
            # 创建交易对象
            trade = Trade(
                user_id=user_id,
                order_id=trade_data.order_id,
                trade_id=trade_data.trade_id,
                symbol=trade_data.symbol,
                base_asset=trade_data.base_asset,
                quote_asset=trade_data.quote_asset,
                trade_type=trade_data.trade_type,
                side=trade_data.side,
                quantity=trade_data.quantity,
                price=trade_data.price,
                fee=trade_data.fee,
                fee_asset=trade_data.fee_asset,
                trade_time=trade_data.trade_time or datetime.utcnow(),
                strategy_id=trade_data.strategy_id,
                strategy_name=trade_data.strategy_name,
                market_maker=trade_data.market_maker,
                liquidity_type=trade_data.liquidity_type,
                realized_pnl=trade_data.realized_pnl,
                unrealized_pnl=trade_data.unrealized_pnl,
                commission_rate=trade_data.commission_rate,
                notes=trade_data.notes,
            )
            
            # 保存到数据库
            db.add(trade)
            await db.commit()
            await db.refresh(trade)
            
            # 缓存交易信息
            await self._cache_trade(trade)
            
            # 发布交易事件
            await self._publish_trade_event(trade)
            
            logger.info(f"交易记录创建成功: user_id={user_id}, trade_id={trade.trade_id}")
            
            return TradeResponse.from_orm(trade)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建交易记录失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_trade(self, db: AsyncSession, user_id: int, trade_id: int) -> Optional[TradeResponse]:
        """
        获取交易记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            trade_id: 交易ID
            
        Returns:
            Optional[TradeResponse]: 交易记录
        """
        query = select(Trade).where(
            and_(
                Trade.id == trade_id,
                Trade.user_id == user_id
            )
        )
        result = await db.execute(query)
        trade = result.scalar_one_or_none()
        
        if trade:
            return TradeResponse.from_orm(trade)
        return None
    
    async def get_trade_by_trade_id(self, db: AsyncSession, user_id: int, trade_id: str) -> Optional[TradeResponse]:
        """
        根据交易ID获取交易记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            trade_id: 外部交易ID
            
        Returns:
            Optional[TradeResponse]: 交易记录
        """
        query = select(Trade).where(
            and_(
                Trade.trade_id == trade_id,
                Trade.user_id == user_id
            )
        )
        result = await db.execute(query)
        trade = result.scalar_one_or_none()
        
        if trade:
            return TradeResponse.from_orm(trade)
        return None
    
    async def list_trades(self, db: AsyncSession, user_id: int, filter_params: TradeFilter) -> TradeListResponse:
        """
        获取交易记录列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            filter_params: 过滤参数
            
        Returns:
            TradeListResponse: 交易记录列表
        """
        try:
            # 构建查询条件
            conditions = [Trade.user_id == user_id]
            
            if filter_params.symbol:
                conditions.append(Trade.symbol == filter_params.symbol)
            if filter_params.base_asset:
                conditions.append(Trade.base_asset == filter_params.base_asset)
            if filter_params.quote_asset:
                conditions.append(Trade.quote_asset == filter_params.quote_asset)
            if filter_params.trade_type:
                conditions.append(Trade.trade_type == filter_params.trade_type)
            if filter_params.side:
                conditions.append(Trade.side == filter_params.side)
            if filter_params.order_id:
                conditions.append(Trade.order_id == filter_params.order_id)
            if filter_params.strategy_id:
                conditions.append(Trade.strategy_id == filter_params.strategy_id)
            if filter_params.strategy_name:
                conditions.append(Trade.strategy_name == filter_params.strategy_name)
            if filter_params.market_maker is not None:
                conditions.append(Trade.market_maker == filter_params.market_maker)
            if filter_params.liquidity_type:
                conditions.append(Trade.liquidity_type == filter_params.liquidity_type)
            if filter_params.min_quantity:
                conditions.append(Trade.quantity >= filter_params.min_quantity)
            if filter_params.max_quantity:
                conditions.append(Trade.quantity <= filter_params.max_quantity)
            if filter_params.min_price:
                conditions.append(Trade.price >= filter_params.min_price)
            if filter_params.max_price:
                conditions.append(Trade.price <= filter_params.max_price)
            if filter_params.min_value:
                conditions.append(Trade.quantity * Trade.price >= filter_params.min_value)
            if filter_params.max_value:
                conditions.append(Trade.quantity * Trade.price <= filter_params.max_value)
            if filter_params.start_time:
                conditions.append(Trade.trade_time >= filter_params.start_time)
            if filter_params.end_time:
                conditions.append(Trade.trade_time <= filter_params.end_time)
            
            # 查询总数
            count_query = select(func.count(Trade.id)).where(and_(*conditions))
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # 查询交易列表
            offset = (filter_params.page - 1) * filter_params.size
            
            # 排序
            order_by = desc(Trade.trade_time)
            if filter_params.sort_by:
                if filter_params.sort_by == "trade_time":
                    order_by = desc(Trade.trade_time) if filter_params.sort_desc else asc(Trade.trade_time)
                elif filter_params.sort_by == "quantity":
                    order_by = desc(Trade.quantity) if filter_params.sort_desc else asc(Trade.quantity)
                elif filter_params.sort_by == "price":
                    order_by = desc(Trade.price) if filter_params.sort_desc else asc(Trade.price)
                elif filter_params.sort_by == "value":
                    order_by = desc(Trade.quantity * Trade.price) if filter_params.sort_desc else asc(Trade.quantity * Trade.price)
            
            query = (
                select(Trade)
                .where(and_(*conditions))
                .order_by(order_by)
                .offset(offset)
                .limit(filter_params.size)
            )
            
            result = await db.execute(query)
            trades = result.scalars().all()
            
            # 计算分页信息
            pages = (total + filter_params.size - 1) // filter_params.size
            
            return TradeListResponse(
                trades=[TradeResponse.from_orm(trade) for trade in trades],
                total=total,
                page=filter_params.page,
                size=filter_params.size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"获取交易记录列表失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_trade_summary(self, db: AsyncSession, user_id: int, symbol: Optional[str] = None, days: int = 30) -> TradeSummary:
        """
        获取交易摘要
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            symbol: 交易对（可选）
            days: 统计天数
            
        Returns:
            TradeSummary: 交易摘要
        """
        try:
            # 时间范围
            start_time = datetime.utcnow() - timedelta(days=days)
            
            # 构建查询条件
            conditions = [
                Trade.user_id == user_id,
                Trade.trade_time >= start_time
            ]
            if symbol:
                conditions.append(Trade.symbol == symbol)
            
            # 查询交易统计
            query = (
                select(
                    func.count(Trade.id).label('total_trades'),
                    func.count(Trade.id).filter(Trade.side == 'BUY').label('buy_trades'),
                    func.count(Trade.id).filter(Trade.side == 'SELL').label('sell_trades'),
                    func.sum(Trade.quantity).label('total_quantity'),
                    func.sum(Trade.quantity * Trade.price).label('total_volume'),
                    func.sum(Trade.fee).label('total_fees'),
                    func.sum(Trade.realized_pnl).label('total_realized_pnl'),
                    func.avg(Trade.price).label('avg_price'),
                    func.min(Trade.price).label('min_price'),
                    func.max(Trade.price).label('max_price'),
                    func.count(func.distinct(Trade.symbol)).label('symbols_traded'),
                    func.count(func.distinct(Trade.strategy_id)).label('strategies_used'),
                )
                .where(and_(*conditions))
            )
            
            result = await db.execute(query)
            stats = result.first()
            
            # 查询最大交易
            largest_trade_query = (
                select(Trade.quantity * Trade.price, Trade.symbol)
                .where(and_(*conditions))
                .order_by(desc(Trade.quantity * Trade.price))
                .limit(1)
            )
            largest_result = await db.execute(largest_trade_query)
            largest = largest_result.first()
            
            # 查询最活跃交易对
            most_active_query = (
                select(Trade.symbol, func.count(Trade.id).label('trade_count'))
                .where(and_(*conditions))
                .group_by(Trade.symbol)
                .order_by(desc(func.count(Trade.id)))
                .limit(1)
            )
            most_active_result = await db.execute(most_active_query)
            most_active = most_active_result.first()
            
            # 计算胜率（基于已实现盈亏）
            win_rate = Decimal('0')
            if stats.total_trades and stats.total_trades > 0:
                win_query = (
                    select(func.count(Trade.id))
                    .where(and_(*conditions, Trade.realized_pnl > 0))
                )
                win_result = await db.execute(win_query)
                win_count = win_result.scalar() or 0
                win_rate = Decimal(win_count) / Decimal(stats.total_trades) * 100
            
            # 计算平均手续费率
            avg_fee_rate = Decimal('0')
            if stats.total_volume and stats.total_volume > 0:
                avg_fee_rate = (stats.total_fees or Decimal('0')) / stats.total_volume * 100
            
            return TradeSummary(
                period_days=days,
                total_trades=stats.total_trades or 0,
                buy_trades=stats.buy_trades or 0,
                sell_trades=stats.sell_trades or 0,
                total_quantity=stats.total_quantity or Decimal('0'),
                total_volume=stats.total_volume or Decimal('0'),
                total_fees=stats.total_fees or Decimal('0'),
                total_realized_pnl=stats.total_realized_pnl or Decimal('0'),
                avg_price=stats.avg_price or Decimal('0'),
                min_price=stats.min_price or Decimal('0'),
                max_price=stats.max_price or Decimal('0'),
                win_rate=win_rate,
                avg_fee_rate=avg_fee_rate,
                symbols_traded=stats.symbols_traded or 0,
                strategies_used=stats.strategies_used or 0,
                largest_trade_value=largest[0] if largest else Decimal('0'),
                largest_trade_symbol=largest[1] if largest else None,
                most_active_symbol=most_active[0] if most_active else None,
                most_active_symbol_trades=most_active[1] if most_active else 0
            )
            
        except Exception as e:
            logger.error(f"获取交易摘要失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_trade_statistics(self, db: AsyncSession, user_id: int, symbol: Optional[str] = None, days: int = 30) -> TradeStatistics:
        """
        获取交易统计
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            symbol: 交易对（可选）
            days: 统计天数
            
        Returns:
            TradeStatistics: 交易统计
        """
        try:
            # 时间范围
            start_time = datetime.utcnow() - timedelta(days=days)
            
            # 构建查询条件
            conditions = [
                Trade.user_id == user_id,
                Trade.trade_time >= start_time
            ]
            if symbol:
                conditions.append(Trade.symbol == symbol)
            
            # 按日期分组统计
            daily_stats_query = (
                select(
                    func.date(Trade.trade_time).label('trade_date'),
                    func.count(Trade.id).label('daily_trades'),
                    func.sum(Trade.quantity * Trade.price).label('daily_volume'),
                    func.sum(Trade.fee).label('daily_fees'),
                    func.sum(Trade.realized_pnl).label('daily_pnl'),
                )
                .where(and_(*conditions))
                .group_by(func.date(Trade.trade_time))
                .order_by(func.date(Trade.trade_time))
            )
            
            daily_result = await db.execute(daily_stats_query)
            daily_stats = daily_result.fetchall()
            
            # 按交易对分组统计
            symbol_stats_query = (
                select(
                    Trade.symbol,
                    func.count(Trade.id).label('trades'),
                    func.sum(Trade.quantity * Trade.price).label('volume'),
                    func.sum(Trade.fee).label('fees'),
                    func.sum(Trade.realized_pnl).label('pnl'),
                    func.avg(Trade.price).label('avg_price'),
                )
                .where(and_(*conditions))
                .group_by(Trade.symbol)
                .order_by(desc(func.sum(Trade.quantity * Trade.price)))
                .limit(10)
            )
            
            symbol_result = await db.execute(symbol_stats_query)
            symbol_stats = symbol_result.fetchall()
            
            # 按策略分组统计
            strategy_stats_query = (
                select(
                    Trade.strategy_name,
                    func.count(Trade.id).label('trades'),
                    func.sum(Trade.quantity * Trade.price).label('volume'),
                    func.sum(Trade.realized_pnl).label('pnl'),
                )
                .where(and_(*conditions, Trade.strategy_name.isnot(None)))
                .group_by(Trade.strategy_name)
                .order_by(desc(func.sum(Trade.realized_pnl)))
                .limit(10)
            )
            
            strategy_result = await db.execute(strategy_stats_query)
            strategy_stats = strategy_result.fetchall()
            
            # 按小时分组统计（活跃时间）
            hourly_stats_query = (
                select(
                    func.extract('hour', Trade.trade_time).label('hour'),
                    func.count(Trade.id).label('trades'),
                    func.sum(Trade.quantity * Trade.price).label('volume'),
                )
                .where(and_(*conditions))
                .group_by(func.extract('hour', Trade.trade_time))
                .order_by(func.extract('hour', Trade.trade_time))
            )
            
            hourly_result = await db.execute(hourly_stats_query)
            hourly_stats = hourly_result.fetchall()
            
            return TradeStatistics(
                period_days=days,
                daily_stats=[
                    {
                        "date": stat.trade_date.isoformat(),
                        "trades": stat.daily_trades,
                        "volume": float(stat.daily_volume or 0),
                        "fees": float(stat.daily_fees or 0),
                        "pnl": float(stat.daily_pnl or 0),
                    }
                    for stat in daily_stats
                ],
                symbol_stats=[
                    {
                        "symbol": stat.symbol,
                        "trades": stat.trades,
                        "volume": float(stat.volume or 0),
                        "fees": float(stat.fees or 0),
                        "pnl": float(stat.pnl or 0),
                        "avg_price": float(stat.avg_price or 0),
                    }
                    for stat in symbol_stats
                ],
                strategy_stats=[
                    {
                        "strategy": stat.strategy_name,
                        "trades": stat.trades,
                        "volume": float(stat.volume or 0),
                        "pnl": float(stat.pnl or 0),
                    }
                    for stat in strategy_stats
                ],
                hourly_stats=[
                    {
                        "hour": int(stat.hour),
                        "trades": stat.trades,
                        "volume": float(stat.volume or 0),
                    }
                    for stat in hourly_stats
                ]
            )
            
        except Exception as e:
            logger.error(f"获取交易统计失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_trades_by_order(self, db: AsyncSession, user_id: int, order_id: int) -> List[TradeResponse]:
        """
        获取订单相关的交易记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            order_id: 订单ID
            
        Returns:
            List[TradeResponse]: 交易记录列表
        """
        query = (
            select(Trade)
            .where(
                and_(
                    Trade.user_id == user_id,
                    Trade.order_id == order_id
                )
            )
            .order_by(Trade.trade_time)
        )
        
        result = await db.execute(query)
        trades = result.scalars().all()
        
        return [TradeResponse.from_orm(trade) for trade in trades]
    
    # 私有方法
    
    async def _cache_trade(self, trade: Trade) -> None:
        """
        缓存交易信息
        """
        try:
            cache_key = f"trade:{trade.user_id}:{trade.id}"
            trade_data = {
                "id": trade.id,
                "user_id": trade.user_id,
                "order_id": trade.order_id,
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "side": trade.side.value,
                "quantity": str(trade.quantity),
                "price": str(trade.price),
                "trade_time": trade.trade_time.isoformat(),
            }
            await self.redis_manager.set(cache_key, trade_data, ttl=3600)
        except Exception as e:
            logger.warning(f"缓存交易失败: trade_id={trade.id}, error={str(e)}")
    
    async def _publish_trade_event(self, trade: Trade) -> None:
        """
        发布交易事件
        """
        try:
            trade_event = {
                "type": "trade_executed",
                "user_id": trade.user_id,
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "side": trade.side.value,
                "quantity": str(trade.quantity),
                "price": str(trade.price),
                "value": str(trade.total_value),
                "fee": str(trade.fee),
                "trade_time": trade.trade_time.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 发布到用户频道
            await self.redis_manager.publish_user_trade_update(trade.user_id, trade_event)
            
            # 发布到全局交易频道
            await self.redis_manager.publish(
                f"trades:{trade.symbol}",
                trade_event
            )
            
        except Exception as e:
            logger.warning(f"发布交易事件失败: trade_id={trade.id}, error={str(e)}")
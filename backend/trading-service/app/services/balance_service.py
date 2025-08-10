#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 余额服务

提供账户余额管理相关的业务逻辑
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.balance import Balance, BalanceType
from app.schemas.balance import (
    BalanceCreate, BalanceUpdate, BalanceFilter, BalanceResponse,
    BalanceListResponse, BalanceSummary, BalanceOperation,
    BalanceOperationResponse, BalanceTransfer, BalanceTransferResponse
)
from app.core.redis import RedisManager

logger = logging.getLogger("balance_service")


class BalanceService:
    """
    余额服务类
    
    提供余额的创建、更新、查询、转账等功能
    """
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
    
    async def create_balance(self, db: AsyncSession, user_id: int, balance_data: BalanceCreate) -> BalanceResponse:
        """
        创建余额记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            balance_data: 余额数据
            
        Returns:
            BalanceResponse: 创建的余额记录
            
        Raises:
            ValueError: 余额记录已存在
        """
        try:
            # 检查余额记录是否已存在
            existing_balance = await self._get_balance_by_asset_type(db, user_id, balance_data.asset, balance_data.balance_type)
            if existing_balance:
                raise ValueError(f"余额记录已存在: {balance_data.asset} - {balance_data.balance_type}")
            
            # 创建余额对象
            balance = Balance(
                user_id=user_id,
                asset=balance_data.asset,
                asset_name=balance_data.asset_name,
                balance_type=balance_data.balance_type,
                total_balance=balance_data.total_balance,
                available_balance=balance_data.available_balance,
                frozen_balance=balance_data.frozen_balance,
                last_update_time=datetime.utcnow(),
                notes=balance_data.notes,
            )
            
            # 保存到数据库
            db.add(balance)
            await db.commit()
            await db.refresh(balance)
            
            # 缓存余额信息
            await self._cache_balance(balance)
            
            logger.info(f"余额创建成功: user_id={user_id}, asset={balance_data.asset}, type={balance_data.balance_type}")
            
            return BalanceResponse.from_orm(balance)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建余额失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_balance(self, db: AsyncSession, user_id: int, asset: str, balance_type: BalanceType = BalanceType.SPOT) -> Optional[BalanceResponse]:
        """
        获取余额信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            asset: 资产符号
            balance_type: 余额类型
            
        Returns:
            Optional[BalanceResponse]: 余额信息
        """
        balance = await self._get_balance_by_asset_type(db, user_id, asset, balance_type)
        if balance:
            return BalanceResponse.from_orm(balance)
        return None
    
    async def list_balances(self, db: AsyncSession, user_id: int, filter_params: BalanceFilter) -> BalanceListResponse:
        """
        获取余额列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            filter_params: 过滤参数
            
        Returns:
            BalanceListResponse: 余额列表
        """
        try:
            # 构建查询条件
            conditions = [Balance.user_id == user_id]
            
            if filter_params.asset:
                conditions.append(Balance.asset == filter_params.asset)
            if filter_params.balance_type:
                conditions.append(Balance.balance_type == filter_params.balance_type)
            if filter_params.is_active is not None:
                conditions.append(Balance.is_active == filter_params.is_active)
            if filter_params.is_locked is not None:
                conditions.append(Balance.is_locked == filter_params.is_locked)
            if filter_params.min_balance:
                conditions.append(Balance.total_balance >= filter_params.min_balance)
            if filter_params.max_balance:
                conditions.append(Balance.total_balance <= filter_params.max_balance)
            if filter_params.min_value:
                conditions.append(Balance.usd_value >= filter_params.min_value)
            if filter_params.max_value:
                conditions.append(Balance.usd_value <= filter_params.max_value)
            if filter_params.has_frozen is not None:
                if filter_params.has_frozen:
                    conditions.append(Balance.frozen_balance > 0)
                else:
                    conditions.append(Balance.frozen_balance == 0)
            
            # 查询总数
            count_query = select(func.count(Balance.id)).where(and_(*conditions))
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # 查询余额列表
            offset = (filter_params.page - 1) * filter_params.size
            query = (
                select(Balance)
                .where(and_(*conditions))
                .order_by(desc(Balance.usd_value), desc(Balance.total_balance))
                .offset(offset)
                .limit(filter_params.size)
            )
            
            result = await db.execute(query)
            balances = result.scalars().all()
            
            # 计算分页信息
            pages = (total + filter_params.size - 1) // filter_params.size
            
            return BalanceListResponse(
                balances=[BalanceResponse.from_orm(balance) for balance in balances],
                total=total,
                page=filter_params.page,
                size=filter_params.size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"获取余额列表失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def get_balance_summary(self, db: AsyncSession, user_id: int) -> BalanceSummary:
        """
        获取余额摘要
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            BalanceSummary: 余额摘要
        """
        try:
            # 查询余额统计
            query = (
                select(
                    func.count(Balance.id).label('total_assets'),
                    func.count(Balance.id).filter(Balance.is_active == True).label('active_assets'),
                    func.sum(Balance.usd_value).label('total_usd_value'),
                    func.sum(Balance.btc_value).label('total_btc_value'),
                    func.sum(Balance.usd_value).filter(Balance.balance_type == BalanceType.SPOT).label('spot_value'),
                    func.sum(Balance.usd_value).filter(Balance.balance_type == BalanceType.MARGIN).label('margin_value'),
                    func.sum(Balance.usd_value).filter(Balance.balance_type == BalanceType.FUTURES).label('futures_value'),
                    func.sum(Balance.usd_value).filter(Balance.balance_type == BalanceType.SAVINGS).label('savings_value'),
                    func.sum(Balance.frozen_balance * Balance.usd_value / Balance.total_balance).label('total_frozen_value'),
                    func.sum(Balance.available_balance * Balance.usd_value / Balance.total_balance).label('total_available_value'),
                    func.sum(Balance.balance_change_24h).label('daily_change_value'),
                    func.sum(Balance.accrued_interest).label('total_accrued_interest'),
                )
                .where(Balance.user_id == user_id)
            )
            
            result = await db.execute(query)
            stats = result.first()
            
            # 查询最大资产
            largest_asset_query = (
                select(Balance.asset, Balance.usd_value)
                .where(Balance.user_id == user_id)
                .order_by(desc(Balance.usd_value))
                .limit(1)
            )
            largest_result = await db.execute(largest_asset_query)
            largest = largest_result.first()
            
            # 计算日变化百分比
            daily_change_percentage = Decimal('0')
            if stats.total_usd_value and stats.total_usd_value > 0:
                daily_change_percentage = (stats.daily_change_value or Decimal('0')) / stats.total_usd_value * 100
            
            return BalanceSummary(
                total_assets=stats.total_assets or 0,
                active_assets=stats.active_assets or 0,
                total_usd_value=stats.total_usd_value or Decimal('0'),
                total_btc_value=stats.total_btc_value or Decimal('0'),
                spot_value=stats.spot_value or Decimal('0'),
                margin_value=stats.margin_value or Decimal('0'),
                futures_value=stats.futures_value or Decimal('0'),
                savings_value=stats.savings_value or Decimal('0'),
                total_frozen_value=stats.total_frozen_value or Decimal('0'),
                total_available_value=stats.total_available_value or Decimal('0'),
                daily_change_value=stats.daily_change_value or Decimal('0'),
                daily_change_percentage=daily_change_percentage,
                total_accrued_interest=stats.total_accrued_interest or Decimal('0'),
                largest_asset_value=largest.usd_value if largest else Decimal('0'),
                largest_asset=largest.asset if largest else None
            )
            
        except Exception as e:
            logger.error(f"获取余额摘要失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def freeze_balance(self, db: AsyncSession, user_id: int, asset: str, amount: Decimal, balance_type: BalanceType = BalanceType.SPOT) -> BalanceOperationResponse:
        """
        冻结余额
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            asset: 资产符号
            amount: 冻结金额
            balance_type: 余额类型
            
        Returns:
            BalanceOperationResponse: 操作结果
        """
        try:
            balance = await self._get_balance_by_asset_type(db, user_id, asset, balance_type)
            if not balance:
                raise ValueError(f"余额记录不存在: {asset} - {balance_type}")
            
            balance_before = balance.available_balance
            
            # 执行冻结操作
            success = balance.freeze_balance(amount)
            if not success:
                raise ValueError(f"冻结失败: 可用余额不足")
            
            await db.commit()
            await db.refresh(balance)
            
            # 更新缓存
            await self._cache_balance(balance)
            
            logger.info(f"余额冻结成功: user_id={user_id}, asset={asset}, amount={amount}")
            
            return BalanceOperationResponse(
                success=True,
                message="冻结成功",
                balance_before=balance_before,
                balance_after=balance.available_balance,
                operation_amount=amount,
                operation_time=datetime.utcnow()
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"冻结余额失败: user_id={user_id}, asset={asset}, error={str(e)}")
            raise
    
    async def unfreeze_balance(self, db: AsyncSession, user_id: int, asset: str, amount: Decimal, balance_type: BalanceType = BalanceType.SPOT) -> BalanceOperationResponse:
        """
        解冻余额
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            asset: 资产符号
            amount: 解冻金额
            balance_type: 余额类型
            
        Returns:
            BalanceOperationResponse: 操作结果
        """
        try:
            balance = await self._get_balance_by_asset_type(db, user_id, asset, balance_type)
            if not balance:
                raise ValueError(f"余额记录不存在: {asset} - {balance_type}")
            
            balance_before = balance.available_balance
            
            # 执行解冻操作
            success = balance.unfreeze_balance(amount)
            if not success:
                raise ValueError(f"解冻失败: 冻结余额不足")
            
            await db.commit()
            await db.refresh(balance)
            
            # 更新缓存
            await self._cache_balance(balance)
            
            logger.info(f"余额解冻成功: user_id={user_id}, asset={asset}, amount={amount}")
            
            return BalanceOperationResponse(
                success=True,
                message="解冻成功",
                balance_before=balance_before,
                balance_after=balance.available_balance,
                operation_amount=amount,
                operation_time=datetime.utcnow()
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"解冻余额失败: user_id={user_id}, asset={asset}, error={str(e)}")
            raise
    
    async def add_balance(self, db: AsyncSession, user_id: int, asset: str, amount: Decimal, balance_type: BalanceType = BalanceType.SPOT) -> BalanceOperationResponse:
        """
        增加余额
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            asset: 资产符号
            amount: 增加金额
            balance_type: 余额类型
            
        Returns:
            BalanceOperationResponse: 操作结果
        """
        try:
            balance = await self._get_balance_by_asset_type(db, user_id, asset, balance_type)
            if not balance:
                # 如果余额记录不存在，创建新记录
                balance_data = BalanceCreate(
                    asset=asset,
                    balance_type=balance_type,
                    total_balance=amount,
                    available_balance=amount,
                    frozen_balance=Decimal('0')
                )
                return await self.create_balance(db, user_id, balance_data)
            
            balance_before = balance.total_balance
            
            # 执行增加操作
            balance.add_balance(amount, update_available=True)
            
            await db.commit()
            await db.refresh(balance)
            
            # 更新缓存
            await self._cache_balance(balance)
            
            logger.info(f"余额增加成功: user_id={user_id}, asset={asset}, amount={amount}")
            
            return BalanceOperationResponse(
                success=True,
                message="增加成功",
                balance_before=balance_before,
                balance_after=balance.total_balance,
                operation_amount=amount,
                operation_time=datetime.utcnow()
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"增加余额失败: user_id={user_id}, asset={asset}, error={str(e)}")
            raise
    
    async def subtract_balance(self, db: AsyncSession, user_id: int, asset: str, amount: Decimal, from_available: bool = True, balance_type: BalanceType = BalanceType.SPOT) -> BalanceOperationResponse:
        """
        减少余额
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            asset: 资产符号
            amount: 减少金额
            from_available: 是否从可用余额中扣除
            balance_type: 余额类型
            
        Returns:
            BalanceOperationResponse: 操作结果
        """
        try:
            balance = await self._get_balance_by_asset_type(db, user_id, asset, balance_type)
            if not balance:
                raise ValueError(f"余额记录不存在: {asset} - {balance_type}")
            
            balance_before = balance.total_balance
            
            # 执行减少操作
            success = balance.subtract_balance(amount, from_available=from_available)
            if not success:
                raise ValueError(f"减少失败: 余额不足")
            
            await db.commit()
            await db.refresh(balance)
            
            # 更新缓存
            await self._cache_balance(balance)
            
            logger.info(f"余额减少成功: user_id={user_id}, asset={asset}, amount={amount}")
            
            return BalanceOperationResponse(
                success=True,
                message="减少成功",
                balance_before=balance_before,
                balance_after=balance.total_balance,
                operation_amount=amount,
                operation_time=datetime.utcnow()
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"减少余额失败: user_id={user_id}, asset={asset}, error={str(e)}")
            raise
    
    async def transfer_balance(self, db: AsyncSession, user_id: int, transfer_data: BalanceTransfer) -> BalanceTransferResponse:
        """
        余额转账
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            transfer_data: 转账数据
            
        Returns:
            BalanceTransferResponse: 转账结果
        """
        try:
            # 获取源余额和目标余额
            from_balance = await self._get_balance_by_asset_type(db, user_id, transfer_data.asset, transfer_data.from_balance_type)
            to_balance = await self._get_balance_by_asset_type(db, user_id, transfer_data.asset, transfer_data.to_balance_type)
            
            if not from_balance:
                raise ValueError(f"源余额记录不存在: {transfer_data.asset} - {transfer_data.from_balance_type}")
            
            # 记录转账前余额
            from_balance_before = from_balance.available_balance
            to_balance_before = to_balance.available_balance if to_balance else Decimal('0')
            
            # 从源余额扣除
            success = from_balance.subtract_balance(transfer_data.amount, from_available=True)
            if not success:
                raise ValueError("转账失败: 源余额不足")
            
            # 如果目标余额不存在，创建新记录
            if not to_balance:
                to_balance = Balance(
                    user_id=user_id,
                    asset=transfer_data.asset,
                    balance_type=transfer_data.to_balance_type,
                    total_balance=transfer_data.amount,
                    available_balance=transfer_data.amount,
                    frozen_balance=Decimal('0'),
                    last_update_time=datetime.utcnow(),
                    notes=transfer_data.notes,
                )
                db.add(to_balance)
            else:
                # 向目标余额增加
                to_balance.add_balance(transfer_data.amount, update_available=True)
            
            await db.commit()
            await db.refresh(from_balance)
            if to_balance.id:
                await db.refresh(to_balance)
            
            # 更新缓存
            await self._cache_balance(from_balance)
            await self._cache_balance(to_balance)
            
            transfer_id = f"TXN_{int(datetime.utcnow().timestamp() * 1000)}"
            
            logger.info(f"余额转账成功: user_id={user_id}, asset={transfer_data.asset}, amount={transfer_data.amount}")
            
            return BalanceTransferResponse(
                transfer_id=transfer_id,
                success=True,
                message="转账成功",
                from_balance_before=from_balance_before,
                from_balance_after=from_balance.available_balance,
                to_balance_before=to_balance_before,
                to_balance_after=to_balance.available_balance,
                transfer_amount=transfer_data.amount,
                transfer_time=datetime.utcnow()
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"余额转账失败: user_id={user_id}, error={str(e)}")
            raise
    
    async def update_market_values(self, db: AsyncSession, price_data: Dict[str, Dict[str, Decimal]]) -> None:
        """
        批量更新市场价值
        
        Args:
            db: 数据库会话
            price_data: 价格数据，格式: {asset: {"usd": price, "btc": price}}
        """
        try:
            for asset, prices in price_data.items():
                # 查询所有该资产的余额记录
                query = select(Balance).where(Balance.asset == asset)
                result = await db.execute(query)
                balances = result.scalars().all()
                
                for balance in balances:
                    balance.update_market_value(
                        usd_price=prices.get("usd"),
                        btc_price=prices.get("btc")
                    )
                    
                    # 更新缓存
                    await self._cache_balance(balance)
            
            await db.commit()
            logger.info(f"市场价值更新成功: {len(price_data)} 个资产")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新市场价值失败: error={str(e)}")
            raise
    
    # 私有方法
    
    async def _get_balance_by_asset_type(self, db: AsyncSession, user_id: int, asset: str, balance_type: BalanceType) -> Optional[Balance]:
        """
        根据资产和类型获取余额记录
        """
        query = select(Balance).where(
            and_(
                Balance.user_id == user_id,
                Balance.asset == asset,
                Balance.balance_type == balance_type
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _cache_balance(self, balance: Balance) -> None:
        """
        缓存余额信息
        """
        try:
            cache_key = f"balance:{balance.user_id}:{balance.asset}:{balance.balance_type.value}"
            balance_data = {
                "id": balance.id,
                "user_id": balance.user_id,
                "asset": balance.asset,
                "balance_type": balance.balance_type.value,
                "total_balance": str(balance.total_balance),
                "available_balance": str(balance.available_balance),
                "frozen_balance": str(balance.frozen_balance),
                "usd_value": str(balance.usd_value) if balance.usd_value else None,
                "last_update_time": balance.last_update_time.isoformat(),
            }
            await self.redis_manager.set(cache_key, balance_data, ttl=300)
        except Exception as e:
            logger.warning(f"缓存余额失败: balance_id={balance.id}, error={str(e)}")
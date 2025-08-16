#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测服务业务逻辑

提供策略回测的核心功能，包括回测任务创建、执行、
结果分析和性能计算等功能。
"""

import asyncio
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
import logging
import json
import time
from concurrent.futures import ThreadPoolExecutor

from ..models.strategy import Strategy, Backtest, BacktestStatus
from ..schemas.strategy import (
    BacktestCreate, BacktestResponse, BacktestDetailResponse,
    BacktestListResponse, BacktestQueryParams
)
from ..core.cache import get_strategy_cache
from ..core.config import settings

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    回测引擎
    
    负责执行策略回测，计算性能指标和生成报告
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.backtest_max_concurrent)
    
    def run_backtest(self, strategy: Strategy, backtest: Backtest) -> Dict[str, Any]:
        """
        执行回测
        
        Args:
            strategy: 策略实例
            backtest: 回测实例
            
        Returns:
            Dict[str, Any]: 回测结果
        """
        try:
            start_time = time.time()
            
            # 获取历史数据
            market_data = self._get_market_data(
                strategy.symbols,
                backtest.start_date,
                backtest.end_date,
                strategy.timeframe
            )
            
            if market_data.empty:
                raise ValueError("无法获取市场数据")
            
            # 初始化回测环境
            portfolio = self._initialize_portfolio(backtest.initial_capital)
            trades = []
            equity_curve = []
            
            # 执行策略逻辑
            for i, (timestamp, data) in enumerate(market_data.iterrows()):
                # 更新组合状态
                portfolio = self._update_portfolio(portfolio, data, backtest.commission)
                
                # 执行策略信号
                signals = self._execute_strategy_logic(strategy, data, portfolio)
                
                # 处理交易信号
                new_trades = self._process_signals(
                    signals, data, portfolio, timestamp, 
                    backtest.commission, backtest.slippage
                )
                trades.extend(new_trades)
                
                # 记录资金曲线
                equity_curve.append({
                    "timestamp": timestamp.isoformat(),
                    "portfolio_value": portfolio["total_value"],
                    "cash": portfolio["cash"],
                    "positions_value": portfolio["positions_value"]
                })
            
            # 计算性能指标
            performance_metrics = self._calculate_performance_metrics(
                trades, equity_curve, backtest.initial_capital
            )
            
            execution_time = time.time() - start_time
            
            return {
                "status": "completed",
                "execution_time": execution_time,
                "trades_data": trades,
                "equity_curve": equity_curve,
                "performance_metrics": performance_metrics,
                "final_capital": portfolio["total_value"]
            }
            
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            return {
                "status": "failed",
                "error_message": str(e)
            }
    
    def _get_market_data(self, symbols: List[str], start_date: datetime, 
                        end_date: datetime, timeframe: str) -> pd.DataFrame:
        """
        获取市场数据
        
        Args:
            symbols: 交易标的列表
            start_date: 开始日期
            end_date: 结束日期
            timeframe: 时间周期
            
        Returns:
            pd.DataFrame: 市场数据
        """
        # 这里应该调用市场数据服务获取真实数据
        # 为了演示，生成模拟数据
        date_range = pd.date_range(start=start_date, end=end_date, freq='H')
        
        data = []
        for timestamp in date_range:
            # 生成模拟价格数据
            base_price = 100
            price = base_price + np.random.normal(0, 5)
            
            data.append({
                "timestamp": timestamp,
                "symbol": symbols[0] if symbols else "BTC_USDT",
                "open": price,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price,
                "volume": np.random.uniform(1000, 10000)
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def _initialize_portfolio(self, initial_capital: float) -> Dict[str, Any]:
        """
        初始化投资组合
        
        Args:
            initial_capital: 初始资金
            
        Returns:
            Dict[str, Any]: 投资组合状态
        """
        return {
            "cash": initial_capital,
            "positions": {},
            "total_value": initial_capital,
            "positions_value": 0.0
        }
    
    def _update_portfolio(self, portfolio: Dict[str, Any], 
                         market_data: pd.Series, commission: float) -> Dict[str, Any]:
        """
        更新投资组合状态
        
        Args:
            portfolio: 当前投资组合
            market_data: 市场数据
            commission: 手续费率
            
        Returns:
            Dict[str, Any]: 更新后的投资组合
        """
        # 更新持仓价值
        positions_value = 0.0
        for symbol, position in portfolio["positions"].items():
            if symbol == market_data["symbol"]:
                current_price = market_data["close"]
                position["current_price"] = current_price
                position["market_value"] = position["quantity"] * current_price
                positions_value += position["market_value"]
        
        portfolio["positions_value"] = positions_value
        portfolio["total_value"] = portfolio["cash"] + positions_value
        
        return portfolio
    
    def _execute_strategy_logic(self, strategy: Strategy, market_data: pd.Series, 
                               portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行策略逻辑
        
        Args:
            strategy: 策略实例
            market_data: 市场数据
            portfolio: 投资组合
            
        Returns:
            List[Dict[str, Any]]: 交易信号列表
        """
        signals = []
        
        # 简单的移动平均策略示例
        # 实际应该执行用户定义的策略代码
        try:
            # 这里应该解析和执行strategy.code
            # 为了演示，使用简单的随机信号
            if np.random.random() > 0.95:  # 5%概率产生信号
                signal_type = "buy" if np.random.random() > 0.5 else "sell"
                signals.append({
                    "type": signal_type,
                    "symbol": market_data["symbol"],
                    "quantity": 1.0,
                    "price": market_data["close"]
                })
        except Exception as e:
            logger.warning(f"策略逻辑执行失败: {e}")
        
        return signals
    
    def _process_signals(self, signals: List[Dict[str, Any]], market_data: pd.Series,
                        portfolio: Dict[str, Any], timestamp: datetime,
                        commission: float, slippage: float) -> List[Dict[str, Any]]:
        """
        处理交易信号
        
        Args:
            signals: 交易信号列表
            market_data: 市场数据
            portfolio: 投资组合
            timestamp: 时间戳
            commission: 手续费率
            slippage: 滑点
            
        Returns:
            List[Dict[str, Any]]: 执行的交易列表
        """
        trades = []
        
        for signal in signals:
            try:
                symbol = signal["symbol"]
                signal_type = signal["type"]
                quantity = signal["quantity"]
                price = signal["price"] * (1 + slippage if signal_type == "buy" else 1 - slippage)
                
                # 计算交易成本
                trade_value = quantity * price
                commission_cost = trade_value * commission
                
                if signal_type == "buy":
                    # 检查资金是否充足
                    total_cost = trade_value + commission_cost
                    if portfolio["cash"] >= total_cost:
                        # 执行买入
                        portfolio["cash"] -= total_cost
                        
                        if symbol not in portfolio["positions"]:
                            portfolio["positions"][symbol] = {
                                "quantity": 0,
                                "avg_price": 0,
                                "current_price": price,
                                "market_value": 0
                            }
                        
                        position = portfolio["positions"][symbol]
                        old_quantity = position["quantity"]
                        old_value = old_quantity * position["avg_price"]
                        new_quantity = old_quantity + quantity
                        new_value = old_value + trade_value
                        
                        position["quantity"] = new_quantity
                        position["avg_price"] = new_value / new_quantity
                        position["current_price"] = price
                        position["market_value"] = new_quantity * price
                        
                        trades.append({
                            "timestamp": timestamp.isoformat(),
                            "symbol": symbol,
                            "type": "buy",
                            "quantity": quantity,
                            "price": price,
                            "value": trade_value,
                            "commission": commission_cost
                        })
                
                elif signal_type == "sell":
                    # 检查持仓是否充足
                    if symbol in portfolio["positions"] and portfolio["positions"][symbol]["quantity"] >= quantity:
                        # 执行卖出
                        portfolio["cash"] += trade_value - commission_cost
                        
                        position = portfolio["positions"][symbol]
                        position["quantity"] -= quantity
                        position["market_value"] = position["quantity"] * price
                        
                        if position["quantity"] == 0:
                            del portfolio["positions"][symbol]
                        
                        trades.append({
                            "timestamp": timestamp.isoformat(),
                            "symbol": symbol,
                            "type": "sell",
                            "quantity": quantity,
                            "price": price,
                            "value": trade_value,
                            "commission": commission_cost
                        })
                
            except Exception as e:
                logger.warning(f"处理交易信号失败: {e}")
        
        return trades
    
    def _calculate_performance_metrics(self, trades: List[Dict[str, Any]], 
                                     equity_curve: List[Dict[str, Any]], 
                                     initial_capital: float) -> Dict[str, Any]:
        """
        计算性能指标
        
        Args:
            trades: 交易列表
            equity_curve: 资金曲线
            initial_capital: 初始资金
            
        Returns:
            Dict[str, Any]: 性能指标
        """
        if not equity_curve:
            return {}
        
        try:
            # 提取资金曲线数据
            values = [point["portfolio_value"] for point in equity_curve]
            
            # 基本指标
            final_value = values[-1]
            total_return = (final_value - initial_capital) / initial_capital
            
            # 计算日收益率
            daily_returns = []
            for i in range(1, len(values)):
                daily_return = (values[i] - values[i-1]) / values[i-1]
                daily_returns.append(daily_return)
            
            # 年化收益率
            days = len(values)
            annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
            
            # 最大回撤
            max_drawdown = 0
            peak = values[0]
            for value in values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # 夏普比率
            sharpe_ratio = 0
            if daily_returns and len(daily_returns) > 1:
                avg_return = np.mean(daily_returns)
                std_return = np.std(daily_returns)
                if std_return > 0:
                    sharpe_ratio = avg_return / std_return * np.sqrt(252)  # 年化
            
            # 索提诺比率
            sortino_ratio = 0
            if daily_returns:
                negative_returns = [r for r in daily_returns if r < 0]
                if negative_returns:
                    downside_std = np.std(negative_returns)
                    if downside_std > 0:
                        avg_return = np.mean(daily_returns)
                        sortino_ratio = avg_return / downside_std * np.sqrt(252)
            
            # 卡玛比率
            calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
            
            # 交易统计
            total_trades = len(trades)
            winning_trades = 0
            losing_trades = 0
            total_profit = 0
            total_loss = 0
            
            # 计算每笔交易的盈亏（简化处理）
            buy_trades = {}
            for trade in trades:
                symbol = trade["symbol"]
                if trade["type"] == "buy":
                    if symbol not in buy_trades:
                        buy_trades[symbol] = []
                    buy_trades[symbol].append(trade)
                elif trade["type"] == "sell" and symbol in buy_trades and buy_trades[symbol]:
                    buy_trade = buy_trades[symbol].pop(0)
                    profit = (trade["price"] - buy_trade["price"]) * trade["quantity"] - trade["commission"] - buy_trade["commission"]
                    if profit > 0:
                        winning_trades += 1
                        total_profit += profit
                    else:
                        losing_trades += 1
                        total_loss += abs(profit)
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            avg_win = total_profit / winning_trades if winning_trades > 0 else 0
            avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
            profit_factor = total_profit / total_loss if total_loss > 0 else 0
            
            return {
                "total_return": total_return,
                "annual_return": annual_return,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "calmar_ratio": calmar_ratio,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "profit_factor": profit_factor,
                "volatility": np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
            }
            
        except Exception as e:
            logger.error(f"计算性能指标失败: {e}")
            return {}


class BacktestService:
    """
    回测服务类
    
    提供回测管理的核心业务逻辑
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = get_strategy_cache()
        self.engine = BacktestEngine()
    
    def create_backtest(self, backtest_data: BacktestCreate, user_id: int) -> BacktestResponse:
        """
        创建回测任务
        
        Args:
            backtest_data: 回测创建数据
            user_id: 用户ID
            
        Returns:
            BacktestResponse: 创建的回测信息
        """
        try:
            # 验证策略是否存在且属于用户
            strategy = self.db.query(Strategy).filter(
                and_(Strategy.id == backtest_data.strategy_id, Strategy.user_id == user_id)
            ).first()
            
            if not strategy:
                raise ValueError("策略不存在或无权限")
            
            # 创建回测实例
            backtest = Backtest(
                strategy_id=backtest_data.strategy_id,
                name=backtest_data.name,
                description=backtest_data.description,
                start_date=backtest_data.start_date,
                end_date=backtest_data.end_date,
                initial_capital=backtest_data.initial_capital,
                commission=backtest_data.commission,
                slippage=backtest_data.slippage,
                status=BacktestStatus.PENDING
            )
            
            # 保存到数据库
            self.db.add(backtest)
            self.db.commit()
            self.db.refresh(backtest)
            
            logger.info(f"回测任务创建成功: {backtest.id} - {backtest.name}")
            return BacktestResponse.from_orm(backtest)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建回测任务失败: {e}")
            raise
    
    async def run_backtest(self, backtest_id: int, user_id: int) -> bool:
        """
        执行回测任务
        
        Args:
            backtest_id: 回测ID
            user_id: 用户ID
            
        Returns:
            bool: 是否启动成功
        """
        try:
            # 查询回测任务
            backtest = self.db.query(Backtest).join(Strategy).filter(
                and_(Backtest.id == backtest_id, Strategy.user_id == user_id)
            ).first()
            
            if not backtest:
                return False
            
            if backtest.status != BacktestStatus.PENDING:
                raise ValueError(f"回测状态 {backtest.status} 无法执行")
            
            # 更新状态为运行中
            backtest.status = BacktestStatus.RUNNING
            backtest.started_at = datetime.utcnow()
            self.db.commit()
            
            # 异步执行回测
            asyncio.create_task(self._execute_backtest_async(backtest))
            
            logger.info(f"回测任务启动成功: {backtest_id}")
            return True
            
        except Exception as e:
            logger.error(f"启动回测任务失败: {e}")
            raise
    
    async def _execute_backtest_async(self, backtest: Backtest):
        """
        异步执行回测
        
        Args:
            backtest: 回测实例
        """
        try:
            # 获取策略
            strategy = self.db.query(Strategy).filter(Strategy.id == backtest.strategy_id).first()
            
            # 执行回测
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.engine.executor,
                self.engine.run_backtest,
                strategy,
                backtest
            )
            
            # 更新回测结果
            if result["status"] == "completed":
                backtest.status = BacktestStatus.COMPLETED
                backtest.final_capital = result["final_capital"]
                backtest.execution_time = result["execution_time"]
                backtest.trades_data = result["trades_data"]
                backtest.equity_curve = result["equity_curve"]
                backtest.performance_metrics = result["performance_metrics"]
                
                # 更新性能指标
                metrics = result["performance_metrics"]
                backtest.total_return = metrics.get("total_return", 0)
                backtest.annual_return = metrics.get("annual_return", 0)
                backtest.max_drawdown = metrics.get("max_drawdown", 0)
                backtest.sharpe_ratio = metrics.get("sharpe_ratio", 0)
                backtest.sortino_ratio = metrics.get("sortino_ratio", 0)
                backtest.calmar_ratio = metrics.get("calmar_ratio", 0)
                backtest.total_trades = metrics.get("total_trades", 0)
                backtest.winning_trades = metrics.get("winning_trades", 0)
                backtest.losing_trades = metrics.get("losing_trades", 0)
                backtest.win_rate = metrics.get("win_rate", 0)
                backtest.avg_win = metrics.get("avg_win", 0)
                backtest.avg_loss = metrics.get("avg_loss", 0)
                backtest.profit_factor = metrics.get("profit_factor", 0)
                
            else:
                backtest.status = BacktestStatus.FAILED
                backtest.error_message = result.get("error_message", "未知错误")
            
            backtest.completed_at = datetime.utcnow()
            self.db.commit()
            
            # 缓存回测结果
            self.cache.cache_backtest_result(
                str(backtest.strategy_id),
                str(backtest.id),
                backtest.to_dict()
            )
            
            logger.info(f"回测任务完成: {backtest.id} - {backtest.status}")
            
        except Exception as e:
            logger.error(f"执行回测任务失败: {e}")
            backtest.status = BacktestStatus.FAILED
            backtest.error_message = str(e)
            backtest.completed_at = datetime.utcnow()
            self.db.commit()
    
    def get_backtest(self, backtest_id: int, user_id: int) -> Optional[BacktestDetailResponse]:
        """
        获取回测详情
        
        Args:
            backtest_id: 回测ID
            user_id: 用户ID
            
        Returns:
            Optional[BacktestDetailResponse]: 回测详情
        """
        try:
            # 先从缓存获取
            cached_data = self.cache.get_backtest_result(str(user_id), str(backtest_id))
            if cached_data:
                return BacktestDetailResponse(**cached_data)
            
            # 从数据库查询
            backtest = self.db.query(Backtest).join(Strategy).filter(
                and_(Backtest.id == backtest_id, Strategy.user_id == user_id)
            ).first()
            
            if not backtest:
                return None
            
            response = BacktestDetailResponse.from_orm(backtest)
            
            # 缓存结果
            if backtest.status == BacktestStatus.COMPLETED:
                self.cache.cache_backtest_result(
                    str(backtest.strategy_id),
                    str(backtest.id),
                    response.dict()
                )
            
            return response
            
        except Exception as e:
            logger.error(f"获取回测详情失败: {e}")
            return None
    
    def list_backtests(self, params: BacktestQueryParams, user_id: int) -> BacktestListResponse:
        """
        获取回测列表
        
        Args:
            params: 查询参数
            user_id: 用户ID
            
        Returns:
            BacktestListResponse: 回测列表响应
        """
        try:
            # 构建查询
            query = self.db.query(Backtest).join(Strategy).filter(Strategy.user_id == user_id)
            
            # 策略过滤
            if params.strategy_id:
                query = query.filter(Backtest.strategy_id == params.strategy_id)
            
            # 状态过滤
            if params.status:
                query = query.filter(Backtest.status == params.status)
            
            # 日期过滤
            if params.start_date:
                query = query.filter(Backtest.created_at >= params.start_date)
            if params.end_date:
                query = query.filter(Backtest.created_at <= params.end_date)
            
            # 总数统计
            total = query.count()
            
            # 排序
            if params.sort_by:
                sort_column = getattr(Backtest, params.sort_by, Backtest.created_at)
                if params.sort_order == "asc":
                    query = query.order_by(sort_column)
                else:
                    query = query.order_by(desc(sort_column))
            
            # 分页
            offset = (params.page - 1) * params.size
            backtests = query.offset(offset).limit(params.size).all()
            
            # 转换为响应格式
            backtest_responses = [BacktestResponse.from_orm(b) for b in backtests]
            
            return BacktestListResponse(
                backtests=backtest_responses,
                total=total,
                page=params.page,
                size=params.size
            )
            
        except Exception as e:
            logger.error(f"获取回测列表失败: {e}")
            raise
    
    def cancel_backtest(self, backtest_id: int, user_id: int) -> bool:
        """
        取消回测任务
        
        Args:
            backtest_id: 回测ID
            user_id: 用户ID
            
        Returns:
            bool: 是否取消成功
        """
        try:
            backtest = self.db.query(Backtest).join(Strategy).filter(
                and_(Backtest.id == backtest_id, Strategy.user_id == user_id)
            ).first()
            
            if not backtest:
                return False
            
            if backtest.status not in [BacktestStatus.PENDING, BacktestStatus.RUNNING]:
                raise ValueError(f"回测状态 {backtest.status} 无法取消")
            
            backtest.status = BacktestStatus.CANCELLED
            backtest.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"回测任务取消成功: {backtest_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"取消回测任务失败: {e}")
            raise
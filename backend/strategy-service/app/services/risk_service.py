#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理服务业务逻辑

提供策略风险评估、风险控制和风险监控等功能。
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import json
from enum import Enum

from ..models.strategy import Strategy, Backtest, PerformanceRecord
from ..core.config import settings
from ..core.cache import get_strategy_cache

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class RiskMetric(str, Enum):
    """风险指标类型"""
    VAR = "var"  # 风险价值
    CVAR = "cvar"  # 条件风险价值
    MAX_DRAWDOWN = "max_drawdown"  # 最大回撤
    VOLATILITY = "volatility"  # 波动率
    BETA = "beta"  # 贝塔系数
    SHARPE = "sharpe"  # 夏普比率
    SORTINO = "sortino"  # 索提诺比率
    CALMAR = "calmar"  # 卡玛比率


class RiskAnalyzer:
    """
    风险分析器
    
    提供各种风险指标的计算和分析功能
    """
    
    def __init__(self):
        self.confidence_levels = [0.95, 0.99]  # VaR置信水平
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """
        计算风险价值(VaR)
        
        Args:
            returns: 收益率序列
            confidence_level: 置信水平
            
        Returns:
            float: VaR值
        """
        if not returns:
            return 0.0
        
        try:
            returns_array = np.array(returns)
            percentile = (1 - confidence_level) * 100
            var = np.percentile(returns_array, percentile)
            return abs(var)
        except Exception as e:
            logger.error(f"计算VaR失败: {e}")
            return 0.0
    
    def calculate_cvar(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """
        计算条件风险价值(CVaR)
        
        Args:
            returns: 收益率序列
            confidence_level: 置信水平
            
        Returns:
            float: CVaR值
        """
        if not returns:
            return 0.0
        
        try:
            returns_array = np.array(returns)
            var = self.calculate_var(returns, confidence_level)
            
            # 计算超过VaR的损失的平均值
            tail_losses = returns_array[returns_array <= -var]
            if len(tail_losses) > 0:
                cvar = abs(np.mean(tail_losses))
            else:
                cvar = var
            
            return cvar
        except Exception as e:
            logger.error(f"计算CVaR失败: {e}")
            return 0.0
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> Tuple[float, int, int]:
        """
        计算最大回撤
        
        Args:
            equity_curve: 资金曲线
            
        Returns:
            Tuple[float, int, int]: (最大回撤, 开始索引, 结束索引)
        """
        if not equity_curve or len(equity_curve) < 2:
            return 0.0, 0, 0
        
        try:
            curve = np.array(equity_curve)
            peak = curve[0]
            max_dd = 0.0
            peak_idx = 0
            trough_idx = 0
            
            for i, value in enumerate(curve):
                if value > peak:
                    peak = value
                    peak_idx = i
                
                drawdown = (peak - value) / peak
                if drawdown > max_dd:
                    max_dd = drawdown
                    trough_idx = i
            
            return max_dd, peak_idx, trough_idx
        except Exception as e:
            logger.error(f"计算最大回撤失败: {e}")
            return 0.0, 0, 0
    
    def calculate_volatility(self, returns: List[float], annualized: bool = True) -> float:
        """
        计算波动率
        
        Args:
            returns: 收益率序列
            annualized: 是否年化
            
        Returns:
            float: 波动率
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        try:
            returns_array = np.array(returns)
            volatility = np.std(returns_array)
            
            if annualized:
                # 假设252个交易日
                volatility *= np.sqrt(252)
            
            return volatility
        except Exception as e:
            logger.error(f"计算波动率失败: {e}")
            return 0.0
    
    def calculate_beta(self, strategy_returns: List[float], 
                      market_returns: List[float]) -> float:
        """
        计算贝塔系数
        
        Args:
            strategy_returns: 策略收益率
            market_returns: 市场收益率
            
        Returns:
            float: 贝塔系数
        """
        if not strategy_returns or not market_returns or len(strategy_returns) != len(market_returns):
            return 0.0
        
        try:
            strategy_array = np.array(strategy_returns)
            market_array = np.array(market_returns)
            
            covariance = np.cov(strategy_array, market_array)[0, 1]
            market_variance = np.var(market_array)
            
            if market_variance == 0:
                return 0.0
            
            beta = covariance / market_variance
            return beta
        except Exception as e:
            logger.error(f"计算贝塔系数失败: {e}")
            return 0.0
    
    def calculate_downside_deviation(self, returns: List[float], 
                                   target_return: float = 0.0) -> float:
        """
        计算下行偏差
        
        Args:
            returns: 收益率序列
            target_return: 目标收益率
            
        Returns:
            float: 下行偏差
        """
        if not returns:
            return 0.0
        
        try:
            returns_array = np.array(returns)
            downside_returns = returns_array[returns_array < target_return]
            
            if len(downside_returns) == 0:
                return 0.0
            
            downside_deviation = np.sqrt(np.mean((downside_returns - target_return) ** 2))
            return downside_deviation
        except Exception as e:
            logger.error(f"计算下行偏差失败: {e}")
            return 0.0
    
    def calculate_information_ratio(self, strategy_returns: List[float], 
                                  benchmark_returns: List[float]) -> float:
        """
        计算信息比率
        
        Args:
            strategy_returns: 策略收益率
            benchmark_returns: 基准收益率
            
        Returns:
            float: 信息比率
        """
        if not strategy_returns or not benchmark_returns or len(strategy_returns) != len(benchmark_returns):
            return 0.0
        
        try:
            strategy_array = np.array(strategy_returns)
            benchmark_array = np.array(benchmark_returns)
            
            excess_returns = strategy_array - benchmark_array
            tracking_error = np.std(excess_returns)
            
            if tracking_error == 0:
                return 0.0
            
            information_ratio = np.mean(excess_returns) / tracking_error
            return information_ratio
        except Exception as e:
            logger.error(f"计算信息比率失败: {e}")
            return 0.0


class RiskController:
    """
    风险控制器
    
    提供实时风险控制和预警功能
    """
    
    def __init__(self):
        self.risk_limits = {
            "max_drawdown": settings.risk_max_drawdown,
            "max_position_size": settings.risk_max_position_size,
            "max_daily_loss": settings.risk_max_daily_loss,
            "max_leverage": settings.risk_max_leverage
        }
    
    def check_position_risk(self, position_size: float, portfolio_value: float) -> Dict[str, Any]:
        """
        检查持仓风险
        
        Args:
            position_size: 持仓大小
            portfolio_value: 组合价值
            
        Returns:
            Dict[str, Any]: 风险检查结果
        """
        try:
            position_ratio = abs(position_size) / portfolio_value if portfolio_value > 0 else 0
            
            risk_level = RiskLevel.LOW
            warnings = []
            
            if position_ratio > self.risk_limits["max_position_size"]:
                risk_level = RiskLevel.HIGH
                warnings.append(f"持仓比例 {position_ratio:.2%} 超过限制 {self.risk_limits['max_position_size']:.2%}")
            elif position_ratio > self.risk_limits["max_position_size"] * 0.8:
                risk_level = RiskLevel.MEDIUM
                warnings.append(f"持仓比例 {position_ratio:.2%} 接近限制")
            
            return {
                "risk_level": risk_level,
                "position_ratio": position_ratio,
                "warnings": warnings,
                "is_safe": risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
            }
        except Exception as e:
            logger.error(f"检查持仓风险失败: {e}")
            return {
                "risk_level": RiskLevel.EXTREME,
                "position_ratio": 0,
                "warnings": ["风险检查失败"],
                "is_safe": False
            }
    
    def check_drawdown_risk(self, current_drawdown: float) -> Dict[str, Any]:
        """
        检查回撤风险
        
        Args:
            current_drawdown: 当前回撤
            
        Returns:
            Dict[str, Any]: 风险检查结果
        """
        try:
            risk_level = RiskLevel.LOW
            warnings = []
            
            if current_drawdown > self.risk_limits["max_drawdown"]:
                risk_level = RiskLevel.EXTREME
                warnings.append(f"回撤 {current_drawdown:.2%} 超过限制 {self.risk_limits['max_drawdown']:.2%}")
            elif current_drawdown > self.risk_limits["max_drawdown"] * 0.8:
                risk_level = RiskLevel.HIGH
                warnings.append(f"回撤 {current_drawdown:.2%} 接近限制")
            elif current_drawdown > self.risk_limits["max_drawdown"] * 0.5:
                risk_level = RiskLevel.MEDIUM
                warnings.append(f"回撤 {current_drawdown:.2%} 需要关注")
            
            return {
                "risk_level": risk_level,
                "current_drawdown": current_drawdown,
                "warnings": warnings,
                "should_stop": risk_level == RiskLevel.EXTREME
            }
        except Exception as e:
            logger.error(f"检查回撤风险失败: {e}")
            return {
                "risk_level": RiskLevel.EXTREME,
                "current_drawdown": current_drawdown,
                "warnings": ["风险检查失败"],
                "should_stop": True
            }
    
    def check_daily_loss_risk(self, daily_pnl: float, portfolio_value: float) -> Dict[str, Any]:
        """
        检查日损失风险
        
        Args:
            daily_pnl: 日盈亏
            portfolio_value: 组合价值
            
        Returns:
            Dict[str, Any]: 风险检查结果
        """
        try:
            daily_loss_ratio = abs(daily_pnl) / portfolio_value if portfolio_value > 0 and daily_pnl < 0 else 0
            
            risk_level = RiskLevel.LOW
            warnings = []
            
            if daily_loss_ratio > self.risk_limits["max_daily_loss"]:
                risk_level = RiskLevel.EXTREME
                warnings.append(f"日损失 {daily_loss_ratio:.2%} 超过限制 {self.risk_limits['max_daily_loss']:.2%}")
            elif daily_loss_ratio > self.risk_limits["max_daily_loss"] * 0.8:
                risk_level = RiskLevel.HIGH
                warnings.append(f"日损失 {daily_loss_ratio:.2%} 接近限制")
            
            return {
                "risk_level": risk_level,
                "daily_loss_ratio": daily_loss_ratio,
                "warnings": warnings,
                "should_stop": risk_level == RiskLevel.EXTREME
            }
        except Exception as e:
            logger.error(f"检查日损失风险失败: {e}")
            return {
                "risk_level": RiskLevel.EXTREME,
                "daily_loss_ratio": 0,
                "warnings": ["风险检查失败"],
                "should_stop": True
            }


class RiskService:
    """
    风险管理服务类
    
    提供策略风险评估和管理的核心业务逻辑
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = get_strategy_cache()
        self.analyzer = RiskAnalyzer()
        self.controller = RiskController()
    
    def assess_strategy_risk(self, strategy_id: int, user_id: int) -> Dict[str, Any]:
        """
        评估策略风险
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 风险评估结果
        """
        try:
            # 获取策略
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise ValueError("策略不存在")
            
            # 获取历史回测数据
            backtests = self.db.query(Backtest).filter(
                Backtest.strategy_id == strategy_id
            ).order_by(Backtest.created_at.desc()).limit(10).all()
            
            if not backtests:
                return {
                    "strategy_id": strategy_id,
                    "risk_level": RiskLevel.MEDIUM,
                    "risk_score": 50,
                    "metrics": {},
                    "warnings": ["缺少历史数据，无法准确评估风险"]
                }
            
            # 收集收益率数据
            all_returns = []
            all_equity_curves = []
            
            for backtest in backtests:
                if backtest.equity_curve:
                    equity_curve = [point["portfolio_value"] for point in backtest.equity_curve]
                    if len(equity_curve) > 1:
                        returns = []
                        for i in range(1, len(equity_curve)):
                            ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                            returns.append(ret)
                        all_returns.extend(returns)
                        all_equity_curves.extend(equity_curve)
            
            if not all_returns:
                return {
                    "strategy_id": strategy_id,
                    "risk_level": RiskLevel.MEDIUM,
                    "risk_score": 50,
                    "metrics": {},
                    "warnings": ["无有效的收益率数据"]
                }
            
            # 计算风险指标
            metrics = self._calculate_comprehensive_risk_metrics(all_returns, all_equity_curves)
            
            # 评估风险等级
            risk_level, risk_score = self._assess_risk_level(metrics)
            
            # 生成风险警告
            warnings = self._generate_risk_warnings(metrics)
            
            result = {
                "strategy_id": strategy_id,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "metrics": metrics,
                "warnings": warnings,
                "assessment_time": datetime.utcnow().isoformat()
            }
            
            # 缓存结果
            self.cache.cache_risk_assessment(str(strategy_id), result)
            
            return result
            
        except Exception as e:
            logger.error(f"评估策略风险失败: {e}")
            raise
    
    def _calculate_comprehensive_risk_metrics(self, returns: List[float], 
                                            equity_curve: List[float]) -> Dict[str, float]:
        """
        计算综合风险指标
        
        Args:
            returns: 收益率序列
            equity_curve: 资金曲线
            
        Returns:
            Dict[str, float]: 风险指标字典
        """
        metrics = {}
        
        try:
            # VaR和CVaR
            metrics["var_95"] = self.analyzer.calculate_var(returns, 0.95)
            metrics["var_99"] = self.analyzer.calculate_var(returns, 0.99)
            metrics["cvar_95"] = self.analyzer.calculate_cvar(returns, 0.95)
            metrics["cvar_99"] = self.analyzer.calculate_cvar(returns, 0.99)
            
            # 最大回撤
            max_dd, _, _ = self.analyzer.calculate_max_drawdown(equity_curve)
            metrics["max_drawdown"] = max_dd
            
            # 波动率
            metrics["volatility"] = self.analyzer.calculate_volatility(returns)
            metrics["downside_volatility"] = self.analyzer.calculate_downside_deviation(returns)
            
            # 收益率统计
            if returns:
                metrics["mean_return"] = np.mean(returns)
                metrics["std_return"] = np.std(returns)
                metrics["skewness"] = float(pd.Series(returns).skew())
                metrics["kurtosis"] = float(pd.Series(returns).kurtosis())
                
                # 夏普比率
                if metrics["std_return"] > 0:
                    metrics["sharpe_ratio"] = metrics["mean_return"] / metrics["std_return"] * np.sqrt(252)
                else:
                    metrics["sharpe_ratio"] = 0
                
                # 索提诺比率
                if metrics["downside_volatility"] > 0:
                    metrics["sortino_ratio"] = metrics["mean_return"] / metrics["downside_volatility"] * np.sqrt(252)
                else:
                    metrics["sortino_ratio"] = 0
                
                # 卡玛比率
                if metrics["max_drawdown"] > 0:
                    annual_return = (1 + metrics["mean_return"]) ** 252 - 1
                    metrics["calmar_ratio"] = annual_return / metrics["max_drawdown"]
                else:
                    metrics["calmar_ratio"] = 0
            
            # 胜率统计
            positive_returns = [r for r in returns if r > 0]
            negative_returns = [r for r in returns if r < 0]
            
            metrics["win_rate"] = len(positive_returns) / len(returns) if returns else 0
            metrics["avg_win"] = np.mean(positive_returns) if positive_returns else 0
            metrics["avg_loss"] = np.mean(negative_returns) if negative_returns else 0
            
            if metrics["avg_loss"] != 0:
                metrics["profit_factor"] = abs(metrics["avg_win"]) / abs(metrics["avg_loss"])
            else:
                metrics["profit_factor"] = 0
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
        
        return metrics
    
    def _assess_risk_level(self, metrics: Dict[str, float]) -> Tuple[RiskLevel, int]:
        """
        评估风险等级
        
        Args:
            metrics: 风险指标
            
        Returns:
            Tuple[RiskLevel, int]: (风险等级, 风险评分)
        """
        try:
            risk_score = 0
            
            # 最大回撤评分 (30%权重)
            max_dd = metrics.get("max_drawdown", 0)
            if max_dd <= 0.05:
                risk_score += 30
            elif max_dd <= 0.10:
                risk_score += 25
            elif max_dd <= 0.20:
                risk_score += 15
            elif max_dd <= 0.30:
                risk_score += 5
            
            # 波动率评分 (25%权重)
            volatility = metrics.get("volatility", 0)
            if volatility <= 0.15:
                risk_score += 25
            elif volatility <= 0.25:
                risk_score += 20
            elif volatility <= 0.40:
                risk_score += 10
            elif volatility <= 0.60:
                risk_score += 5
            
            # 夏普比率评分 (20%权重)
            sharpe = metrics.get("sharpe_ratio", 0)
            if sharpe >= 2.0:
                risk_score += 20
            elif sharpe >= 1.5:
                risk_score += 15
            elif sharpe >= 1.0:
                risk_score += 10
            elif sharpe >= 0.5:
                risk_score += 5
            
            # VaR评分 (15%权重)
            var_95 = metrics.get("var_95", 0)
            if var_95 <= 0.02:
                risk_score += 15
            elif var_95 <= 0.05:
                risk_score += 10
            elif var_95 <= 0.10:
                risk_score += 5
            
            # 胜率评分 (10%权重)
            win_rate = metrics.get("win_rate", 0)
            if win_rate >= 0.6:
                risk_score += 10
            elif win_rate >= 0.5:
                risk_score += 7
            elif win_rate >= 0.4:
                risk_score += 3
            
            # 确定风险等级
            if risk_score >= 80:
                risk_level = RiskLevel.LOW
            elif risk_score >= 60:
                risk_level = RiskLevel.MEDIUM
            elif risk_score >= 40:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.EXTREME
            
            return risk_level, risk_score
            
        except Exception as e:
            logger.error(f"评估风险等级失败: {e}")
            return RiskLevel.MEDIUM, 50
    
    def _generate_risk_warnings(self, metrics: Dict[str, float]) -> List[str]:
        """
        生成风险警告
        
        Args:
            metrics: 风险指标
            
        Returns:
            List[str]: 警告列表
        """
        warnings = []
        
        try:
            # 最大回撤警告
            max_dd = metrics.get("max_drawdown", 0)
            if max_dd > 0.30:
                warnings.append(f"最大回撤过高 ({max_dd:.2%})，存在极高风险")
            elif max_dd > 0.20:
                warnings.append(f"最大回撤较高 ({max_dd:.2%})，需要关注")
            
            # 波动率警告
            volatility = metrics.get("volatility", 0)
            if volatility > 0.60:
                warnings.append(f"波动率过高 ({volatility:.2%})，策略不稳定")
            elif volatility > 0.40:
                warnings.append(f"波动率较高 ({volatility:.2%})，风险较大")
            
            # 夏普比率警告
            sharpe = metrics.get("sharpe_ratio", 0)
            if sharpe < 0:
                warnings.append(f"夏普比率为负 ({sharpe:.2f})，风险调整后收益不佳")
            elif sharpe < 0.5:
                warnings.append(f"夏普比率较低 ({sharpe:.2f})，收益风险比不理想")
            
            # VaR警告
            var_95 = metrics.get("var_95", 0)
            if var_95 > 0.10:
                warnings.append(f"95% VaR过高 ({var_95:.2%})，单日损失风险大")
            
            # 胜率警告
            win_rate = metrics.get("win_rate", 0)
            if win_rate < 0.3:
                warnings.append(f"胜率过低 ({win_rate:.2%})，策略有效性存疑")
            
            # 偏度和峰度警告
            skewness = metrics.get("skewness", 0)
            kurtosis = metrics.get("kurtosis", 0)
            
            if skewness < -1:
                warnings.append("收益分布左偏严重，存在极端损失风险")
            if kurtosis > 3:
                warnings.append("收益分布峰度过高，极端事件概率大")
            
        except Exception as e:
            logger.error(f"生成风险警告失败: {e}")
        
        return warnings
    
    def monitor_real_time_risk(self, strategy_id: int, user_id: int) -> Dict[str, Any]:
        """
        实时风险监控
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 实时风险状态
        """
        try:
            # 获取最新性能记录
            latest_record = self.db.query(PerformanceRecord).filter(
                PerformanceRecord.strategy_id == strategy_id
            ).order_by(PerformanceRecord.timestamp.desc()).first()
            
            if not latest_record:
                return {
                    "strategy_id": strategy_id,
                    "status": "no_data",
                    "message": "无实时数据"
                }
            
            # 检查各项风险
            risk_checks = []
            overall_risk_level = RiskLevel.LOW
            should_stop = False
            
            # 持仓风险检查
            if latest_record.portfolio_value > 0:
                position_risk = self.controller.check_position_risk(
                    latest_record.total_positions_value or 0,
                    latest_record.portfolio_value
                )
                risk_checks.append({
                    "type": "position",
                    "result": position_risk
                })
                
                if position_risk["risk_level"] == RiskLevel.HIGH:
                    overall_risk_level = RiskLevel.HIGH
                elif position_risk["risk_level"] == RiskLevel.EXTREME:
                    overall_risk_level = RiskLevel.EXTREME
                    should_stop = True
            
            # 回撤风险检查
            if latest_record.current_drawdown is not None:
                drawdown_risk = self.controller.check_drawdown_risk(
                    latest_record.current_drawdown
                )
                risk_checks.append({
                    "type": "drawdown",
                    "result": drawdown_risk
                })
                
                if drawdown_risk["should_stop"]:
                    should_stop = True
                    overall_risk_level = RiskLevel.EXTREME
            
            # 日损失风险检查
            if latest_record.daily_pnl is not None and latest_record.portfolio_value > 0:
                daily_loss_risk = self.controller.check_daily_loss_risk(
                    latest_record.daily_pnl,
                    latest_record.portfolio_value
                )
                risk_checks.append({
                    "type": "daily_loss",
                    "result": daily_loss_risk
                })
                
                if daily_loss_risk["should_stop"]:
                    should_stop = True
                    overall_risk_level = RiskLevel.EXTREME
            
            return {
                "strategy_id": strategy_id,
                "status": "active",
                "overall_risk_level": overall_risk_level,
                "should_stop": should_stop,
                "risk_checks": risk_checks,
                "latest_record": {
                    "timestamp": latest_record.timestamp.isoformat(),
                    "portfolio_value": latest_record.portfolio_value,
                    "daily_pnl": latest_record.daily_pnl,
                    "current_drawdown": latest_record.current_drawdown
                },
                "check_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"实时风险监控失败: {e}")
            return {
                "strategy_id": strategy_id,
                "status": "error",
                "message": str(e)
            }
    
    def get_risk_report(self, strategy_id: int, user_id: int, 
                       days: int = 30) -> Dict[str, Any]:
        """
        获取风险报告
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            days: 报告天数
            
        Returns:
            Dict[str, Any]: 风险报告
        """
        try:
            # 获取指定时间范围内的性能记录
            start_date = datetime.utcnow() - timedelta(days=days)
            records = self.db.query(PerformanceRecord).filter(
                PerformanceRecord.strategy_id == strategy_id,
                PerformanceRecord.timestamp >= start_date
            ).order_by(PerformanceRecord.timestamp).all()
            
            if not records:
                return {
                    "strategy_id": strategy_id,
                    "period_days": days,
                    "message": "指定时间范围内无数据"
                }
            
            # 提取数据
            timestamps = [r.timestamp for r in records]
            portfolio_values = [r.portfolio_value for r in records]
            daily_pnls = [r.daily_pnl for r in records if r.daily_pnl is not None]
            
            # 计算收益率
            returns = []
            if len(portfolio_values) > 1:
                for i in range(1, len(portfolio_values)):
                    ret = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                    returns.append(ret)
            
            # 计算风险指标
            metrics = self._calculate_comprehensive_risk_metrics(returns, portfolio_values)
            
            # 风险趋势分析
            risk_trend = self._analyze_risk_trend(records)
            
            # 生成建议
            recommendations = self._generate_risk_recommendations(metrics, risk_trend)
            
            return {
                "strategy_id": strategy_id,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "metrics": metrics,
                "risk_trend": risk_trend,
                "recommendations": recommendations,
                "data_points": len(records)
            }
            
        except Exception as e:
            logger.error(f"获取风险报告失败: {e}")
            raise
    
    def _analyze_risk_trend(self, records: List[PerformanceRecord]) -> Dict[str, Any]:
        """
        分析风险趋势
        
        Args:
            records: 性能记录列表
            
        Returns:
            Dict[str, Any]: 风险趋势分析
        """
        try:
            if len(records) < 7:  # 至少需要一周数据
                return {"status": "insufficient_data"}
            
            # 计算滚动风险指标
            window_size = min(7, len(records) // 3)  # 滚动窗口大小
            
            rolling_volatility = []
            rolling_drawdown = []
            
            for i in range(window_size, len(records)):
                window_records = records[i-window_size:i]
                window_values = [r.portfolio_value for r in window_records]
                
                # 计算窗口内的波动率
                if len(window_values) > 1:
                    window_returns = []
                    for j in range(1, len(window_values)):
                        ret = (window_values[j] - window_values[j-1]) / window_values[j-1]
                        window_returns.append(ret)
                    
                    volatility = self.analyzer.calculate_volatility(window_returns, False)
                    rolling_volatility.append(volatility)
                
                # 计算窗口内的最大回撤
                max_dd, _, _ = self.analyzer.calculate_max_drawdown(window_values)
                rolling_drawdown.append(max_dd)
            
            # 趋势分析
            volatility_trend = "stable"
            drawdown_trend = "stable"
            
            if len(rolling_volatility) >= 3:
                recent_vol = np.mean(rolling_volatility[-3:])
                early_vol = np.mean(rolling_volatility[:3])
                
                if recent_vol > early_vol * 1.2:
                    volatility_trend = "increasing"
                elif recent_vol < early_vol * 0.8:
                    volatility_trend = "decreasing"
            
            if len(rolling_drawdown) >= 3:
                recent_dd = np.mean(rolling_drawdown[-3:])
                early_dd = np.mean(rolling_drawdown[:3])
                
                if recent_dd > early_dd * 1.2:
                    drawdown_trend = "increasing"
                elif recent_dd < early_dd * 0.8:
                    drawdown_trend = "decreasing"
            
            return {
                "status": "analyzed",
                "volatility_trend": volatility_trend,
                "drawdown_trend": drawdown_trend,
                "current_volatility": rolling_volatility[-1] if rolling_volatility else 0,
                "current_drawdown": rolling_drawdown[-1] if rolling_drawdown else 0,
                "analysis_window": window_size
            }
            
        except Exception as e:
            logger.error(f"分析风险趋势失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def _generate_risk_recommendations(self, metrics: Dict[str, float], 
                                     risk_trend: Dict[str, Any]) -> List[str]:
        """
        生成风险建议
        
        Args:
            metrics: 风险指标
            risk_trend: 风险趋势
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        try:
            # 基于风险指标的建议
            max_dd = metrics.get("max_drawdown", 0)
            if max_dd > 0.20:
                recommendations.append("建议降低仓位规模或调整策略参数以控制回撤")
            
            volatility = metrics.get("volatility", 0)
            if volatility > 0.40:
                recommendations.append("波动率过高，建议增加风险控制措施")
            
            sharpe = metrics.get("sharpe_ratio", 0)
            if sharpe < 0.5:
                recommendations.append("夏普比率较低，建议优化策略以提高风险调整后收益")
            
            win_rate = metrics.get("win_rate", 0)
            if win_rate < 0.4:
                recommendations.append("胜率较低，建议检查策略逻辑和信号质量")
            
            # 基于趋势的建议
            if risk_trend.get("volatility_trend") == "increasing":
                recommendations.append("波动率呈上升趋势，建议密切监控市场环境变化")
            
            if risk_trend.get("drawdown_trend") == "increasing":
                recommendations.append("回撤呈恶化趋势，建议考虑暂停策略或调整参数")
            
            # 通用建议
            if not recommendations:
                recommendations.append("当前风险水平可接受，建议继续监控")
            
        except Exception as e:
            logger.error(f"生成风险建议失败: {e}")
            recommendations.append("风险分析异常，建议人工检查")
        
        return recommendations
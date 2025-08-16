#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理API路由

提供策略风险评估、实时监控和风险报告等API接口。
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...services.risk_service import RiskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/assessment/{strategy_id}", status_code=200)
async def assess_strategy_risk(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    评估策略风险
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 风险评估结果
    """
    try:
        service = RiskService(db)
        assessment = service.assess_strategy_risk(strategy_id, current_user["id"])
        
        return assessment
        
    except ValueError as e:
        logger.warning(f"风险评估失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"风险评估失败: {e}")
        raise HTTPException(status_code=500, detail="风险评估失败")


@router.get("/monitor/{strategy_id}", status_code=200)
async def monitor_real_time_risk(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    实时风险监控
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 实时风险状态
    """
    try:
        service = RiskService(db)
        risk_status = service.monitor_real_time_risk(strategy_id, current_user["id"])
        
        return risk_status
        
    except Exception as e:
        logger.error(f"实时风险监控失败: {e}")
        raise HTTPException(status_code=500, detail="实时风险监控失败")


@router.get("/report/{strategy_id}", status_code=200)
async def get_risk_report(
    strategy_id: int,
    days: int = Query(30, ge=1, le=365, description="报告天数"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取风险报告
    
    Args:
        strategy_id: 策略ID
        days: 报告天数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 风险报告
    """
    try:
        service = RiskService(db)
        report = service.get_risk_report(strategy_id, current_user["id"], days)
        
        return report
        
    except Exception as e:
        logger.error(f"获取风险报告失败: {e}")
        raise HTTPException(status_code=500, detail="获取风险报告失败")


@router.get("/limits", status_code=200)
async def get_risk_limits(
    current_user: dict = Depends(get_current_user)
):
    """
    获取风险限制配置
    
    Args:
        current_user: 当前用户
        
    Returns:
        dict: 风险限制配置
    """
    try:
        from ...core.config import settings
        
        limits = {
            "max_drawdown": settings.risk_max_drawdown,
            "max_position_size": settings.risk_max_position_size,
            "max_daily_loss": settings.risk_max_daily_loss,
            "max_leverage": settings.risk_max_leverage,
            "description": {
                "max_drawdown": "最大回撤限制",
                "max_position_size": "最大持仓比例限制",
                "max_daily_loss": "最大日损失限制",
                "max_leverage": "最大杠杆倍数限制"
            }
        }
        
        return limits
        
    except Exception as e:
        logger.error(f"获取风险限制配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取风险限制配置失败")


@router.post("/check/position", status_code=200)
async def check_position_risk(
    position_size: float,
    portfolio_value: float,
    current_user: dict = Depends(get_current_user)
):
    """
    检查持仓风险
    
    Args:
        position_size: 持仓大小
        portfolio_value: 组合价值
        current_user: 当前用户
        
    Returns:
        dict: 持仓风险检查结果
    """
    try:
        from ...services.risk_service import RiskController
        
        controller = RiskController()
        risk_check = controller.check_position_risk(position_size, portfolio_value)
        
        return {
            "position_size": position_size,
            "portfolio_value": portfolio_value,
            "risk_check": risk_check,
            "check_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"检查持仓风险失败: {e}")
        raise HTTPException(status_code=500, detail="检查持仓风险失败")


@router.post("/check/drawdown", status_code=200)
async def check_drawdown_risk(
    current_drawdown: float,
    current_user: dict = Depends(get_current_user)
):
    """
    检查回撤风险
    
    Args:
        current_drawdown: 当前回撤
        current_user: 当前用户
        
    Returns:
        dict: 回撤风险检查结果
    """
    try:
        from ...services.risk_service import RiskController
        
        controller = RiskController()
        risk_check = controller.check_drawdown_risk(current_drawdown)
        
        return {
            "current_drawdown": current_drawdown,
            "risk_check": risk_check,
            "check_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"检查回撤风险失败: {e}")
        raise HTTPException(status_code=500, detail="检查回撤风险失败")


@router.post("/check/daily-loss", status_code=200)
async def check_daily_loss_risk(
    daily_pnl: float,
    portfolio_value: float,
    current_user: dict = Depends(get_current_user)
):
    """
    检查日损失风险
    
    Args:
        daily_pnl: 日盈亏
        portfolio_value: 组合价值
        current_user: 当前用户
        
    Returns:
        dict: 日损失风险检查结果
    """
    try:
        from ...services.risk_service import RiskController
        
        controller = RiskController()
        risk_check = controller.check_daily_loss_risk(daily_pnl, portfolio_value)
        
        return {
            "daily_pnl": daily_pnl,
            "portfolio_value": portfolio_value,
            "risk_check": risk_check,
            "check_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"检查日损失风险失败: {e}")
        raise HTTPException(status_code=500, detail="检查日损失风险失败")


@router.get("/metrics/{strategy_id}", status_code=200)
async def get_risk_metrics(
    strategy_id: int,
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$", description="统计周期"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取风险指标
    
    Args:
        strategy_id: 策略ID
        period: 统计周期
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 风险指标
    """
    try:
        # 解析周期
        period_days = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365
        }.get(period, 30)
        
        service = RiskService(db)
        report = service.get_risk_report(strategy_id, current_user["id"], period_days)
        
        # 提取风险指标
        metrics = report.get("metrics", {})
        
        return {
            "strategy_id": strategy_id,
            "period": period,
            "period_days": period_days,
            "metrics": metrics,
            "calculation_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取风险指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取风险指标失败")


@router.get("/alerts/{strategy_id}", status_code=200)
async def get_risk_alerts(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取风险预警
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 风险预警信息
    """
    try:
        service = RiskService(db)
        
        # 获取风险评估
        assessment = service.assess_strategy_risk(strategy_id, current_user["id"])
        
        # 获取实时监控
        monitor = service.monitor_real_time_risk(strategy_id, current_user["id"])
        
        # 整合预警信息
        alerts = []
        
        # 从风险评估中提取警告
        if "warnings" in assessment:
            for warning in assessment["warnings"]:
                alerts.append({
                    "type": "assessment",
                    "level": "warning",
                    "message": warning,
                    "timestamp": assessment.get("assessment_time")
                })
        
        # 从实时监控中提取警告
        if monitor.get("status") == "active" and "risk_checks" in monitor:
            for check in monitor["risk_checks"]:
                if "warnings" in check["result"]:
                    for warning in check["result"]["warnings"]:
                        alerts.append({
                            "type": "real_time",
                            "level": "warning" if check["result"]["risk_level"] != "extreme" else "critical",
                            "message": warning,
                            "timestamp": monitor.get("check_time")
                        })
        
        # 按时间排序
        alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "strategy_id": strategy_id,
            "alerts": alerts,
            "alert_count": len(alerts),
            "critical_count": len([a for a in alerts if a["level"] == "critical"]),
            "warning_count": len([a for a in alerts if a["level"] == "warning"]),
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取风险预警失败: {e}")
        raise HTTPException(status_code=500, detail="获取风险预警失败")


@router.get("/dashboard/{strategy_id}", status_code=200)
async def get_risk_dashboard(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取风险仪表板数据
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 风险仪表板数据
    """
    try:
        service = RiskService(db)
        
        # 获取风险评估
        assessment = service.assess_strategy_risk(strategy_id, current_user["id"])
        
        # 获取实时监控
        monitor = service.monitor_real_time_risk(strategy_id, current_user["id"])
        
        # 获取30天风险报告
        report_30d = service.get_risk_report(strategy_id, current_user["id"], 30)
        
        # 构建仪表板数据
        dashboard = {
            "strategy_id": strategy_id,
            "overview": {
                "risk_level": assessment.get("risk_level"),
                "risk_score": assessment.get("risk_score"),
                "overall_status": monitor.get("overall_risk_level"),
                "should_stop": monitor.get("should_stop", False)
            },
            "key_metrics": {
                "max_drawdown": assessment.get("metrics", {}).get("max_drawdown"),
                "volatility": assessment.get("metrics", {}).get("volatility"),
                "sharpe_ratio": assessment.get("metrics", {}).get("sharpe_ratio"),
                "var_95": assessment.get("metrics", {}).get("var_95")
            },
            "real_time_status": {
                "portfolio_value": monitor.get("latest_record", {}).get("portfolio_value"),
                "daily_pnl": monitor.get("latest_record", {}).get("daily_pnl"),
                "current_drawdown": monitor.get("latest_record", {}).get("current_drawdown"),
                "last_update": monitor.get("latest_record", {}).get("timestamp")
            },
            "trend_analysis": report_30d.get("risk_trend", {}),
            "recommendations": report_30d.get("recommendations", []),
            "warnings": assessment.get("warnings", []),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return dashboard
        
    except Exception as e:
        logger.error(f"获取风险仪表板数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取风险仪表板数据失败")
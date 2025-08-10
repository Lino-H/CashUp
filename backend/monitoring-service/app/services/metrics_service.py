#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 指标服务

指标收集、处理和管理的业务逻辑
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.core.database import get_db
from app.core.cache import CacheManager
from app.core.exceptions import MetricsCollectionError, DataStorageError
from app.models.metrics import Metric, MetricValue, MetricAlert, MetricType, MetricStatus
from app.schemas.metrics import (
    MetricCreate, MetricUpdate, MetricValueCreate, MetricValueBatchCreate,
    MetricAlertCreate, MetricAlertUpdate, MetricQuery, MetricAggregateQuery,
    AggregationType
)

logger = logging.getLogger(__name__)


class MetricsService:
    """指标服务类"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.collection_tasks = {}
        
    async def create_metric(self, db: Session, metric_data: MetricCreate) -> Metric:
        """创建指标"""
        try:
            # 检查指标名称是否已存在
            existing = db.query(Metric).filter(
                and_(
                    Metric.name == metric_data.name,
                    Metric.source == metric_data.source
                )
            ).first()
            
            if existing:
                raise ValueError(f"Metric '{metric_data.name}' already exists for source '{metric_data.source}'")
            
            # 创建指标
            metric = Metric(
                name=metric_data.name,
                description=metric_data.description,
                metric_type=metric_data.metric_type,
                category=metric_data.category,
                unit=metric_data.unit,
                source=metric_data.source,
                tags=metric_data.tags or {},
                metadata=metric_data.metadata or {},
                collection_interval=metric_data.collection_interval,
                retention_days=metric_data.retention_days,
                aggregation_method=metric_data.aggregation_method,
                enabled=metric_data.enabled
            )
            
            db.add(metric)
            db.commit()
            db.refresh(metric)
            
            # 清除相关缓存
            await self.cache.clear_pattern("metrics:*")
            
            logger.info(f"Created metric: {metric.name} (ID: {metric.id})")
            return metric
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create metric: {e}")
            raise MetricsCollectionError(f"Failed to create metric: {e}")
    
    async def get_metric(self, db: Session, metric_id: int) -> Optional[Metric]:
        """获取指标详情"""
        cache_key = f"metrics:detail:{metric_id}"
        
        # 尝试从缓存获取
        cached_metric = await self.cache.get(cache_key)
        if cached_metric:
            return cached_metric
        
        # 从数据库获取
        metric = db.query(Metric).filter(Metric.id == metric_id).first()
        
        if metric:
            # 缓存结果
            await self.cache.set(cache_key, metric, ttl=300)
        
        return metric
    
    async def get_metrics(self, db: Session, query: MetricQuery) -> Tuple[List[Metric], int]:
        """获取指标列表"""
        try:
            # 构建查询
            db_query = db.query(Metric)
            
            # 应用过滤条件
            if query.name:
                db_query = db_query.filter(Metric.name.ilike(f"%{query.name}%"))
            
            if query.metric_type:
                db_query = db_query.filter(Metric.metric_type == query.metric_type)
            
            if query.category:
                db_query = db_query.filter(Metric.category == query.category)
            
            if query.source:
                db_query = db_query.filter(Metric.source.ilike(f"%{query.source}%"))
            
            if query.status:
                db_query = db_query.filter(Metric.status == query.status)
            
            if query.enabled is not None:
                db_query = db_query.filter(Metric.enabled == query.enabled)
            
            if query.tags:
                for key, value in query.tags.items():
                    db_query = db_query.filter(
                        Metric.tags[key].astext == value
                    )
            
            if query.created_after:
                db_query = db_query.filter(Metric.created_at >= query.created_after)
            
            if query.created_before:
                db_query = db_query.filter(Metric.created_at <= query.created_before)
            
            # 获取总数
            total = db_query.count()
            
            # 应用排序
            if query.order_by:
                order_field = getattr(Metric, query.order_by, None)
                if order_field:
                    if query.order_desc:
                        db_query = db_query.order_by(desc(order_field))
                    else:
                        db_query = db_query.order_by(asc(order_field))
            
            # 应用分页
            metrics = db_query.offset(query.offset).limit(query.limit).all()
            
            return metrics, total
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            raise MetricsCollectionError(f"Failed to get metrics: {e}")
    
    async def update_metric(self, db: Session, metric_id: int, metric_data: MetricUpdate) -> Optional[Metric]:
        """更新指标"""
        try:
            metric = db.query(Metric).filter(Metric.id == metric_id).first()
            if not metric:
                return None
            
            # 更新字段
            update_data = metric_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(metric, field, value)
            
            metric.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(metric)
            
            # 清除相关缓存
            await self.cache.delete(f"metrics:detail:{metric_id}")
            await self.cache.clear_pattern("metrics:*")
            
            logger.info(f"Updated metric: {metric.name} (ID: {metric.id})")
            return metric
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update metric: {e}")
            raise MetricsCollectionError(f"Failed to update metric: {e}")
    
    async def delete_metric(self, db: Session, metric_id: int) -> bool:
        """删除指标"""
        try:
            metric = db.query(Metric).filter(Metric.id == metric_id).first()
            if not metric:
                return False
            
            # 删除相关的指标值和告警
            db.query(MetricValue).filter(MetricValue.metric_id == metric_id).delete()
            db.query(MetricAlert).filter(MetricAlert.metric_id == metric_id).delete()
            
            # 删除指标
            db.delete(metric)
            db.commit()
            
            # 清除相关缓存
            await self.cache.delete(f"metrics:detail:{metric_id}")
            await self.cache.clear_pattern("metrics:*")
            
            logger.info(f"Deleted metric: {metric.name} (ID: {metric.id})")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete metric: {e}")
            raise MetricsCollectionError(f"Failed to delete metric: {e}")
    
    async def add_metric_value(self, db: Session, metric_id: int, value_data: MetricValueCreate) -> MetricValue:
        """添加指标值"""
        try:
            # 检查指标是否存在
            metric = db.query(Metric).filter(Metric.id == metric_id).first()
            if not metric:
                raise ValueError(f"Metric with ID {metric_id} not found")
            
            # 创建指标值
            metric_value = MetricValue(
                metric_id=metric_id,
                value=value_data.value,
                timestamp=value_data.timestamp or datetime.utcnow(),
                labels=value_data.labels or {},
                metadata=value_data.metadata or {}
            )
            
            db.add(metric_value)
            
            # 更新指标状态
            metric.last_value = value_data.value
            metric.last_updated = metric_value.timestamp
            metric.value_count += 1
            
            # 更新统计信息
            if metric.min_value is None or value_data.value < metric.min_value:
                metric.min_value = value_data.value
            if metric.max_value is None or value_data.value > metric.max_value:
                metric.max_value = value_data.value
            
            # 计算平均值
            if metric.avg_value is None:
                metric.avg_value = value_data.value
            else:
                metric.avg_value = (
                    (metric.avg_value * (metric.value_count - 1) + value_data.value) / 
                    metric.value_count
                )
            
            db.commit()
            db.refresh(metric_value)
            
            # 检查告警规则
            await self._check_alert_rules(db, metric, metric_value)
            
            # 清除相关缓存
            await self.cache.clear_pattern(f"metrics:values:{metric_id}:*")
            
            logger.debug(f"Added value {value_data.value} to metric {metric.name}")
            return metric_value
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add metric value: {e}")
            raise DataStorageError(f"Failed to add metric value: {e}")
    
    async def add_metric_values_batch(self, db: Session, batch_data: MetricValueBatchCreate) -> List[MetricValue]:
        """批量添加指标值"""
        try:
            metric_values = []
            
            for value_data in batch_data.values:
                # 检查指标是否存在
                metric = db.query(Metric).filter(Metric.id == value_data.metric_id).first()
                if not metric:
                    logger.warning(f"Metric with ID {value_data.metric_id} not found, skipping")
                    continue
                
                # 创建指标值
                metric_value = MetricValue(
                    metric_id=value_data.metric_id,
                    value=value_data.value,
                    timestamp=value_data.timestamp or datetime.utcnow(),
                    labels=value_data.labels or {},
                    metadata=value_data.metadata or {}
                )
                
                db.add(metric_value)
                metric_values.append(metric_value)
                
                # 更新指标统计
                metric.last_value = value_data.value
                metric.last_updated = metric_value.timestamp
                metric.value_count += 1
            
            db.commit()
            
            # 批量刷新
            for mv in metric_values:
                db.refresh(mv)
            
            # 清除相关缓存
            await self.cache.clear_pattern("metrics:values:*")
            
            logger.info(f"Added {len(metric_values)} metric values in batch")
            return metric_values
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add metric values batch: {e}")
            raise DataStorageError(f"Failed to add metric values batch: {e}")
    
    async def get_metric_values(self, db: Session, metric_id: int, 
                               start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None,
                               limit: int = 1000) -> List[MetricValue]:
        """获取指标值"""
        try:
            # 构建缓存键
            cache_key = f"metrics:values:{metric_id}:{start_time}:{end_time}:{limit}"
            
            # 尝试从缓存获取
            cached_values = await self.cache.get(cache_key)
            if cached_values:
                return cached_values
            
            # 构建查询
            query = db.query(MetricValue).filter(MetricValue.metric_id == metric_id)
            
            if start_time:
                query = query.filter(MetricValue.timestamp >= start_time)
            
            if end_time:
                query = query.filter(MetricValue.timestamp <= end_time)
            
            # 按时间倒序排列
            values = query.order_by(desc(MetricValue.timestamp)).limit(limit).all()
            
            # 缓存结果
            await self.cache.set(cache_key, values, ttl=60)
            
            return values
            
        except Exception as e:
            logger.error(f"Failed to get metric values: {e}")
            raise MetricsCollectionError(f"Failed to get metric values: {e}")
    
    async def aggregate_metrics(self, db: Session, query: MetricAggregateQuery) -> Dict[str, Any]:
        """聚合指标数据"""
        try:
            # 构建缓存键
            cache_key = f"metrics:aggregate:{hash(str(query.dict()))}"
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # 构建查询
            base_query = db.query(MetricValue).join(Metric)
            
            # 应用过滤条件
            if query.metric_ids:
                base_query = base_query.filter(MetricValue.metric_id.in_(query.metric_ids))
            
            if query.start_time:
                base_query = base_query.filter(MetricValue.timestamp >= query.start_time)
            
            if query.end_time:
                base_query = base_query.filter(MetricValue.timestamp <= query.end_time)
            
            if query.labels:
                for key, value in query.labels.items():
                    base_query = base_query.filter(
                        MetricValue.labels[key].astext == value
                    )
            
            # 执行聚合
            result = {}
            
            if AggregationType.COUNT in query.aggregations:
                result['count'] = base_query.count()
            
            if AggregationType.SUM in query.aggregations:
                result['sum'] = base_query.with_entities(
                    func.sum(MetricValue.value)
                ).scalar() or 0
            
            if AggregationType.AVG in query.aggregations:
                result['avg'] = base_query.with_entities(
                    func.avg(MetricValue.value)
                ).scalar() or 0
            
            if AggregationType.MIN in query.aggregations:
                result['min'] = base_query.with_entities(
                    func.min(MetricValue.value)
                ).scalar()
            
            if AggregationType.MAX in query.aggregations:
                result['max'] = base_query.with_entities(
                    func.max(MetricValue.value)
                ).scalar()
            
            if AggregationType.STDDEV in query.aggregations:
                result['stddev'] = base_query.with_entities(
                    func.stddev(MetricValue.value)
                ).scalar() or 0
            
            # 时间序列聚合
            if query.group_by_time:
                time_series = self._aggregate_by_time(
                    base_query, query.group_by_time, query.aggregations[0]
                )
                result['time_series'] = time_series
            
            # 缓存结果
            await self.cache.set(cache_key, result, ttl=300)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            raise MetricsCollectionError(f"Failed to aggregate metrics: {e}")
    
    async def get_prometheus_metrics(self, db: Session) -> str:
        """获取Prometheus格式的指标"""
        try:
            cache_key = "metrics:prometheus"
            
            # 尝试从缓存获取
            cached_metrics = await self.cache.get(cache_key)
            if cached_metrics:
                return cached_metrics
            
            # 获取所有启用的指标
            metrics = db.query(Metric).filter(Metric.enabled == True).all()
            
            prometheus_output = []
            
            for metric in metrics:
                # 获取最新的指标值
                latest_value = db.query(MetricValue).filter(
                    MetricValue.metric_id == metric.id
                ).order_by(desc(MetricValue.timestamp)).first()
                
                if latest_value:
                    # 构建Prometheus格式
                    metric_name = metric.name.replace('-', '_').replace('.', '_')
                    
                    # 添加HELP和TYPE注释
                    if metric.description:
                        prometheus_output.append(f"# HELP {metric_name} {metric.description}")
                    
                    metric_type = "gauge"  # 默认类型
                    if metric.metric_type == MetricType.COUNTER:
                        metric_type = "counter"
                    elif metric.metric_type == MetricType.HISTOGRAM:
                        metric_type = "histogram"
                    
                    prometheus_output.append(f"# TYPE {metric_name} {metric_type}")
                    
                    # 构建标签
                    labels = []
                    if latest_value.labels:
                        for key, value in latest_value.labels.items():
                            labels.append(f'{key}="{value}"')
                    
                    # 添加源标签
                    labels.append(f'source="{metric.source}"')
                    
                    label_str = ",".join(labels)
                    if label_str:
                        prometheus_output.append(f"{metric_name}{{{label_str}}} {latest_value.value}")
                    else:
                        prometheus_output.append(f"{metric_name} {latest_value.value}")
            
            result = "\n".join(prometheus_output)
            
            # 缓存结果
            await self.cache.set(cache_key, result, ttl=30)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get Prometheus metrics: {e}")
            raise MetricsCollectionError(f"Failed to get Prometheus metrics: {e}")
    
    async def trigger_collection(self, db: Session, metric_id: Optional[int] = None) -> Dict[str, Any]:
        """手动触发指标收集"""
        try:
            if metric_id:
                # 收集单个指标
                metric = db.query(Metric).filter(Metric.id == metric_id).first()
                if not metric:
                    raise ValueError(f"Metric with ID {metric_id} not found")
                
                result = await self._collect_metric(db, metric)
                return {"metric_id": metric_id, "result": result}
            else:
                # 收集所有启用的指标
                metrics = db.query(Metric).filter(Metric.enabled == True).all()
                results = []
                
                for metric in metrics:
                    try:
                        result = await self._collect_metric(db, metric)
                        results.append({"metric_id": metric.id, "result": result})
                    except Exception as e:
                        logger.error(f"Failed to collect metric {metric.id}: {e}")
                        results.append({"metric_id": metric.id, "error": str(e)})
                
                return {"total_metrics": len(metrics), "results": results}
                
        except Exception as e:
            logger.error(f"Failed to trigger collection: {e}")
            raise MetricsCollectionError(f"Failed to trigger collection: {e}")
    
    async def get_metrics_statistics(self, db: Session) -> Dict[str, Any]:
        """获取指标统计信息"""
        try:
            cache_key = "metrics:statistics"
            
            # 尝试从缓存获取
            cached_stats = await self.cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # 基础统计
            total_metrics = db.query(Metric).count()
            enabled_metrics = db.query(Metric).filter(Metric.enabled == True).count()
            active_metrics = db.query(Metric).filter(
                and_(
                    Metric.enabled == True,
                    Metric.status == MetricStatus.ACTIVE
                )
            ).count()
            
            # 按类型统计
            type_stats = db.query(
                Metric.metric_type,
                func.count(Metric.id)
            ).group_by(Metric.metric_type).all()
            
            # 按分类统计
            category_stats = db.query(
                Metric.category,
                func.count(Metric.id)
            ).group_by(Metric.category).all()
            
            # 按来源统计
            source_stats = db.query(
                Metric.source,
                func.count(Metric.id)
            ).group_by(Metric.source).all()
            
            # 数据量统计
            total_values = db.query(MetricValue).count()
            
            # 最近24小时的数据量
            recent_values = db.query(MetricValue).filter(
                MetricValue.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            # 告警统计
            total_alerts = db.query(MetricAlert).count()
            active_alerts = db.query(MetricAlert).filter(
                MetricAlert.enabled == True
            ).count()
            
            stats = {
                "total_metrics": total_metrics,
                "enabled_metrics": enabled_metrics,
                "active_metrics": active_metrics,
                "total_values": total_values,
                "recent_values_24h": recent_values,
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "type_distribution": dict(type_stats),
                "category_distribution": dict(category_stats),
                "source_distribution": dict(source_stats),
                "collection_rate": recent_values / 24 if recent_values > 0 else 0,
                "avg_values_per_metric": total_values / total_metrics if total_metrics > 0 else 0
            }
            
            # 缓存结果
            await self.cache.set(cache_key, stats, ttl=300)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get metrics statistics: {e}")
            raise MetricsCollectionError(f"Failed to get metrics statistics: {e}")
    
    async def cleanup_expired_data(self, db: Session) -> Dict[str, int]:
        """清理过期数据"""
        try:
            cleanup_stats = {"deleted_values": 0, "updated_metrics": 0}
            
            # 获取所有指标的保留策略
            metrics = db.query(Metric).all()
            
            for metric in metrics:
                if metric.retention_days and metric.retention_days > 0:
                    cutoff_date = datetime.utcnow() - timedelta(days=metric.retention_days)
                    
                    # 删除过期的指标值
                    deleted_count = db.query(MetricValue).filter(
                        and_(
                            MetricValue.metric_id == metric.id,
                            MetricValue.timestamp < cutoff_date
                        )
                    ).delete()
                    
                    cleanup_stats["deleted_values"] += deleted_count
                    
                    if deleted_count > 0:
                        # 更新指标的值计数
                        remaining_count = db.query(MetricValue).filter(
                            MetricValue.metric_id == metric.id
                        ).count()
                        
                        metric.value_count = remaining_count
                        cleanup_stats["updated_metrics"] += 1
            
            db.commit()
            
            # 清除相关缓存
            await self.cache.clear_pattern("metrics:*")
            
            logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup expired data: {e}")
            raise MetricsCollectionError(f"Failed to cleanup expired data: {e}")
    
    async def _collect_metric(self, db: Session, metric: Metric) -> Dict[str, Any]:
        """收集单个指标的数据"""
        # 这里应该实现具体的指标收集逻辑
        # 根据指标的源和类型，调用相应的收集器
        
        # 示例实现：模拟数据收集
        import random
        
        value = random.uniform(0, 100)
        timestamp = datetime.utcnow()
        
        # 创建指标值
        metric_value = MetricValue(
            metric_id=metric.id,
            value=value,
            timestamp=timestamp,
            labels={"collected": "true"},
            metadata={"collection_method": "manual"}
        )
        
        db.add(metric_value)
        
        # 更新指标状态
        metric.last_value = value
        metric.last_updated = timestamp
        metric.value_count += 1
        
        db.commit()
        
        return {
            "value": value,
            "timestamp": timestamp.isoformat(),
            "status": "success"
        }
    
    async def _check_alert_rules(self, db: Session, metric: Metric, metric_value: MetricValue):
        """检查告警规则"""
        # 获取该指标的所有启用的告警规则
        alert_rules = db.query(MetricAlert).filter(
            and_(
                MetricAlert.metric_id == metric.id,
                MetricAlert.enabled == True
            )
        ).all()
        
        for rule in alert_rules:
            try:
                # 检查是否触发告警
                if rule.is_triggered(metric_value.value):
                    # 这里应该触发告警通知
                    logger.warning(f"Alert triggered for metric {metric.name}: {rule.get_alert_message(metric_value.value)}")
                    
                    # 更新告警状态
                    rule.last_triggered_at = datetime.utcnow()
                    rule.trigger_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to check alert rule {rule.id}: {e}")
        
        db.commit()
    
    def _aggregate_by_time(self, query, interval: str, aggregation: AggregationType) -> List[Dict[str, Any]]:
        """按时间间隔聚合数据"""
        # 这里应该实现时间序列聚合逻辑
        # 根据间隔（如5m, 1h, 1d）对数据进行分组聚合
        
        # 示例实现
        return []
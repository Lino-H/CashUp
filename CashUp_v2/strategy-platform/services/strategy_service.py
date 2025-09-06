"""
策略服务层
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json
import asyncio
import importlib.util
import inspect
from pathlib import Path

from models.models import Strategy
from schemas.strategy import StrategyCreate, StrategyUpdate, StrategyType, StrategyStatus
from strategies.manager import StrategyManager
from data.manager import DataManager
from utils.logger import get_logger

logger = get_logger(__name__)

class StrategyService:
    """策略服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.strategy_manager = StrategyManager()
        self.data_manager = DataManager()
        self.running_strategies = {}
    
    async def get_strategy_by_id(self, strategy_id: int) -> Optional[Strategy]:
        """根据ID获取策略"""
        query = select(Strategy).where(Strategy.id == strategy_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_strategies(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = None, 
        search: Optional[str] = None
    ) -> Tuple[List[Strategy], int]:
        """获取策略列表"""
        query = select(Strategy)
        
        conditions = []
        if status:
            conditions.append(Strategy.status == status)
        
        if search:
            conditions.append(
                or_(
                    Strategy.name.ilike(f"%{search}%"),
                    Strategy.description.ilike(f"%{search}%")
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 获取总数
        count_query = select(Strategy.__table__)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.db.execute(count_query)
        total = len(count_result.fetchall())
        
        # 分页查询
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        strategies = result.scalars().all()
        
        return list(strategies), total
    
    async def create_strategy(self, strategy_data: StrategyCreate) -> Strategy:
        """创建策略"""
        # 验证策略代码
        validation_result = self.validate_strategy_code(strategy_data.code)
        if not validation_result["valid"]:
            raise ValueError(f"策略代码无效: {'; '.join(validation_result['errors'])}")
        
        strategy = Strategy(
            name=strategy_data.name,
            description=strategy_data.description,
            type=strategy_data.type,
            code=strategy_data.code,
            config=strategy_data.config,
            version=strategy_data.version,
            author=strategy_data.author,
            tags=strategy_data.tags,
            status=StrategyStatus.DRAFT
        )
        
        self.db.add(strategy)
        await self.db.commit()
        await self.db.refresh(strategy)
        
        # 保存策略代码到文件
        await self._save_strategy_to_file(strategy)
        
        logger.info(f"策略创建成功: {strategy.name}")
        return strategy
    
    async def update_strategy(self, strategy_id: int, update_data: dict) -> Strategy:
        """更新策略"""
        query = update(Strategy).where(Strategy.id == strategy_id).values(**update_data)
        await self.db.execute(query)
        await self.db.commit()
        
        updated_strategy = await self.get_strategy_by_id(strategy_id)
        
        # 如果更新了代码，重新保存到文件
        if "code" in update_data:
            await self._save_strategy_to_file(updated_strategy)
        
        return updated_strategy
    
    async def delete_strategy(self, strategy_id: int) -> bool:
        """删除策略"""
        # 先停止策略
        await self.stop_strategy(strategy_id)
        
        query = delete(Strategy).where(Strategy.id == strategy_id)
        result = await self.db.execute(query)
        await self.db.commit()
        
        # 删除策略文件
        strategy = await self.get_strategy_by_id(strategy_id)
        if strategy:
            await self._delete_strategy_file(strategy)
        
        return result.rowcount > 0
    
    async def start_strategy(self, strategy_id: int) -> bool:
        """启动策略"""
        try:
            strategy = await self.get_strategy_by_id(strategy_id)
            if not strategy:
                return False
            
            # 如果策略已经在运行，先停止
            if strategy_id in self.running_strategies:
                await self.stop_strategy(strategy_id)
            
            # 创建策略配置
            from ..strategies.base import StrategyConfig, TimeFrame
            
            config = StrategyConfig(
                symbols=strategy.config.get("symbols", ["BTCUSDT"]),
                timeframe=TimeFrame(strategy.config.get("timeframe", "1h")),
                initial_capital=strategy.config.get("initial_capital", 10000.0),
                **strategy.config.get("extra_params", {})
            )
            
            # 加载策略
            strategy_instance = self.strategy_manager.load_strategy(strategy.name, config)
            if not strategy_instance:
                return False
            
            # 启动策略
            success = await self.strategy_manager.start_strategy(strategy.name, self.data_manager)
            
            if success:
                self.running_strategies[strategy_id] = strategy_instance
                
                # 更新策略状态
                await self.update_strategy(strategy_id, {
                    "status": StrategyStatus.ACTIVE,
                    "last_run_at": datetime.utcnow()
                })
                
                logger.info(f"策略启动成功: {strategy.name}")
                return True
            else:
                logger.error(f"策略启动失败: {strategy.name}")
                return False
                
        except Exception as e:
            logger.error(f"启动策略失败: {e}")
            return False
    
    async def stop_strategy(self, strategy_id: int) -> bool:
        """停止策略"""
        try:
            strategy = await self.get_strategy_by_id(strategy_id)
            if not strategy:
                return False
            
            # 停止策略
            success = self.strategy_manager.stop_strategy(strategy.name)
            
            if success:
                # 从运行列表中移除
                if strategy_id in self.running_strategies:
                    del self.running_strategies[strategy_id]
                
                # 更新策略状态
                await self.update_strategy(strategy_id, {"status": StrategyStatus.INACTIVE})
                
                logger.info(f"策略停止成功: {strategy.name}")
                return True
            else:
                logger.error(f"策略停止失败: {strategy.name}")
                return False
                
        except Exception as e:
            logger.error(f"停止策略失败: {e}")
            return False
    
    async def reload_strategy(self, strategy_id: int) -> bool:
        """重新加载策略"""
        try:
            strategy = await self.get_strategy_by_id(strategy_id)
            if not strategy:
                return False
            
            # 重新发现策略
            self.strategy_manager.discover_strategies()
            
            # 如果策略正在运行，先停止
            if strategy_id in self.running_strategies:
                await self.stop_strategy(strategy_id)
            
            # 重新加载策略
            success = self.strategy_manager.reload_strategy(strategy.name)
            
            if success:
                logger.info(f"策略重新加载成功: {strategy.name}")
                return True
            else:
                logger.error(f"策略重新加载失败: {strategy.name}")
                return False
                
        except Exception as e:
            logger.error(f"重新加载策略失败: {e}")
            return False
    
    async def get_strategy_performance(self, strategy_id: int) -> Dict[str, Any]:
        """获取策略性能"""
        try:
            strategy = await self.get_strategy_by_id(strategy_id)
            if not strategy:
                return {}
            
            # 如果策略正在运行，获取实时性能
            if strategy_id in self.running_strategies:
                strategy_instance = self.running_strategies[strategy_id]
                performance = strategy_instance.calculate_metrics()
                return performance.__dict__
            else:
                # 返回历史性能数据
                return strategy.performance or {}
                
        except Exception as e:
            logger.error(f"获取策略性能失败: {e}")
            return {}
    
    def validate_strategy_code(self, code: str) -> Dict[str, Any]:
        """验证策略代码"""
        return self.strategy_manager.validate_strategy_code(code)
    
    def create_strategy_template(self, strategy_name: str, strategy_type: str) -> str:
        """创建策略模板"""
        return self.strategy_manager.create_strategy_template(strategy_name, strategy_type)
    
    def get_strategy_template_types(self) -> List[str]:
        """获取策略模板类型"""
        return ["basic", "ma_cross", "rsi", "grid"]
    
    async def _save_strategy_to_file(self, strategy: Strategy) -> None:
        """保存策略代码到文件"""
        try:
            strategy_dir = Path(self.strategy_manager.strategies_dir) / "custom"
            strategy_dir.mkdir(exist_ok=True)
            
            file_path = strategy_dir / f"{strategy.name}.py"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(strategy.code)
            
            logger.info(f"策略代码已保存到文件: {file_path}")
            
        except Exception as e:
            logger.error(f"保存策略代码到文件失败: {e}")
    
    async def _delete_strategy_file(self, strategy: Strategy) -> None:
        """删除策略文件"""
        try:
            strategy_dir = Path(self.strategy_manager.strategies_dir) / "custom"
            file_path = strategy_dir / f"{strategy.name}.py"
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"策略文件已删除: {file_path}")
            
        except Exception as e:
            logger.error(f"删除策略文件失败: {e}")
    
    async def get_running_strategies(self) -> List[Dict[str, Any]]:
        """获取正在运行的策略"""
        running_strategies = []
        
        for strategy_id, strategy_instance in self.running_strategies.items():
            strategy = await self.get_strategy_by_id(strategy_id)
            if strategy:
                running_strategies.append({
                    "id": strategy.id,
                    "name": strategy.name,
                    "type": strategy.type,
                    "status": "running",
                    "start_time": strategy_instance.start_time if hasattr(strategy_instance, 'start_time') else None,
                    "performance": strategy_instance.calculate_metrics().__dict__
                })
        
        return running_strategies
    
    async def get_strategy_logs(self, strategy_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """获取策略日志"""
        # 这里应该从日志系统获取策略日志
        # 现在返回模拟数据
        return [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "策略运行正常",
                "strategy_id": strategy_id
            }
        ]
    
    async def batch_update_strategies(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量更新策略"""
        results = []
        
        for update in updates:
            strategy_id = update.get("id")
            if not strategy_id:
                continue
            
            try:
                strategy = await self.get_strategy_by_id(strategy_id)
                if not strategy:
                    results.append({
                        "id": strategy_id,
                        "success": False,
                        "error": "策略不存在"
                    })
                    continue
                
                # 更新策略
                update_data = {k: v for k, v in update.items() if k != "id"}
                updated_strategy = await self.update_strategy(strategy_id, update_data)
                
                results.append({
                    "id": strategy_id,
                    "success": True,
                    "strategy": updated_strategy
                })
                
            except Exception as e:
                results.append({
                    "id": strategy_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def export_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """导出策略"""
        try:
            strategy = await self.get_strategy_by_id(strategy_id)
            if not strategy:
                return {}
            
            export_data = {
                "name": strategy.name,
                "description": strategy.description,
                "type": strategy.type,
                "code": strategy.code,
                "config": strategy.config,
                "version": strategy.version,
                "author": strategy.author,
                "tags": strategy.tags,
                "exported_at": datetime.utcnow().isoformat()
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"导出策略失败: {e}")
            return {}
    
    async def import_strategy(self, import_data: Dict[str, Any]) -> Strategy:
        """导入策略"""
        try:
            # 检查策略名称是否已存在
            existing_strategy = await self.db.execute(
                select(Strategy).where(Strategy.name == import_data["name"])
            )
            if existing_strategy.scalar_one_or_none():
                raise ValueError(f"策略名称 {import_data['name']} 已存在")
            
            # 创建策略
            strategy_data = StrategyCreate(
                name=import_data["name"],
                description=import_data.get("description", ""),
                type=import_data.get("type", StrategyType.CUSTOM),
                code=import_data["code"],
                config=import_data.get("config", {}),
                version=import_data.get("version", "1.0.0"),
                author=import_data.get("author", ""),
                tags=import_data.get("tags", [])
            )
            
            strategy = await self.create_strategy(strategy_data)
            
            logger.info(f"策略导入成功: {strategy.name}")
            return strategy
            
        except Exception as e:
            logger.error(f"导入策略失败: {e}")
            raise
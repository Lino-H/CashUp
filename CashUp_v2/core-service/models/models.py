"""
数据模型定义
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, DECIMAL, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum as PyEnum

from ..database.connection import Base

class UserRole(PyEnum):
    """用户角色枚举"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"

class UserStatus(PyEnum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(100), nullable=True, comment="全名")
    role = Column(Enum(UserRole), default=UserRole.TRADER, comment="用户角色")
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, comment="用户状态")
    is_verified = Column(Boolean, default=False, comment="邮箱是否验证")
    avatar_url = Column(String(255), nullable=True, comment="头像URL")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    strategies = relationship("Strategy", back_populates="user")
    orders = relationship("Order", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Strategy(Base):
    """策略模型"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True, comment="策略ID")
    name = Column(String(100), nullable=False, comment="策略名称")
    description = Column(Text, nullable=True, comment="策略描述")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建用户ID")
    strategy_type = Column(String(50), nullable=False, comment="策略类型")
    config = Column(JSON, nullable=True, comment="策略配置")
    code = Column(Text, nullable=True, comment="策略代码")
    status = Column(String(20), default="draft", comment="策略状态")
    version = Column(String(20), default="1.0.0", comment="策略版本")
    is_public = Column(Boolean, default=False, comment="是否公开")
    tags = Column(JSON, nullable=True, comment="策略标签")
    performance_metrics = Column(JSON, nullable=True, comment="性能指标")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="strategies")
    backtests = relationship("Backtest", back_populates="strategy")
    orders = relationship("Order", back_populates="strategy")
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}')>"

class Backtest(Base):
    """回测模型"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True, comment="回测ID")
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="策略ID")
    name = Column(String(100), nullable=False, comment="回测名称")
    start_date = Column(DateTime, nullable=False, comment="开始时间")
    end_date = Column(DateTime, nullable=False, comment="结束时间")
    initial_capital = Column(DECIMAL(15, 2), nullable=False, comment="初始资金")
    final_capital = Column(DECIMAL(15, 2), nullable=True, comment="最终资金")
    total_return = Column(DECIMAL(10, 4), nullable=True, comment="总收益率")
    sharpe_ratio = Column(DECIMAL(10, 4), nullable=True, comment="夏普比率")
    max_drawdown = Column(DECIMAL(10, 4), nullable=True, comment="最大回撤")
    win_rate = Column(DECIMAL(10, 4), nullable=True, comment="胜率")
    profit_factor = Column(DECIMAL(10, 4), nullable=True, comment="盈利因子")
    total_trades = Column(Integer, nullable=True, comment="总交易次数")
    profitable_trades = Column(Integer, nullable=True, comment="盈利交易次数")
    status = Column(String(20), default="pending", comment="回测状态")
    config = Column(JSON, nullable=True, comment="回测配置")
    logs = Column(Text, nullable=True, comment="回测日志")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    strategy = relationship("Strategy", back_populates="backtests")
    
    def __repr__(self):
        return f"<Backtest(id={self.id}, name='{self.name}')>"

class Order(Base):
    """订单模型"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True, comment="订单ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True, comment="策略ID")
    exchange = Column(String(20), nullable=False, comment="交易所")
    symbol = Column(String(20), nullable=False, comment="交易对")
    side = Column(String(10), nullable=False, comment="买卖方向")
    type = Column(String(20), nullable=False, comment="订单类型")
    quantity = Column(DECIMAL(15, 8), nullable=False, comment="数量")
    price = Column(DECIMAL(15, 8), nullable=True, comment="价格")
    stop_price = Column(DECIMAL(15, 8), nullable=True, comment="止损价格")
    iceberg_quantity = Column(DECIMAL(15, 8), nullable=True, comment="冰山数量")
    status = Column(String(20), default="pending", comment="订单状态")
    exchange_order_id = Column(String(100), nullable=True, comment="交易所订单ID")
    filled_quantity = Column(DECIMAL(15, 8), default=0, comment="已成交数量")
    filled_price = Column(DECIMAL(15, 8), nullable=True, comment="成交价格")
    commission = Column(DECIMAL(15, 8), default=0, comment="手续费")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="orders")
    strategy = relationship("Strategy", back_populates="orders")
    
    def __repr__(self):
        return f"<Order(id={self.id}, symbol='{self.symbol}')>"

class Config(Base):
    """配置模型"""
    __tablename__ = "configs"
    
    id = Column(Integer, primary_key=True, index=True, comment="配置ID")
    key = Column(String(100), unique=True, nullable=False, comment="配置键")
    value = Column(JSON, nullable=False, comment="配置值")
    description = Column(Text, nullable=True, comment="配置描述")
    category = Column(String(50), default="general", comment="配置分类")
    is_system = Column(Boolean, default=False, comment="是否系统配置")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Config(id={self.id}, key='{self.key}')>"

class NotificationLog(Base):
    """通知日志模型"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="通知ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    type = Column(String(50), nullable=False, comment="通知类型")
    channel = Column(String(50), nullable=False, comment="通知渠道")
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    status = Column(String(20), default="pending", comment="通知状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    sent_at = Column(DateTime, nullable=True, comment="发送时间")
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, type='{self.type}')>"
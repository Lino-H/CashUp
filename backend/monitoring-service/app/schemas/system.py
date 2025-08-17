#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 系统数据模式

定义系统相关的API请求和响应数据模式
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class SystemStatusEnum(str, Enum):
    """系统状态枚举"""
    RUNNING = "running"
    STARTING = "starting"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class LogLevelEnum(str, Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BackupStatusEnum(str, Enum):
    """备份状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MaintenanceTaskStatusEnum(str, Enum):
    """维护任务状态枚举"""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class SecurityLevelEnum(str, Enum):
    """安全级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# 系统信息模式
class SystemInfoResponse(BaseModel):
    """系统信息响应模式"""
    system_name: str = Field(..., description="系统名称")
    version: str = Field(..., description="系统版本")
    build_number: str = Field(..., description="构建号")
    build_date: datetime = Field(..., description="构建日期")
    environment: str = Field(..., description="运行环境")
    hostname: str = Field(..., description="主机名")
    ip_address: str = Field(..., description="IP地址")
    port: int = Field(..., description="端口")
    pid: int = Field(..., description="进程ID")
    uptime: int = Field(..., description="运行时间(秒)")
    start_time: datetime = Field(..., description="启动时间")
    timezone: str = Field(..., description="时区")
    python_version: str = Field(..., description="Python版本")
    platform: str = Field(..., description="平台信息")
    architecture: str = Field(..., description="架构")
    cpu_count: int = Field(..., description="CPU核心数")
    memory_total: int = Field(..., description="总内存(字节)")
    disk_total: int = Field(..., description="总磁盘空间(字节)")
    dependencies: Dict[str, str] = Field(..., description="依赖版本")
    features: List[str] = Field(..., description="启用的功能")
    configuration: Dict[str, Any] = Field(..., description="配置信息")
    
    class Config:
        from_attributes = True


# 系统状态模式
class SystemStatusResponse(BaseModel):
    """系统状态响应模式"""
    status: SystemStatusEnum = Field(..., description="系统状态")
    health_score: float = Field(..., description="健康评分", ge=0, le=100)
    last_check: datetime = Field(..., description="最后检查时间")
    services_status: Dict[str, str] = Field(..., description="服务状态")
    database_status: str = Field(..., description="数据库状态")
    cache_status: str = Field(..., description="缓存状态")
    queue_status: str = Field(..., description="队列状态")
    storage_status: str = Field(..., description="存储状态")
    network_status: str = Field(..., description="网络状态")
    external_services: Dict[str, str] = Field(..., description="外部服务状态")
    active_connections: int = Field(..., description="活跃连接数")
    active_sessions: int = Field(..., description="活跃会话数")
    active_tasks: int = Field(..., description="活跃任务数")
    error_count: int = Field(..., description="错误数量")
    warning_count: int = Field(..., description="警告数量")
    alerts: List[Dict[str, Any]] = Field(..., description="活跃告警")
    maintenance_mode: bool = Field(..., description="是否维护模式")
    read_only_mode: bool = Field(..., description="是否只读模式")
    
    class Config:
        from_attributes = True


# 系统资源使用模式
class SystemResourcesResponse(BaseModel):
    """系统资源使用响应模式"""
    cpu_usage: float = Field(..., description="CPU使用率(%)", ge=0, le=100)
    cpu_load_1m: float = Field(..., description="1分钟负载")
    cpu_load_5m: float = Field(..., description="5分钟负载")
    cpu_load_15m: float = Field(..., description="15分钟负载")
    memory_usage: float = Field(..., description="内存使用率(%)", ge=0, le=100)
    memory_used: int = Field(..., description="已用内存(字节)")
    memory_available: int = Field(..., description="可用内存(字节)")
    memory_cached: int = Field(..., description="缓存内存(字节)")
    memory_buffers: int = Field(..., description="缓冲区内存(字节)")
    swap_usage: float = Field(..., description="交换空间使用率(%)", ge=0, le=100)
    swap_used: int = Field(..., description="已用交换空间(字节)")
    swap_total: int = Field(..., description="总交换空间(字节)")
    disk_usage: Dict[str, Dict[str, Any]] = Field(..., description="磁盘使用情况")
    network_io: Dict[str, Dict[str, int]] = Field(..., description="网络IO统计")
    disk_io: Dict[str, Dict[str, int]] = Field(..., description="磁盘IO统计")
    process_count: int = Field(..., description="进程数量")
    thread_count: int = Field(..., description="线程数量")
    file_descriptors: int = Field(..., description="文件描述符数量")
    open_files: int = Field(..., description="打开文件数量")
    tcp_connections: int = Field(..., description="TCP连接数")
    udp_connections: int = Field(..., description="UDP连接数")
    
    class Config:
        from_attributes = True


# 系统性能指标模式
class SystemPerformanceResponse(BaseModel):
    """系统性能指标响应模式"""
    response_time_avg: float = Field(..., description="平均响应时间(毫秒)")
    response_time_p50: float = Field(..., description="50%响应时间(毫秒)")
    response_time_p95: float = Field(..., description="95%响应时间(毫秒)")
    response_time_p99: float = Field(..., description="99%响应时间(毫秒)")
    throughput: float = Field(..., description="吞吐量(请求/秒)")
    requests_per_minute: int = Field(..., description="每分钟请求数")
    requests_per_hour: int = Field(..., description="每小时请求数")
    error_rate: float = Field(..., description="错误率(%)", ge=0, le=100)
    success_rate: float = Field(..., description="成功率(%)", ge=0, le=100)
    concurrent_users: int = Field(..., description="并发用户数")
    active_sessions: int = Field(..., description="活跃会话数")
    database_connections: int = Field(..., description="数据库连接数")
    cache_hit_rate: float = Field(..., description="缓存命中率(%)", ge=0, le=100)
    cache_miss_rate: float = Field(..., description="缓存未命中率(%)", ge=0, le=100)
    queue_size: int = Field(..., description="队列大小")
    queue_processing_time: float = Field(..., description="队列处理时间(毫秒)")
    gc_collections: int = Field(..., description="垃圾回收次数")
    gc_time: float = Field(..., description="垃圾回收时间(毫秒)")
    memory_leaks: int = Field(..., description="内存泄漏数量")
    deadlocks: int = Field(..., description="死锁数量")
    
    class Config:
        from_attributes = True


# 系统配置模式
class SystemConfigResponse(BaseModel):
    """系统配置响应模式"""
    config_version: str = Field(..., description="配置版本")
    last_updated: datetime = Field(..., description="最后更新时间")
    updated_by: Optional[str] = Field(None, description="更新者")
    environment: str = Field(..., description="环境")
    debug_mode: bool = Field(..., description="调试模式")
    log_level: LogLevelEnum = Field(..., description="日志级别")
    max_connections: int = Field(..., description="最大连接数")
    connection_timeout: int = Field(..., description="连接超时(秒)")
    request_timeout: int = Field(..., description="请求超时(秒)")
    session_timeout: int = Field(..., description="会话超时(秒)")
    cache_ttl: int = Field(..., description="缓存TTL(秒)")
    rate_limit: Dict[str, int] = Field(..., description="速率限制")
    security_settings: Dict[str, Any] = Field(..., description="安全设置")
    feature_flags: Dict[str, bool] = Field(..., description="功能开关")
    database_config: Dict[str, Any] = Field(..., description="数据库配置")
    cache_config: Dict[str, Any] = Field(..., description="缓存配置")
    queue_config: Dict[str, Any] = Field(..., description="队列配置")
    monitoring_config: Dict[str, Any] = Field(..., description="监控配置")
    notification_config: Dict[str, Any] = Field(..., description="通知配置")
    custom_settings: Dict[str, Any] = Field(..., description="自定义设置")
    
    class Config:
        from_attributes = True


class SystemConfigUpdate(BaseModel):
    """更新系统配置请求模式"""
    debug_mode: Optional[bool] = Field(None, description="调试模式")
    log_level: Optional[LogLevelEnum] = Field(None, description="日志级别")
    max_connections: Optional[int] = Field(None, description="最大连接数", ge=1, le=10000)
    connection_timeout: Optional[int] = Field(None, description="连接超时(秒)", ge=1, le=300)
    request_timeout: Optional[int] = Field(None, description="请求超时(秒)", ge=1, le=300)
    session_timeout: Optional[int] = Field(None, description="会话超时(秒)", ge=60, le=86400)
    cache_ttl: Optional[int] = Field(None, description="缓存TTL(秒)", ge=60, le=86400)
    rate_limit: Optional[Dict[str, int]] = Field(None, description="速率限制")
    security_settings: Optional[Dict[str, Any]] = Field(None, description="安全设置")
    feature_flags: Optional[Dict[str, bool]] = Field(None, description="功能开关")
    database_config: Optional[Dict[str, Any]] = Field(None, description="数据库配置")
    cache_config: Optional[Dict[str, Any]] = Field(None, description="缓存配置")
    queue_config: Optional[Dict[str, Any]] = Field(None, description="队列配置")
    monitoring_config: Optional[Dict[str, Any]] = Field(None, description="监控配置")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="通知配置")
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="自定义设置")


# 系统日志模式
class SystemLogResponse(BaseModel):
    """系统日志响应模式"""
    id: int = Field(..., description="日志ID")
    timestamp: datetime = Field(..., description="时间戳")
    level: LogLevelEnum = Field(..., description="日志级别")
    logger: str = Field(..., description="记录器名称")
    module: str = Field(..., description="模块名称")
    function: str = Field(..., description="函数名称")
    line_number: int = Field(..., description="行号")
    message: str = Field(..., description="日志消息")
    exception: Optional[str] = Field(None, description="异常信息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")
    
    class Config:
        from_attributes = True


class SystemLogQuery(BaseModel):
    """系统日志查询请求模式"""
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    level: Optional[LogLevelEnum] = Field(None, description="日志级别")
    logger: Optional[str] = Field(None, description="记录器名称")
    module: Optional[str] = Field(None, description="模块名称")
    message_contains: Optional[str] = Field(None, description="消息包含")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    has_exception: Optional[bool] = Field(None, description="是否有异常")
    limit: int = Field(100, description="限制数量", ge=1, le=1000)
    offset: int = Field(0, description="偏移量", ge=0)
    order_by: str = Field("timestamp", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")


# 系统备份模式
class SystemBackupBase(BaseModel):
    """系统备份基础模式"""
    name: str = Field(..., description="备份名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="备份描述", max_length=1000)
    backup_type: str = Field(..., description="备份类型", max_length=50)
    include_data: bool = Field(True, description="是否包含数据")
    include_config: bool = Field(True, description="是否包含配置")
    include_logs: bool = Field(False, description="是否包含日志")
    compression: bool = Field(True, description="是否压缩")
    encryption: bool = Field(False, description="是否加密")
    
    @validator('backup_type')
    def validate_backup_type(cls, v):
        """验证备份类型"""
        valid_types = ['full', 'incremental', 'differential', 'custom']
        if v not in valid_types:
            raise ValueError(f'Invalid backup type. Must be one of: {valid_types}')
        return v


class SystemBackupCreate(SystemBackupBase):
    """创建系统备份请求模式"""
    schedule: Optional[str] = Field(None, description="备份计划(cron表达式)")
    retention_days: int = Field(30, description="保留天数", ge=1, le=365)
    storage_location: Optional[str] = Field(None, description="存储位置")
    notification_channels: Optional[List[int]] = Field(None, description="通知渠道")


class SystemBackupResponse(SystemBackupBase):
    """系统备份响应模式"""
    id: int = Field(..., description="备份ID")
    status: BackupStatusEnum = Field(..., description="备份状态")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    checksum: Optional[str] = Field(None, description="校验和")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration: Optional[int] = Field(None, description="持续时间(秒)")
    error_message: Optional[str] = Field(None, description="错误消息")
    progress: float = Field(0.0, description="进度(%)", ge=0, le=100)
    schedule: Optional[str] = Field(None, description="备份计划")
    retention_days: int = Field(..., description="保留天数")
    storage_location: Optional[str] = Field(None, description="存储位置")
    
    class Config:
        from_attributes = True


# 系统维护任务模式
class SystemMaintenanceTaskBase(BaseModel):
    """系统维护任务基础模式"""
    name: str = Field(..., description="任务名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="任务描述", max_length=1000)
    task_type: str = Field(..., description="任务类型", max_length=50)
    command: Optional[str] = Field(None, description="执行命令", max_length=1000)
    script_path: Optional[str] = Field(None, description="脚本路径", max_length=500)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="任务参数")
    timeout: int = Field(3600, description="超时时间(秒)", ge=60, le=86400)
    
    @validator('task_type')
    def validate_task_type(cls, v):
        """验证任务类型"""
        valid_types = ['cleanup', 'optimization', 'backup', 'update', 'restart', 'custom']
        if v not in valid_types:
            raise ValueError(f'Invalid task type. Must be one of: {valid_types}')
        return v


class SystemMaintenanceTaskCreate(SystemMaintenanceTaskBase):
    """创建系统维护任务请求模式"""
    schedule: Optional[str] = Field(None, description="任务计划(cron表达式)")
    enabled: bool = Field(True, description="是否启用")
    run_immediately: bool = Field(False, description="是否立即执行")
    notification_channels: Optional[List[int]] = Field(None, description="通知渠道")
    dependencies: Optional[List[int]] = Field(None, description="依赖任务ID")
    retry_count: int = Field(3, description="重试次数", ge=0, le=10)
    retry_interval: int = Field(300, description="重试间隔(秒)", ge=60, le=3600)


class SystemMaintenanceTaskUpdate(BaseModel):
    """更新系统维护任务请求模式"""
    name: Optional[str] = Field(None, description="任务名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="任务描述", max_length=1000)
    command: Optional[str] = Field(None, description="执行命令", max_length=1000)
    script_path: Optional[str] = Field(None, description="脚本路径", max_length=500)
    parameters: Optional[Dict[str, Any]] = Field(None, description="任务参数")
    timeout: Optional[int] = Field(None, description="超时时间(秒)", ge=60, le=86400)
    schedule: Optional[str] = Field(None, description="任务计划(cron表达式)")
    enabled: Optional[bool] = Field(None, description="是否启用")
    notification_channels: Optional[List[int]] = Field(None, description="通知渠道")
    dependencies: Optional[List[int]] = Field(None, description="依赖任务ID")
    retry_count: Optional[int] = Field(None, description="重试次数", ge=0, le=10)
    retry_interval: Optional[int] = Field(None, description="重试间隔(秒)", ge=60, le=3600)


class SystemMaintenanceTaskResponse(SystemMaintenanceTaskBase):
    """系统维护任务响应模式"""
    id: int = Field(..., description="任务ID")
    status: MaintenanceTaskStatusEnum = Field(..., description="任务状态")
    schedule: Optional[str] = Field(None, description="任务计划")
    enabled: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_run_at: Optional[datetime] = Field(None, description="最后执行时间")
    next_run_at: Optional[datetime] = Field(None, description="下次执行时间")
    run_count: int = Field(0, description="执行次数")
    success_count: int = Field(0, description="成功次数")
    failure_count: int = Field(0, description="失败次数")
    avg_duration: Optional[float] = Field(None, description="平均持续时间(秒)")
    last_duration: Optional[float] = Field(None, description="最后持续时间(秒)")
    last_output: Optional[str] = Field(None, description="最后输出")
    last_error: Optional[str] = Field(None, description="最后错误")
    notification_channels: List[int] = Field(default_factory=list, description="通知渠道")
    dependencies: List[int] = Field(default_factory=list, description="依赖任务ID")
    retry_count: int = Field(..., description="重试次数")
    retry_interval: int = Field(..., description="重试间隔(秒)")
    
    class Config:
        from_attributes = True


# 系统安全模式
class SystemSecurityResponse(BaseModel):
    """系统安全状态响应模式"""
    security_level: SecurityLevelEnum = Field(..., description="安全级别")
    last_scan: datetime = Field(..., description="最后扫描时间")
    vulnerabilities: int = Field(..., description="漏洞数量")
    critical_vulnerabilities: int = Field(..., description="严重漏洞数量")
    high_vulnerabilities: int = Field(..., description="高危漏洞数量")
    medium_vulnerabilities: int = Field(..., description="中危漏洞数量")
    low_vulnerabilities: int = Field(..., description="低危漏洞数量")
    security_score: float = Field(..., description="安全评分", ge=0, le=100)
    failed_login_attempts: int = Field(..., description="失败登录尝试")
    blocked_ips: int = Field(..., description="被阻止的IP数量")
    active_sessions: int = Field(..., description="活跃会话数")
    suspicious_activities: int = Field(..., description="可疑活动数量")
    ssl_certificate_status: str = Field(..., description="SSL证书状态")
    ssl_certificate_expiry: Optional[datetime] = Field(None, description="SSL证书过期时间")
    firewall_status: str = Field(..., description="防火墙状态")
    antivirus_status: str = Field(..., description="防病毒状态")
    intrusion_detection_status: str = Field(..., description="入侵检测状态")
    backup_encryption_status: str = Field(..., description="备份加密状态")
    password_policy_compliance: float = Field(..., description="密码策略合规性(%)", ge=0, le=100)
    two_factor_auth_enabled: bool = Field(..., description="是否启用双因子认证")
    audit_log_enabled: bool = Field(..., description="是否启用审计日志")
    security_updates_available: int = Field(..., description="可用安全更新数量")
    compliance_status: Dict[str, str] = Field(..., description="合规状态")
    security_recommendations: List[str] = Field(..., description="安全建议")
    
    class Config:
        from_attributes = True


class SystemSecurityScanRequest(BaseModel):
    """系统安全扫描请求模式"""
    scan_type: str = Field(..., description="扫描类型")
    deep_scan: bool = Field(False, description="是否深度扫描")
    include_dependencies: bool = Field(True, description="是否包含依赖")
    async_scan: bool = Field(True, description="是否异步扫描")
    
    @validator('scan_type')
    def validate_scan_type(cls, v):
        """验证扫描类型"""
        valid_types = ['vulnerability', 'malware', 'configuration', 'compliance', 'full']
        if v not in valid_types:
            raise ValueError(f'Invalid scan type. Must be one of: {valid_types}')
        return v


# 系统操作请求模式
class SystemOperationRequest(BaseModel):
    """系统操作请求模式"""
    operation: str = Field(..., description="操作类型")
    force: bool = Field(False, description="是否强制执行")
    reason: Optional[str] = Field(None, description="操作原因", max_length=500)
    scheduled_time: Optional[datetime] = Field(None, description="计划执行时间")
    notification_channels: Optional[List[int]] = Field(None, description="通知渠道")
    
    @validator('operation')
    def validate_operation(cls, v):
        """验证操作类型"""
        valid_operations = ['restart', 'shutdown', 'cleanup', 'optimize', 'reset', 'maintenance']
        if v not in valid_operations:
            raise ValueError(f'Invalid operation. Must be one of: {valid_operations}')
        return v


class SystemOperationResponse(BaseModel):
    """系统操作响应模式"""
    operation_id: str = Field(..., description="操作ID")
    operation: str = Field(..., description="操作类型")
    status: str = Field(..., description="操作状态")
    started_at: datetime = Field(..., description="开始时间")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")
    progress: float = Field(0.0, description="进度(%)", ge=0, le=100)
    message: Optional[str] = Field(None, description="状态消息")
    
    class Config:
        from_attributes = True


# 为了兼容性，添加别名
SystemResourceResponse = SystemResourcesResponse

# 列表响应类
class SystemLogListResponse(BaseModel):
    """系统日志列表响应"""
    logs: List[SystemLogResponse]
    total: int
    page: int = 1
    size: int = 20
    pages: int

class SystemBackupListResponse(BaseModel):
    """系统备份列表响应"""
    backups: List[SystemBackupResponse]
    total: int
    page: int = 1
    size: int = 20
    pages: int

class SystemMaintenanceListResponse(BaseModel):
    """系统维护任务列表响应"""
    tasks: List[SystemMaintenanceTaskResponse]
    total: int
    page: int = 1
    size: int = 20
    pages: int

# 其他缺失的响应类
SystemMaintenanceResponse = SystemMaintenanceTaskResponse
SystemPerformanceResponse = SystemResourcesResponse
SystemCleanupRequest = SystemOperationRequest
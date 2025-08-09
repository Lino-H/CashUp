# CashUp 量化交易系统 - 项目规则文档

## 📋 项目概述

### 项目名称
**CashUp** - 专业量化交易系统

### 项目目标
构建一个功能完整、高性能、可扩展的量化交易平台，支持多交易所接入、策略管理、风险控制、回测分析和智能通知等核心功能。

### 核心价值
- 🎯 **专业性**：面向专业交易员和量化团队
- 🚀 **高性能**：支持高频交易和大规模数据处理
- 🔧 **可扩展**：微服务架构，易于扩展和维护
- 🛡️ **安全性**：多层安全防护，资金安全保障
- 📊 **智能化**：AI辅助决策和风险管理

## 🏗️ 技术架构

### 微服务架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Load Balancer │
│   (React)       │◄──►│   (Nginx)       │◄──►│   (Docker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
        │ User Service │ │Trading Svc│ │Strategy Svc │
        └──────────────┘ └───────────┘ └─────────────┘
                │               │               │
        ┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
        │Market Service│ │Order Svc  │ │Notification │
        └──────────────┘ └───────────┘ └─────────────┘
                │               │               │
        ┌───────▼──────┐ ┌─────▼─────┐
        │Config Service│ │Monitor Svc│
        └──────────────┘ └───────────┘
```

### 技术栈

#### 后端技术
- **语言**: Python 3.12+
- **框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL (主库) + Redis (缓存)
- **消息队列**: RabbitMQ
- **ORM**: SQLAlchemy 2.0
- **依赖管理**: UV (现代化 Python 包管理)
- **容器化**: Docker + Docker Compose

#### 前端技术
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **路由**: React Router
- **图表**: Recharts
- **UI组件**: Lucide React Icons

#### 外部集成
- **交易所**: Gate.io API
- **通知渠道**: 
  - QANotify
  - WXPusher
  - PushPlus
  - Telegram Bot
  - Email (SMTP)

## 🛠️ 开发环境配置

### 系统要求
- **操作系统**: macOS (主要开发环境)
- **Python**: 3.12+
- **Node.js**: 23.10.0 (LTS)
- **Docker**: 最新版本
- **Git**: 最新版本

### 环境初始化
```bash
# 1. 克隆项目
git clone git@github.com:Lino-H/CashUp.git
cd CashUp

# 2. 初始化 Python 环境
uv venv cashup
source cashup/bin/activate  # macOS/Linux

# 3. 安装前端依赖
cd frontend
npm install

# 4. 启动基础设施
docker-compose up -d postgres redis rabbitmq

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

### 虚拟环境管理
- **Python**: 使用 `uv` 管理，虚拟环境名称统一为 `cashup`
- **激活命令**: `source cashup/bin/activate`
- **每次开发前必须激活环境**

## 📁 项目结构

```
CashUp/
├── .trae/documents/          # 需求文档 (V1-V4)
├── backend/                  # 后端微服务
│   ├── user-service/         # 用户认证服务
│   ├── trading-service/      # 交易执行服务
│   ├── strategy-service/     # 策略管理服务
│   ├── market-service/       # 行情数据服务
│   ├── order-service/        # 订单管理服务
│   ├── notification-service/ # 通知服务
│   ├── config-service/       # 配置管理服务
│   └── monitoring-service/   # 监控服务
├── frontend/                 # React 前端应用
├── configs/                  # 配置文件
├── docker/                   # Docker 相关文件
├── docs/                     # 项目文档
├── scripts/                  # 工具脚本
├── docker-compose.yml        # 容器编排
├── Makefile                  # 构建脚本
└── PROJECT_RULES.md          # 本文件
```

### 微服务详情

| 服务名称 | 端口 | 职责 | 主要技术 |
|---------|------|------|----------|
| user-service | 8001 | 用户认证、权限管理 | FastAPI, JWT, Redis |
| trading-service | 8002 | 交易执行、订单管理 | FastAPI, CCXT, WebSocket |
| strategy-service | 8003 | 策略管理、回测引擎 | FastAPI, NumPy, Pandas |
| market-service | 8004 | 行情数据、技术指标 | FastAPI, WebSocket, Redis |
| order-service | 8005 | 订单生命周期管理 | FastAPI, PostgreSQL |
| notification-service | 8006 | 多渠道消息推送 | FastAPI, Celery, Templates |
| config-service | 8007 | 配置管理、参数调优 | FastAPI, Apollo |
| monitoring-service | 8008 | 系统监控、告警 | FastAPI, Prometheus |

## 🔄 开发工作流程

### 1. 功能开发流程
```bash
# 1. 激活环境
source cashup/bin/activate

# 2. 创建功能分支
git checkout -b feature/功能名称

# 3. 开发代码
# - 遵循代码规范
# - 添加必要注释
# - 编写单元测试

# 4. 测试验证
make test
make lint

# 5. 提交代码
git add .
git commit -m "feat: 功能描述"
git push origin feature/功能名称

# 6. 创建 Pull Request
```

### 2. 代码审查标准
- ✅ 代码符合 PEP 8 规范
- ✅ 函数和类有完整的文档字符串
- ✅ 关键逻辑有中文注释
- ✅ 单元测试覆盖率 > 80%
- ✅ 无安全漏洞和性能问题
- ✅ API 文档完整

### 3. 发布流程
```bash
# 1. 合并到主分支
git checkout main
git merge feature/功能名称

# 2. 更新版本号
# 编辑各服务的 pyproject.toml

# 3. 构建和测试
make build
make test-all

# 4. 部署
make deploy
```

## 🚀 常用命令和脚本

### Makefile 命令
```bash
# 环境管理
make setup          # 初始化开发环境
make clean          # 清理临时文件

# 开发调试
make dev            # 启动开发环境
make test           # 运行测试
make lint           # 代码检查
make format         # 代码格式化

# 构建部署
make build          # 构建所有服务
make deploy         # 部署到生产环境
make logs           # 查看日志
```

### 脚本工具
```bash
# 项目启动
./start_project.sh

# 环境配置
./setup_env.sh

# Docker 构建测试
./scripts/test-docker-build.sh

# UV 迁移测试
./scripts/test-uv-migration.sh
```

### Docker 命令
```bash
# 启动基础设施
docker-compose up -d postgres redis rabbitmq

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service-name]

# 重建服务
docker-compose build [service-name]
```

## 🏭 部署和运维规则

### 环境分类
- **开发环境** (dev): 本地开发调试
- **测试环境** (test): 功能测试验证
- **预生产环境** (staging): 生产前验证
- **生产环境** (prod): 正式运行环境

### 配置管理
- 使用环境变量管理配置
- 敏感信息存储在 `.env.production`
- 不同环境使用不同的配置文件
- 配置变更需要审批流程

### 监控告警
- **系统监控**: CPU、内存、磁盘、网络
- **应用监控**: 响应时间、错误率、吞吐量
- **业务监控**: 价格、交易量、盈亏、风险指标
- **告警渠道**: pushplus、wxpusher、qanotify、邮件、Telegram

### 备份策略
- **数据库**: 暂无计划
- **配置文件**: 版本控制管理
- **日志文件**: 保留 30 天，压缩存储
- **代码**: Git 仓库多地备份

## 📝 代码规范和最佳实践

### Python 代码规范
```python
# 1. 导入顺序
import os
import sys
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from sqlalchemy import Column, Integer, String

from .models import User
from .utils import hash_password

# 2. 函数文档字符串
def create_user(username: str, password: str) -> User:
    """
    创建新用户
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        User: 创建的用户对象
        
    Raises:
        ValueError: 用户名已存在
    """
    # 实现逻辑...
    pass

# 3. 类定义
class TradingStrategy:
    """交易策略基类"""
    
    def __init__(self, name: str, params: Dict):
        """初始化策略"""
        self.name = name
        self.params = params
        
    def execute(self) -> bool:
        """执行策略逻辑"""
        # 具体实现...
        return True
```

### React 代码规范
```typescript
// 1. 组件定义
interface UserCardProps {
  user: User;
  onEdit: (user: User) => void;
}

/**
 * 用户卡片组件
 */
export const UserCard: React.FC<UserCardProps> = ({ user, onEdit }) => {
  // 组件逻辑...
  
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      {/* JSX 内容 */}
    </div>
  );
};

// 2. 自定义 Hook
export const useUserData = (userId: string) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Hook 逻辑...
  
  return { user, loading, refetch };
};
```

### 数据库设计规范
```python
# 1. 模型定义
class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
```

### API 设计规范
```python
# 1. 路由定义
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    创建新用户
    
    - **username**: 用户名 (3-20字符)
    - **email**: 邮箱地址
    - **password**: 密码 (8-50字符)
    """
    # API 实现...
    pass

# 2. 响应模型
class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

## 🔒 安全规范

### 1. 认证授权
- 使用 JWT Token 进行身份认证
- 实施 RBAC (基于角色的访问控制)
- API 密钥定期轮换
- 敏感操作需要二次验证

### 2. 数据安全
- 密码使用 bcrypt 加密存储
- 敏感数据传输使用 HTTPS
- 数据库连接使用 SSL
- 定期进行安全审计

### 3. 代码安全
- 禁止硬编码密钥和密码
- 使用环境变量管理敏感配置
- 定期更新依赖包，修复安全漏洞
- 代码提交前进行安全扫描

## 📊 性能优化

### 1. 数据库优化
- 合理设计索引
- 使用连接池
- 读写分离
- 定期分析慢查询

### 2. 缓存策略
- Redis 缓存热点数据
- CDN 加速静态资源
- 浏览器缓存优化
- 数据库查询结果缓存

### 3. 代码优化
- 异步编程提高并发性能
- 合理使用数据结构和算法
- 避免 N+1 查询问题
- 定期进行性能测试

## 📈 监控指标

### 系统指标
- CPU 使用率 < 80%
- 内存使用率 < 85%
- 磁盘使用率 < 90%
- 网络延迟 < 100ms

### 应用指标
- API 响应时间 < 500ms
- 错误率 < 1%
- 可用性 > 99.9%
- 并发用户数监控

### 业务指标
- 交易成功率 > 99%
- 策略执行延迟 < 100ms
- 风险控制有效性
- 用户活跃度

## 🎯 当前开发重点

### 第一阶段 (当前)
1. ✅ 项目基础架构搭建
2. ✅ 微服务框架配置
3. ✅ Docker 环境优化
4. 🔄 用户认证系统开发
5. 🔄 基础 API 接口实现

### 第二阶段
1. 交易执行引擎
2. 策略管理系统
3. 行情数据接入
4. 风险控制模块

### 第三阶段
1. 回测引擎优化
2. 通知系统完善
3. 监控告警系统
4. 前端界面开发

> 💡 **提示**: 本文档是项目开发的重要参考，请在每次对话前查阅相关章节，确保了解当前项目状态和开发目标。
# CashUp 策略服务

## 概述

CashUp量化交易系统的策略服务，负责交易策略的管理、执行和监控。

## 功能特性

- 策略管理：创建、编辑、删除交易策略
- 策略执行：实时执行交易策略
- 策略监控：监控策略运行状态和性能
- 回测功能：历史数据回测验证策略效果
- 风险控制：策略风险管理和控制

## 技术栈

- FastAPI：Web框架
- SQLAlchemy：ORM
- PostgreSQL：数据库
- Redis：缓存
- Celery：异步任务队列
- NumPy/Pandas：数据处理
- TA-Lib：技术分析指标

## 快速开始

### 安装依赖

```bash
poetry install
```

### 运行服务

```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

### API文档

启动服务后访问：http://localhost:8000/docs

## 环境变量

- `DATABASE_URL`: 数据库连接URL
- `REDIS_URL`: Redis连接URL
- `JWT_SECRET_KEY`: JWT密钥

## 开发

### 代码格式化

```bash
poetry run black .
poetry run isort .
```

### 运行测试

```bash
poetry run pytest
```

### 类型检查

```bash
poetry run mypy .
```

## 许可证

MIT License
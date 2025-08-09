# CashUp 量化交易系统 Makefile

.PHONY: help install dev build up down logs clean test lint format

# 默认目标
help:
	@echo "CashUp 量化交易系统 - 可用命令:"
	@echo "  install     - 安装所有依赖"
	@echo "  dev         - 启动开发环境"
	@echo "  build       - 构建所有服务"
	@echo "  up          - 启动所有服务"
	@echo "  down        - 停止所有服务"
	@echo "  logs        - 查看服务日志"
	@echo "  clean       - 清理容器和镜像"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"

# 安装依赖
install:
	@echo "创建Python虚拟环境..."
	uv venv cashup
	@echo "激活虚拟环境并安装后端依赖..."
	source cashup/bin/activate && \
	for service in user-service trading-service strategy-service market-service notification-service order-service config-service monitoring-service; do \
		echo "安装 $$service 依赖..."; \
		uv pip install -r backend/$$service/requirements.txt; \
	done
	@echo "安装前端依赖..."
	cd frontend && npm install

# 启动开发环境
dev:
	@echo "启动基础服务..."
	docker-compose up -d postgres redis rabbitmq apollo
	@echo "等待服务启动..."
	sleep 10
	@echo "开发环境已启动，请手动启动各个服务"

# 构建所有服务
build:
	@echo "构建所有Docker镜像..."
	docker-compose build

# 启动所有服务
up:
	@echo "启动所有服务..."
	docker-compose up -d
	@echo "服务启动完成，访问 http://localhost:3000"

# 停止所有服务
down:
	@echo "停止所有服务..."
	docker-compose down

# 查看日志
logs:
	docker-compose logs -f

# 清理容器和镜像
clean:
	@echo "清理Docker容器和镜像..."
	docker-compose down -v --rmi all
	docker system prune -f

# 运行测试
test:
	@echo "运行后端测试..."
	source cashup/bin/activate && \
	for service in user-service trading-service strategy-service market-service notification-service order-service config-service monitoring-service; do \
		echo "测试 $$service..."; \
		cd backend/$$service && python -m pytest tests/ && cd ../..; \
	done
	@echo "运行前端测试..."
	cd frontend && npm test

# 代码检查
lint:
	@echo "检查后端代码..."
	source cashup/bin/activate && \
	for service in user-service trading-service strategy-service market-service notification-service order-service config-service monitoring-service; do \
		echo "检查 $$service..."; \
		cd backend/$$service && flake8 . && cd ../..; \
	done
	@echo "检查前端代码..."
	cd frontend && npm run lint

# 代码格式化
format:
	@echo "格式化后端代码..."
	source cashup/bin/activate && \
	for service in user-service trading-service strategy-service market-service notification-service order-service config-service monitoring-service; do \
		echo "格式化 $$service..."; \
		cd backend/$$service && black . && isort . && cd ../..; \
	done
	@echo "格式化前端代码..."
	cd frontend && npm run format

# 数据库迁移
migrate:
	@echo "运行数据库迁移..."
	source cashup/bin/activate && \
	for service in user-service trading-service strategy-service market-service notification-service order-service config-service monitoring-service; do \
		echo "迁移 $$service 数据库..."; \
		cd backend/$$service && alembic upgrade head && cd ../..; \
	done

# 重置数据库
reset-db:
	@echo "重置数据库..."
	docker-compose exec postgres psql -U cashup -d cashup -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	make migrate

# 查看服务状态
status:
	@echo "服务状态:"
	docker-compose ps
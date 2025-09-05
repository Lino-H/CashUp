# CashUp_v2 量化交易系统 Makefile

.PHONY: help install dev build up down logs clean test lint format migrate backup-db

# 默认目标
help:
	@echo "CashUp_v2 量化交易系统 - 可用命令:"
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
	@echo "  migrate     - 运行数据库迁移"
	@echo "  backup-db   - 备份数据库"
	@echo "  restore-db  - 恢复数据库"

# 安装依赖
install:
	@echo "创建Python虚拟环境..."
	uv venv cashup
	@echo "激活虚拟环境并安装依赖..."
	source cashup/bin/activate && \
		uv pip install -e ./core-service && \
		uv pip install -e ./trading-engine && \
		uv pip install -e ./strategy-platform && \
		uv pip install -e ./notification-service
	@echo "安装前端依赖..."
	cd frontend && npm install

# 启动开发环境
dev:
	@echo "启动基础服务..."
	docker-compose up -d postgres redis
	@echo "等待服务启动..."
	sleep 5
	@echo "启动后端服务..."
	source cashup/bin/activate && \
		uvicorn core-service.main:app --host 0.0.0.0 --port 8001 --reload & \
		uvicorn trading-engine.main:app --host 0.0.0.0 --port 8002 --reload & \
		uvicorn strategy-platform.main:app --host 0.0.0.0 --port 8003 --reload & \
		uvicorn notification-service.main:app --host 0.0.0.0 --port 8004 --reload &
	@echo "启动前端服务..."
	cd frontend && npm run dev &
	@echo "开发环境已启动"

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
		pytest core-service/tests/ && \
		pytest trading-engine/tests/ && \
		pytest strategy-platform/tests/ && \
		pytest notification-service/tests/
	@echo "运行前端测试..."
	cd frontend && npm test

# 代码检查
lint:
	@echo "检查后端代码..."
	source cashup/bin/activate && \
		flake8 core-service/ trading-engine/ strategy-platform/ notification-service/ && \
		mypy core-service/ trading-engine/ strategy-platform/ notification-service/
	@echo "检查前端代码..."
	cd frontend && npm run lint

# 代码格式化
format:
	@echo "格式化后端代码..."
	source cashup/bin/activate && \
		black core-service/ trading-engine/ strategy-platform/ notification-service/ && \
		isort core-service/ trading-engine/ strategy-platform/ notification-service/
	@echo "格式化前端代码..."
	cd frontend && npm run format

# 数据库迁移
migrate:
	@echo "运行数据库迁移..."
	docker-compose exec -T postgres psql -U cashup -d cashup -f scripts/init.sql

# 备份数据库
backup-db:
	@echo "备份数据库..."
	docker-compose exec postgres pg_dump -U cashup cashup > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
restore-db:
	@read -p "输入备份文件名: " backup_file; \
	docker-compose exec -T postgres psql -U cashup -d cashup < $$backup_file

# 重置数据库
reset-db:
	@echo "重置数据库..."
	docker-compose exec postgres psql -U cashup -d cashup -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	make migrate

# 查看服务状态
status:
	@echo "服务状态:"
	docker-compose ps

# 创建策略模板
create-strategy:
	@read -p "输入策略名称: " strategy_name; \
	read -p "输入策略类型 (basic/ma_cross/rsi/grid): " strategy_type; \
	python3 scripts/create_strategy.py $$strategy_name $$strategy_type

# 运行回测
run-backtest:
	@read -p "输入策略名称: " strategy_name; \
	read -p "输入交易对 (如: BTC/USDT): " symbol; \
	read -p "输入时间周期 (如: 1h): " timeframe; \
	read -p "输入开始日期 (YYYY-MM-DD): " start_date; \
	read -p "输入结束日期 (YYYY-MM-DD): " end_date; \
	python3 scripts/run_backtest.py $$strategy_name $$symbol $$timeframe $$start_date $$end_date

# 生成回测报告
generate-report:
	@read -p "输入策略名称: " strategy_name; \
	python3 scripts/generate_report.py $$strategy_name

# 部署到生产环境
deploy:
	@echo "部署到生产环境..."
	docker-compose -f docker-compose.prod.yml build
	docker-compose -f docker-compose.prod.yml up -d

# 查看系统资源使用情况
monitor:
	@echo "系统资源使用情况:"
	docker stats --no-stream

# 重启服务
restart:
	@echo "重启所有服务..."
	docker-compose restart

# 更新依赖
update-deps:
	@echo "更新Python依赖..."
	source cashup/bin/activate && \
		uv pip install -U -r core-service/requirements.txt && \
		uv pip install -U -r trading-engine/requirements.txt && \
		uv pip install -U -r strategy-platform/requirements.txt && \
		uv pip install -U -r notification-service/requirements.txt
	@echo "更新前端依赖..."
	cd frontend && npm update
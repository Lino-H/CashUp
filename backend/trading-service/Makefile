.PHONY: help install dev test lint format clean docker-build docker-run migrate upgrade downgrade

# 默认目标
help:
	@echo "CashUp Trading Service - 可用命令:"
	@echo ""
	@echo "开发环境:"
	@echo "  install     - 安装依赖"
	@echo "  dev         - 启动开发服务器"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理临时文件"
	@echo ""
	@echo "数据库:"
	@echo "  migrate     - 创建新的迁移文件"
	@echo "  upgrade     - 应用数据库迁移"
	@echo "  downgrade   - 回滚数据库迁移"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-run   - 运行Docker容器"
	@echo "  docker-up    - 启动Docker Compose"
	@echo "  docker-down  - 停止Docker Compose"
	@echo ""

# 安装依赖
install:
	@echo "安装Python依赖..."
	pip install -r requirements.txt
	@echo "依赖安装完成!"

# 启动开发服务器
dev:
	@echo "启动开发服务器..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
test:
	@echo "运行测试..."
	pytest -v --cov=app --cov-report=term-missing

# 运行快速测试（跳过慢测试）
test-fast:
	@echo "运行快速测试..."
	pytest -v -m "not slow" --cov=app --cov-report=term-missing

# 运行集成测试
test-integration:
	@echo "运行集成测试..."
	pytest -v -m "integration" --cov=app --cov-report=term-missing

# 代码检查
lint:
	@echo "运行代码检查..."
	flake8 app/
	mypy app/
	bandit -r app/

# 代码格式化
format:
	@echo "格式化代码..."
	black app/
	isort app/
	@echo "代码格式化完成!"

# 检查代码格式
format-check:
	@echo "检查代码格式..."
	black --check app/
	isort --check-only app/

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf dist/
	rm -rf build/
	@echo "清理完成!"

# 数据库迁移
migrate:
	@echo "创建数据库迁移文件..."
	@read -p "请输入迁移描述: " desc; \
	alembic revision --autogenerate -m "$$desc"

# 应用数据库迁移
upgrade:
	@echo "应用数据库迁移..."
	alembic upgrade head
	@echo "数据库迁移完成!"

# 回滚数据库迁移
downgrade:
	@echo "回滚数据库迁移..."
	alembic downgrade -1
	@echo "数据库回滚完成!"

# 查看迁移历史
history:
	@echo "查看迁移历史..."
	alembic history --verbose

# 查看当前版本
current:
	@echo "查看当前数据库版本..."
	alembic current

# 构建Docker镜像
docker-build:
	@echo "构建Docker镜像..."
	docker build -t cashup-trading-service .
	@echo "Docker镜像构建完成!"

# 运行Docker容器
docker-run:
	@echo "运行Docker容器..."
	docker run -p 8000:8000 --env-file .env cashup-trading-service

# 启动Docker Compose
docker-up:
	@echo "启动Docker Compose..."
	docker-compose up -d
	@echo "服务启动完成!"

# 停止Docker Compose
docker-down:
	@echo "停止Docker Compose..."
	docker-compose down
	@echo "服务停止完成!"

# 查看Docker Compose日志
docker-logs:
	@echo "查看服务日志..."
	docker-compose logs -f

# 重启Docker Compose服务
docker-restart:
	@echo "重启Docker Compose服务..."
	docker-compose restart
	@echo "服务重启完成!"

# 安全检查
security:
	@echo "运行安全检查..."
	bandit -r app/
	safety check

# 依赖检查
deps-check:
	@echo "检查依赖更新..."
	pip list --outdated

# 生成依赖文件
deps-freeze:
	@echo "生成依赖文件..."
	pip freeze > requirements.txt
	@echo "依赖文件已更新!"

# 初始化开发环境
init-dev:
	@echo "初始化开发环境..."
	make install
	make upgrade
	@echo "开发环境初始化完成!"

# 完整测试（包括代码检查）
test-all:
	@echo "运行完整测试..."
	make format-check
	make lint
	make test
	@echo "所有测试完成!"

# 生产环境部署检查
production-check:
	@echo "生产环境部署检查..."
	make format-check
	make lint
	make security
	make test
	@echo "生产环境检查完成!"

# 备份数据库
backup-db:
	@echo "备份数据库..."
	@read -p "请输入备份文件名 (不含扩展名): " name; \
	pg_dump $(DATABASE_URL) > backups/$$name.sql
	@echo "数据库备份完成!"

# 恢复数据库
restore-db:
	@echo "恢复数据库..."
	@read -p "请输入备份文件路径: " file; \
	psql $(DATABASE_URL) < $$file
	@echo "数据库恢复完成!"

# 查看项目统计
stats:
	@echo "项目代码统计:"
	@echo "Python文件数量:"
	@find app/ -name "*.py" | wc -l
	@echo "代码行数:"
	@find app/ -name "*.py" -exec wc -l {} + | tail -1
	@echo "测试文件数量:"
	@find tests/ -name "*.py" 2>/dev/null | wc -l || echo "0"

# 生成API文档
docs:
	@echo "生成API文档..."
	@echo "启动服务后访问: http://localhost:8000/docs"
	make dev
.PHONY: help install dev test lint format clean docker-build docker-run docker-stop logs

# 默认目标
help:
	@echo "CashUp配置管理服务 - 可用命令:"
	@echo ""
	@echo "开发命令:"
	@echo "  install     - 安装依赖"
	@echo "  dev         - 启动开发服务器"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理临时文件"
	@echo ""
	@echo "Docker命令:"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-run   - 运行Docker容器"
	@echo "  docker-stop  - 停止Docker容器"
	@echo "  docker-logs  - 查看Docker日志"
	@echo ""
	@echo "数据库命令:"
	@echo "  db-init     - 初始化数据库"
	@echo "  db-migrate  - 运行数据库迁移"
	@echo "  db-reset    - 重置数据库"

# 安装依赖
install:
	@echo "安装Python依赖..."
	pip install -r requirements.txt
	@echo "依赖安装完成!"

# 启动开发服务器
dev:
	@echo "启动开发服务器..."
	python main.py

# 运行测试
test:
	@echo "运行测试..."
	pytest

# 运行特定类型的测试
test-unit:
	@echo "运行单元测试..."
	pytest -m unit

test-integration:
	@echo "运行集成测试..."
	pytest -m integration

test-api:
	@echo "运行API测试..."
	pytest -m api

# 代码检查
lint:
	@echo "运行代码检查..."
	flake8 app/ main.py
	mypy app/ main.py

# 代码格式化
format:
	@echo "格式化代码..."
	black app/ main.py
	isort app/ main.py
	@echo "代码格式化完成!"

# 检查代码格式
format-check:
	@echo "检查代码格式..."
	black --check app/ main.py
	isort --check-only app/ main.py

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "*.log" -delete
	@echo "清理完成!"

# Docker命令
docker-build:
	@echo "构建Docker镜像..."
	docker build -t cashup/config-service:latest .
	@echo "Docker镜像构建完成!"

docker-run:
	@echo "启动Docker容器..."
	docker-compose up -d
	@echo "Docker容器启动完成!"

docker-stop:
	@echo "停止Docker容器..."
	docker-compose down
	@echo "Docker容器已停止!"

docker-logs:
	@echo "查看Docker日志..."
	docker-compose logs -f config-service

# 数据库命令
db-init:
	@echo "初始化数据库..."
	psql -U postgres -f init.sql
	@echo "数据库初始化完成!"

db-reset:
	@echo "重置数据库..."
	docker-compose exec postgres psql -U cashup -d cashup_config -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	docker-compose exec postgres psql -U cashup -d cashup_config -f /docker-entrypoint-initdb.d/init.sql
	@echo "数据库重置完成!"

# 健康检查
health:
	@echo "检查服务健康状态..."
	curl -f http://localhost:8003/health || echo "服务不可用"

# 查看API文档
docs:
	@echo "打开API文档..."
	open http://localhost:8003/docs

# 生成requirements.txt
freeze:
	@echo "生成requirements.txt..."
	pip freeze > requirements.txt
	@echo "requirements.txt已更新!"

# 安全检查
security:
	@echo "运行安全检查..."
	bandit -r app/
	safety check

# 性能测试
perf:
	@echo "运行性能测试..."
	locust -f tests/performance/locustfile.py --host=http://localhost:8003

# 代码覆盖率报告
coverage:
	@echo "生成代码覆盖率报告..."
	pytest --cov=app --cov-report=html
	open htmlcov/index.html

# 全面检查（格式、检查、测试）
check-all: format-check lint test
	@echo "所有检查完成!"

# 部署准备
deploy-prep: clean format-check lint test docker-build
	@echo "部署准备完成!"

# 开发环境设置
dev-setup: install
	@echo "设置开发环境..."
	cp .env.example .env
	@echo "请编辑 .env 文件配置环境变量"
	@echo "然后运行 'make docker-run' 启动依赖服务"
	@echo "最后运行 'make dev' 启动开发服务器"

# 生产环境部署
prod-deploy:
	@echo "部署到生产环境..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "生产环境部署完成!"

# 监控
monitor:
	@echo "查看服务监控..."
	docker-compose logs -f

# 备份数据库
db-backup:
	@echo "备份数据库..."
	docker-compose exec postgres pg_dump -U cashup cashup_config > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "数据库备份完成!"

# 恢复数据库
db-restore:
	@echo "恢复数据库..."
	@read -p "请输入备份文件名: " backup_file; \
	docker-compose exec -T postgres psql -U cashup -d cashup_config < $$backup_file
	@echo "数据库恢复完成!"
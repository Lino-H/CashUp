# 多阶段构建 - 构建阶段
FROM python:3.11-alpine as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    curl

# 安装uv包管理器
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv

# 复制依赖文件
COPY market-service/pyproject.toml ./

# 创建虚拟环境并安装依赖
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache-dir .

# 运行阶段
FROM python:3.11-alpine as runtime

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# 安装运行时依赖
RUN apk add --no-cache \
    libpq \
    curl \
    && adduser -D -s /bin/sh app

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制共享代码和应用代码
COPY --chown=app:app shared ./shared
COPY --chown=app:app market-service ./

# 创建logs目录并设置权限
RUN mkdir -p logs && chown -R app:app logs

# 切换到非root用户
USER app

# 暴露端口
EXPOSE 8004

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖和uv
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# 将uv添加到PATH
ENV PATH="/root/.cargo/bin:$PATH"

# 复制项目文件（优先复制依赖文件，利用 Docker 缓存）
COPY pyproject.toml ./

# 使用uv安装依赖（--no-cache-dir 减少镜像体积）
RUN uv venv cashup && \
    . cashup/bin/activate && \
    uv pip install --no-cache-dir .

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["/bin/bash", "-c", "source cashup/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"]
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制共享库
COPY shared ./shared

# 复制requirements文件
COPY exchange-service/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY exchange-service/app ./app

# 设置Python路径
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8003

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
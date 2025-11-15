# AI Agent服务 Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY ../../requirements.txt .
COPY requirements-ai.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-ai.txt

# 复制应用代码
COPY app/ ./app/
COPY ../../shared/ ./shared/

# 设置Python路径
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8004

# 启动命令
CMD ["python", "-m", "app.main"]
FROM python:3.9-slim
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY bot/ ./bot/
COPY web/ ./web/
COPY start.sh .

# 创建文件存储目录并设置权限
RUN mkdir -p /app/bot/files && chmod 755 /app/bot/files

# 确保启动脚本可执行
RUN chmod +x start.sh

# 暴露Web服务端口
EXPOSE 5000

# 启动命令
CMD ["./start.sh"]
    
# 使用官方Python镜像作为基础
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY bot/ ./bot/
COPY web/ ./web/

# 创建数据目录并设置权限
RUN mkdir -p /app/bot/files && chmod 755 /app/bot/files

# 暴露Web端口
EXPOSE 5000

# 启动脚本
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
    
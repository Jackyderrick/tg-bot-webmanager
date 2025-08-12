#!/bin/bash
# 启动脚本：同时运行机器人和Web服务

# 确保配置文件存在
if [ ! -f /app/bot/config.json ]; then
    echo "初始化默认配置文件..."
    cp /app/bot/config.json /app/bot/config.json  # 复制默认配置
fi

# 后台启动Telegram机器人
python /app/bot/bot.py &

# 启动Flask Web服务（使用Gunicorn生产服务器）
gunicorn -w 4 -b 0.0.0.0:5000 "web.app:app"
    
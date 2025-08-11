#!/bin/bash
set -e

# 启动机器人和Web服务
echo "Starting Telegram bot..."
python -u bot/bot.py &

echo "Starting Web management interface..."
python -u web/app.py &

# 等待所有后台进程
wait -n

# 退出状态码
exit $?
    
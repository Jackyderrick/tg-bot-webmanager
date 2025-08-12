from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    Filters, CallbackContext, CallbackQueryHandler
)
import logging
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import uuid

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

# 机器人Token（从环境变量获取）
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8148383405:AAEZNgccPDWyAnwbzK-23NrcTF0lfeaVi8Y')

# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.start()


def load_config():
    """加载配置文件，添加错误处理"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        # 返回默认配置
        return {
            "responses": {
                "选项1": "您选择了选项1，这是对应的回复内容～",
                "选项2": "您选择了选项2，这是对应的回复内容～",
                "选项3": "您选择了选项3，这是对应的回复内容～"
            },
            "keyboard_buttons": [
                ["选项1", "选项2"],
                ["选项3", "获取文件"],
                ["隐藏键盘"]
            ],
            "file_to_send": "example_file.txt",
            "file_caption": "这是您请求的文件",
            "users": [],
            "notifications": {
                "pending": [],
                "sent": []
            }
        }


def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存配置文件失败: {str(e)}")


def add_user(user_id):
    """添加用户到数据库（去重）"""
    config = load_config()
    if user_id not in config['users']:
        config['users'].append(user_id)
        save_config(config)
        logger.info(f"添加新用户: {user_id}")


def create_example_file(file_path):
    """创建示例文件（确保文件存在）"""
    try:
        Path(file_path).write_text("这是机器人自动生成的示例文件内容", encoding="utf-8")
        logger.info(f"已创建示例文件: {file_path}")
    except Exception as e:
        logger.error(f"创建示例文件失败: {str(e)}")


def start(update: Update, context: CallbackContext) -> None:
    """发送欢迎消息并显示自定义键盘"""
    try:
        config = load_config()
        user = update.effective_user
        if user:
            # 添加用户到数据库
            add_user(user.id)
            update.message.reply_html(
                f"你好 {user.mention_html()}！\n点击下方键盘按钮使用功能～"
            )
        
        # 显示自定义键盘
        reply_markup = ReplyKeyboardMarkup(
            config['keyboard_buttons'],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        update.message.reply_text("请选择操作：", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"处理start命令时出错: {str(e)}")
        update.message.reply_text("初始化失败，请稍后重试")


def handle_keyboard_click(update: Update, context: CallbackContext) -> None:
    """处理键盘按钮点击"""
    try:
        # 添加用户到数据库
        user = update.effective_user
        if user:
            add_user(user.id)
            
        config = load_config()
        user_message = update.message.text.strip()
        
        # 处理文本回复
        if user_message in config['responses']:
            update.message.reply_text(config['responses'][user_message])
        
        # 处理文件发送
        elif user_message == "获取文件":
            try:
                file_path = os.path.join(os.path.dirname(__file__), config['file_to_send'])
                if not os.path.exists(file_path):
                    create_example_file(file_path)
                
                if os.path.getsize(file_path) > 50 * 1024 * 1024:  # 50MB限制
                    update.message.reply_text("文件过大，无法发送（限制50MB）")
                    return
                    
                update.message.reply_document(
                    document=open(file_path, 'rb'),
                    caption=config['file_caption']
                )
            except Exception as e:
                logger.error(f"发送文件失败: {str(e)}")
                update.message.reply_text(f"发送文件失败：{str(e)}")
        
        # 处理隐藏键盘
        elif user_message == "隐藏键盘":
            update.message.reply_text(
                "已隐藏键盘，发送 /start 可重新显示～",
                reply_markup=ReplyKeyboardRemove()
            )
        
        # 其他消息
        else:
            update.message.reply_text("请点击键盘按钮操作，或发送 /start 重新显示键盘～")
    except Exception as e:
        logger.error(f"处理键盘点击时出错: {str(e)}")
        update.message.reply_text("操作失败，请稍后重试")


def button_callback(update: Update, context: CallbackContext) -> None:
    """处理Inline按钮点击，添加内容变化检查"""
    try:
        query = update.callback_query
        query.answer()  # 显示"正在处理"提示
        
        callback_data = query.data
        config = load_config()
        
        # 获取新回复内容
        new_text = config['responses'].get(callback_data, "未知选项，请重试~")
        
        # 检查当前消息内容是否与新内容相同
        current_text = query.message.text
        if new_text == current_text:
            # 内容相同，不执行更新，仅提示
            query.answer(text="内容未变化", show_alert=False)
            return
        
        # 内容不同，执行更新
        query.edit_message_text(text=new_text)
    except Exception as e:
        logger.error(f"处理按钮回调时出错: {str(e)}")
        # 根据错误类型提供不同提示
        if "not modified" in str(e).lower():
            query.answer(text="内容未变化", show_alert=False)
        else:
            query.answer(text="操作失败，请重试", show_alert=True)


def error_handler(update: Update, context: CallbackContext) -> None:
    """错误处理函数"""
    logger.error(f'Update {update} caused error {context.error}')
    # 尝试向用户发送错误提示
    if update and update.effective_message:
        try:
            update.effective_message.reply_text("操作过程中出现错误，请稍后重试")
        except:
            pass


# 通知相关功能
def send_notification_to_users(context: CallbackContext, message: str, notification_id: str = None):
    """向所有用户发送通知"""
    config = load_config()
    success_count = 0
    fail_count = 0
    
    for user_id in config['users']:
        try:
            context.bot.send_message(chat_id=user_id, text=message)
            success_count += 1
        except Exception as e:
            logger.error(f"向用户 {user_id} 发送通知失败: {str(e)}")
            fail_count += 1
    
    logger.info(f"通知发送完成: 成功 {success_count} 人, 失败 {fail_count} 人")
    
    # 更新通知状态为已发送
    if notification_id:
        config = load_config()
        # 查找并移动通知到已发送列表
        for i, notification in enumerate(config['notifications']['pending']):
            if notification['id'] == notification_id:
                notification['status'] = 'sent'
                notification['sent_time'] = datetime.now().isoformat()
                config['notifications']['sent'].append(notification)
                del config['notifications']['pending'][i]
                save_config(config)
                break


def send_immediate_notification(message: str):
    """立即发送通知"""
    try:
        # 使用Updater获取bot上下文发送消息
        updater = Updater(TOKEN)
        context = updater.bot
        send_notification_to_users(CallbackContext(updater.dispatcher), message)
        
        # 记录已发送通知
        config = load_config()
        config['notifications']['sent'].append({
            'id': str(uuid.uuid4()),
            'message': message,
            'type': 'immediate',
            'status': 'sent',
            'sent_time': datetime.now().isoformat()
        })
        save_config(config)
        return True, "通知已立即发送"
    except Exception as e:
        logger.error(f"立即发送通知失败: {str(e)}")
        return False, f"发送失败: {str(e)}"


def schedule_notification(message: str, scheduled_time: datetime):
    """定时发送通知"""
    try:
        notification_id = str(uuid.uuid4())
        
        # 计算与当前时间的差值（秒）
        now = datetime.now()
        delay = (scheduled_time - now).total_seconds()
        
        if delay <= 0:
            return False, "定时时间必须晚于当前时间"
        
        # 使用调度器安排任务
        job = scheduler.add_job(
            send_notification_to_users,
            'date',
            run_date=scheduled_time,
            args=[CallbackContext(Updater(TOKEN).dispatcher), message, notification_id]
        )
        
        # 保存定时通知到配置
        config = load_config()
        config['notifications']['pending'].append({
            'id': notification_id,
            'message': message,
            'type': 'scheduled',
            'status': 'pending',
            'scheduled_time': scheduled_time.isoformat(),
            'job_id': job.id
        })
        save_config(config)
        
        return True, f"通知已安排在 {scheduled_time} 发送"
    except Exception as e:
        logger.error(f"安排定时通知失败: {str(e)}")
        return False, f"安排失败: {str(e)}"


def cancel_scheduled_notification(notification_id: str):
    """取消定时通知"""
    try:
        config = load_config()
        # 查找通知
        for i, notification in enumerate(config['notifications']['pending']):
            if notification['id'] == notification_id:
                # 从调度器中移除任务
                scheduler.remove_job(notification['job_id'])
                
                # 从配置中移除
                del config['notifications']['pending'][i]
                save_config(config)
                return True, "通知已取消"
        
        return False, "未找到该通知"
    except Exception as e:
        logger.error(f"取消通知失败: {str(e)}")
        return False, f"取消失败: {str(e)}"


def load_notifications():
    """加载所有通知（包括待发送和已发送）"""
    config = load_config()
    return {
        'pending': config['notifications']['pending'],
        'sent': config['notifications']['sent']
    }


def main() -> None:
    """启动机器人"""
    try:
        config = load_config()
        # 确保示例文件存在
        file_path = os.path.join(os.path.dirname(__file__), config['file_to_send'])
        if not os.path.exists(file_path):
            create_example_file(file_path)
        
        # 初始化Updater
        updater = Updater(TOKEN)
        dp = updater.dispatcher
        
        # 注册处理器
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_keyboard_click))
        dp.add_handler(CallbackQueryHandler(button_callback))
        dp.add_error_handler(error_handler)
        
        logger.info("机器人已启动")
        updater.start_polling()
        updater.idle()
    except Exception as e:
        logger.critical(f"机器人启动失败: {str(e)}", exc_info=True)


if __name__ == '__main__':
    main()
    
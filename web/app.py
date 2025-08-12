import os
import sys
# 解决模块导入问题
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime
from bot.bot import (
    load_config, save_config, 
    send_immediate_notification, 
    schedule_notification, 
    cancel_scheduled_notification,
    load_notifications
)
from flask_basicauth import BasicAuth

app = Flask(__name__)
# 在 web/app.py 顶部修改导入部分
from bot.bot import (
    send_immediate_notification, 
    schedule_notification, 
    cancel_scheduled_notification,
    load_notifications  # 现在这个函数已存在
)
# 配置基础认证
app.config['BASIC_AUTH_USERNAME'] = os.getenv('ADMIN_USERNAME', 'admin')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('ADMIN_PASSWORD', 'password')  # 建议修改为强密码
basic_auth = BasicAuth(app)

# 机器人文件存放目录
BOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot')
# 允许的文件上传类型和大小限制
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB


def allowed_file(filename):
    """检查文件是否为允许的类型"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
@basic_auth.required
def index():
    """管理页面"""
    config = load_config()
    notifications = load_notifications()
    # 获取机器人目录下的文件列表
    files = []
    if os.path.exists(BOT_DIR):
        files = [f for f in os.listdir(BOT_DIR) if os.path.isfile(os.path.join(BOT_DIR, f))]
    return render_template('index.html', 
                          config=config, 
                          files=files,
                          notifications=notifications)


@app.route('/update-responses', methods=['POST'])
@basic_auth.required
def update_responses():
    """更新回复内容"""
    config = load_config()
    config['responses'] = request.json['responses']
    save_config(config)
    return jsonify({'status': 'success'})


@app.route('/update-keyboard', methods=['POST'])
@basic_auth.required
def update_keyboard():
    """更新更新键盘按钮"""
    config = load_config()
    config['keyboard_buttons'] = request.json['keyboard']
    save_config(config)
    return jsonify({'status': 'success'})


@app.route('/update-file-settings', methods=['POST'])
@basic_auth.required
def update_file_settings():
    """更新文件设置"""
    config = load_config()
    config['file_to_send'] = request.form['file_to_send']
    config['file_caption'] = request.form['file_caption']
    save_config(config)
    return redirect('/')


@app.route('/upload-file', methods=['POST'])
@basic_auth.required
def upload_file():
    """上传文件到机器人目录"""
    if 'file' not in request.files:
        return redirect('/')
    
    file = request.files['file']
    if file.filename == '':
        return redirect('/')
    
    if file and allowed_file(file.filename):
        file_path = os.path.join(BOT_DIR, file.filename)
        file.save(file_path)
    return redirect('/')


@app.route('/send-notification', methods=['POST'])
@basic_auth.required
def send_notification():
    """发送通知（立即或定时）"""
    message = request.form['message'].strip()
    if not message:
        return jsonify({'status': 'error', 'message': '通知内容不能为空'})
    
    notification_type = request.form['notification_type']
    
    if notification_type == 'immediate':
        success, msg = send_immediate_notification(message)
        return jsonify({'status': 'success' if success else 'error', 'message': msg})
    else:
        # 处理定时通知
        try:
            time_str = request.form['scheduled_time']
            # 解析时间字符串 (YYYY-MM-DDThh:mm)
            scheduled_time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M')
            success, msg = schedule_notification(message, scheduled_time)
            return jsonify({'status': 'success' if success else 'error', 'message': msg})
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'时间格式错误: {str(e)}'})


@app.route('/cancel-notification/<notification_id>', methods=['POST'])
@basic_auth.required
def cancel_notification(notification_id):
    """取消定时通知"""
    success, msg = cancel_scheduled_notification(notification_id)
    return jsonify({'status': 'success' if success else 'error', 'message': msg})


if __name__ == '__main__':
    # 确保bot目录存在
    if not os.path.exists(BOT_DIR):
        os.makedirs(BOT_DIR)
    app.run(host='0.0.0.0', port=5000, debug=False)
    
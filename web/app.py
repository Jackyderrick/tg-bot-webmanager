from flask import Flask, render_template, request, redirect, jsonify, abort
import os
import json
from pathlib import Path
import traceback
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 限制上传文件大小为20MB

# 配置文件路径（与机器人共享）
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot', 'config.json')
# 机器人文件存放目录
BOT_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot')

# 确保目录存在
Path(BOT_FILES_DIR).mkdir(parents=True, exist_ok=True)


def get_valid_config():
    """获取有效的配置，确保配置结构正确"""
    try:
        config = load_config()
        # 验证基本结构
        required_keys = ['responses', 'keyboard_buttons', 'file_to_send', 'file_caption']
        for key in required_keys:
            if key not in config:
                config[key] = {} if key == 'responses' else [] if key == 'keyboard_buttons' else ''
        return config
    except Exception as e:
        app.logger.error(f"获取配置失败: {str(e)}")
        return {
            'responses': {},
            'keyboard_buttons': [],
            'file_to_send': '',
            'file_caption': ''
        }


def load_config():
    """加载配置文件"""
    if not os.path.exists(CONFIG_PATH):
        return {}
        
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    """管理页面，增加错误处理"""
    try:
        config = get_valid_config()
        # 获取机器人目录下的文件列表（用于文件选择）
        files = []
        if os.path.exists(BOT_FILES_DIR):
            files = [f for f in os.listdir(BOT_FILES_DIR) 
                    if os.path.isfile(os.path.join(BOT_FILES_DIR, f)) 
                    and not f.startswith('.')]  # 排除隐藏文件
        return render_template('index.html', config=config, files=files)
    except Exception as e:
        app.logger.error(f"加载管理页面失败: {str(e)}")
        return "加载页面失败，请稍后重试", 500


@app.route('/update-responses', methods=['POST'])
def update_responses():
    """更新回复内容，增加数据验证"""
    try:
        if not request.is_json:
            return jsonify({'status': 'error', 'message': '无效的数据格式'}), 400
            
        data = request.get_json()
        if 'responses' not in data or not isinstance(data['responses'], dict):
            return jsonify({'status': 'error', 'message': '无效的回复数据'}), 400
            
        config = get_valid_config()
        config['responses'] = data['responses']
        save_config(config)
        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.error(f"更新回复内容失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '保存失败'}), 500


@app.route('/update-keyboard', methods=['POST'])
def update_keyboard():
    """更新键盘按钮，增加数据验证"""
    try:
        if not request.is_json:
            return jsonify({'status': 'error', 'message': '无效的数据格式'}), 400
            
        data = request.get_json()
        if 'keyboard' not in data or not isinstance(data['keyboard'], list):
            return jsonify({'status': 'error', 'message': '无效的键盘数据'}), 400
            
        # 验证键盘结构
        valid_keyboard = []
        for row in data['keyboard']:
            if isinstance(row, list):
                valid_row = [str(item).strip() for item in row if item and str(item).strip()]
                if valid_row:
                    valid_keyboard.append(valid_row)
        
        config = get_valid_config()
        config['keyboard_buttons'] = valid_keyboard
        save_config(config)
        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.error(f"更新键盘按钮失败: {str(e)}")
        return jsonify({'status': 'error', 'message': '保存失败'}), 500


@app.route('/update-file-settings', methods=['POST'])
def update_file_settings():
    """更新文件设置"""
    try:
        config = get_valid_config()
        config['file_to_send'] = request.form.get('file_to_send', '').strip()
        config['file_caption'] = request.form.get('file_caption', '').strip()
        save_config(config)
        return redirect('/')
    except Exception as e:
        app.logger.error(f"更新文件设置失败: {str(e)}")
        return "保存文件设置失败，请稍后重试", 500


@app.route('/upload-file', methods=['POST'])
def upload_file():
    """上传文件到机器人目录，增加文件验证"""
    try:
        if 'file' not in request.files:
            return redirect('/')
        
        file = request.files['file']
        if file.filename == '':
            return redirect('/')
        
        if file:
            # 安全的文件名处理
            filename = Path(file.filename).name  # 移除路径信息
            # 禁止上传的文件类型
            forbidden_extensions = ['.py', '.php', '.exe', '.sh', '.bat']
            if any(filename.endswith(ext) for ext in forbidden_extensions):
                return "不允许上传该类型的文件", 403
                
            file_path = os.path.join(BOT_FILES_DIR, filename)
            file.save(file_path)
        return redirect('/')
    except Exception as e:
        app.logger.error(f"文件上传失败: {str(e)}")
        return "文件上传失败，请稍后重试", 500


if __name__ == '__main__':
    # 生产环境使用时应设置debug=False
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    
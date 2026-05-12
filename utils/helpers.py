import os
import json
import shutil
from datetime import datetime

from utils.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CONFIG_PATH = os.path.join(DATA_DIR, 'config.json')
BOT_DIR = os.path.join(BASE_DIR, 'bot_data')


def get_greeting():
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return '早上好'
    elif 12 <= hour < 18:
        return '中午好'
    else:
        return '晚上好'


def format_size(size_bytes):
    if size_bytes < 1024:
        return f'{size_bytes}B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.2f}KB'
    elif size_bytes < 1024 * 1024 * 1024:
        return f'{size_bytes / (1024 * 1024):.2f}MB'
    else:
        return f'{size_bytes / (1024 * 1024 * 1024):.2f}GB'


def parse_size_to_bytes(size_str):
    size_str = size_str.strip().upper()
    multipliers = {'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}
    for unit, multiplier in multipliers.items():
        if size_str.endswith(unit):
            try:
                return float(size_str[:-len(unit)]) * multiplier
            except ValueError:
                return 0
    try:
        return float(size_str)
    except ValueError:
        return 0


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return get_default_config()
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'加载配置文件失败: {e}')
        return get_default_config()


def save_config(config):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_default_config():
    return {
        'proxy': {
            'enabled': False,
            'host': '127.0.0.1',
            'port': 10808,
            'type': 'http'
        },
        'storage': {
            'default_capacity_gb': 1.0,
            'whitelist_mode': False,
            'blacklist_mode': True,
            'allowed_users': [],
            'blocked_users': []
        },
        'admins': [],
        'bots': [],
        'theme': {
            'primary_color': '#2196F3',
            'primary_dark': '#1976D2',
            'background_color': '#F5F5F5',
            'card_color': '#FFFFFF',
            'text_color': '#333333',
            'text_secondary': '#666666',
            'success_color': '#4CAF50',
            'warning_color': '#FF9800',
            'danger_color': '#F44336',
            'sidebar_color': '#1E1E2D',
            'sidebar_text': '#A2A3B7',
            'sidebar_active': '#FFFFFF',
            'border_radius': '8px',
            'font_family': 'Microsoft YaHei'
        }
    }


def get_bot_file_dir(user_id):
    user_dir = os.path.join(BOT_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def calculate_dir_size(directory):
    total = 0
    if not os.path.exists(directory):
        return 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def calculate_user_usage(user_id):
    user_dir = get_bot_file_dir(user_id)
    return calculate_dir_size(user_dir)


def calculate_total_usage():
    if not os.path.exists(BOT_DIR):
        return 0
    return calculate_dir_size(BOT_DIR)


def get_user_files(user_id):
    user_dir = get_bot_file_dir(user_id)
    if not os.path.exists(user_dir):
        return []
    files = []
    for f in os.listdir(user_dir):
        fpath = os.path.join(user_dir, f)
        if os.path.isfile(fpath):
            files.append({
                'name': f,
                'size': os.path.getsize(fpath),
                'path': fpath
            })
    return files


def delete_user_file(user_id, filename):
    user_dir = get_bot_file_dir(user_id)
    fpath = os.path.join(user_dir, filename)
    if os.path.exists(fpath):
        os.remove(fpath)
        return True
    return False

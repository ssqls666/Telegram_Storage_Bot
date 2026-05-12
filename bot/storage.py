import os
import json
import asyncio
import aiofiles
from datetime import datetime

from utils.logger import logger
from utils.helpers import get_bot_file_dir, calculate_user_usage, get_user_files, delete_user_file

USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'user_usage.json')


class StorageManager:
    def __init__(self):
        self._lock = asyncio.Lock()

    def _load_usage_data(self):
        if os.path.exists(USAGE_FILE):
            try:
                with open(USAGE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_usage_data(self, data):
        os.makedirs(os.path.dirname(USAGE_FILE), exist_ok=True)
        with open(USAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def get_user_usage(self, user_id):
        user_dir = get_bot_file_dir(str(user_id))
        return calculate_user_usage(str(user_id))

    async def get_user_limits(self, user_id, default_gb=1.0):
        data = self._load_usage_data()
        uid = str(user_id)
        if uid in data:
            return data[uid].get('limit_gb', default_gb)
        return default_gb

    async def set_user_limit(self, user_id, limit_gb):
        async with self._lock:
            data = self._load_usage_data()
            uid = str(user_id)
            if uid not in data:
                data[uid] = {}
            data[uid]['limit_gb'] = limit_gb
            self._save_usage_data(data)
            logger.info(f'设置用户 {user_id} 容量限制为 {limit_gb}GB')

    async def check_storage(self, user_id, file_size, config):
        usage = await self.get_user_usage(str(user_id))
        limit = await self.get_user_limits(str(user_id), config.get('storage', {}).get('default_capacity_gb', 1.0))
        limit_bytes = limit * 1024 * 1024 * 1024
        available = limit_bytes - usage
        return available >= file_size, available, usage, limit_bytes

    async def save_file(self, user_id, file_name, file_data, config):
        user_dir = get_bot_file_dir(str(user_id))
        file_path = os.path.join(user_dir, file_name)

        file_size = len(file_data)
        can_store, available, usage, limit = await self.check_storage(
            str(user_id), file_size, config
        )

        if not can_store:
            return False, f'对不起,你已超出管理员设定空间'

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)

        logger.info(f'用户 {user_id} 上传文件: {file_name} ({file_size} bytes)')
        return True, f'🎉恭喜你 上传成功🎉'

    async def list_user_files(self, user_id):
        files = get_user_files(str(user_id))
        file_list = []
        for i, f in enumerate(files, 1):
            size_str = self._fmt_size(f['size'])
            file_list.append((i, f['name'], size_str))
        return file_list

    async def get_file_data(self, user_id, file_index):
        files = get_user_files(str(user_id))
        if 1 <= file_index <= len(files):
            f = files[file_index - 1]
            return f['path'], f['name']
        return None, None

    async def delete_file(self, user_id, file_index):
        files = get_user_files(str(user_id))
        if 1 <= file_index <= len(files):
            f = files[file_index - 1]
            if delete_user_file(str(user_id), f['name']):
                logger.info(f'用户 {user_id} 删除文件: {f["name"]}')
                return True, f['name']
        return False, None

    def _fmt_size(self, size_bytes):
        if size_bytes < 1024:
            return f'{size_bytes}B'
        elif size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.2f}KB'
        elif size_bytes < 1024 * 1024 * 1024:
            return f'{size_bytes / (1024 * 1024):.2f}MB'
        else:
            return f'{size_bytes / (1024 * 1024 * 1024):.2f}GB'

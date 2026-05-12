import json
import os
import asyncio

from utils.logger import logger

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')


class UserManager:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._users = {}
        self._load()

    def _load(self):
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    self._users = json.load(f)
            except Exception as e:
                logger.error(f'加载用户数据失败: {e}')
                self._users = {}

    def _save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._users, f, ensure_ascii=False, indent=2)

    async def register_user(self, user_id, username='', first_name='', last_name=''):
        async with self._lock:
            uid = str(user_id)
            if uid not in self._users:
                self._users[uid] = {
                    'id': uid,
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'registered_at': '',
                    'file_count': 0,
                    'total_uploaded': 0
                }
                from datetime import datetime
                self._users[uid]['registered_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save()
                logger.info(f'新用户注册: {user_id} ({username})')
            return self._users[uid]

    async def get_user(self, user_id):
        uid = str(user_id)
        return self._users.get(uid)

    async def update_user_stats(self, user_id, file_size):
        async with self._lock:
            uid = str(user_id)
            if uid in self._users:
                self._users[uid]['file_count'] = self._users[uid].get('file_count', 0) + 1
                self._users[uid]['total_uploaded'] = self._users[uid].get('total_uploaded', 0) + file_size
                self._save()

    async def get_all_users(self):
        return list(self._users.values())

    async def is_whitelisted(self, user_id, config):
        whitelist = config.get('storage', {}).get('allowed_users', [])
        if config.get('storage', {}).get('whitelist_mode', False):
            return str(user_id) in [str(u) for u in whitelist]
        return True

    async def is_blocked(self, user_id, config):
        blacklist = config.get('storage', {}).get('blocked_users', [])
        if config.get('storage', {}).get('blacklist_mode', True):
            return str(user_id) in [str(u) for u in blacklist]
        return False

    async def check_access(self, user_id, config):
        if await self.is_blocked(user_id, config):
            return False, '你已被管理员禁止使用'
        if not await self.is_whitelisted(user_id, config):
            return False, '你没有使用权限'
        return True, ''

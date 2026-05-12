import asyncio
import os
import time
import threading
from typing import Dict

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from bot.telegram_handler import TelegramBotHandler
from bot.storage import StorageManager
from utils.logger import logger
from utils.helpers import calculate_total_usage, calculate_user_usage, BOT_DIR


class BotManager(QObject):
    bot_status_changed = pyqtSignal(str, str, object)
    stats_updated = pyqtSignal(dict)
    message_received = pyqtSignal(str, str, str)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.storage = StorageManager()
        self._bots: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._loop = None
        self._thread = None
        self._running = False
        self._loop_ready = threading.Event()
        self._global_stats = {
            'total_upload_bytes': 0,
            'total_download_bytes': 0,
            'upload_speed': 0,
            'download_speed': 0,
            'last_10min_upload': [],
            'last_10min_download': [],
        }
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._update_stats)
        self._stats_timer.start(10000)

    def start_all(self):
        if self._running:
            return
        self._running = True
        self._loop_ready.clear()
        self._thread = threading.Thread(
            target=self._run_event_loop, daemon=True, name='BotEventLoop')
        self._thread.start()
        if not self._loop_ready.wait(timeout=8):
            logger.error('事件循环启动超时')
        logger.info('Bot管理器启动')

    def stop_all(self):
        self._running = False
        with self._lock:
            bots_snapshot = list(self._bots.items())
        for token, info in bots_snapshot:
            handler = info.get('handler')
            if handler:
                handler.shutdown()

        if self._loop and self._loop.is_running():
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info('Bot管理器停止')

    def _run_event_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        for bot_config in self.config.get('bots', []):
            token = bot_config.get('token', '').strip()
            if not token:
                continue
            self._schedule_bot_start(bot_config)

        self._loop_ready.set()

        try:
            self._loop.run_forever()
        except Exception as e:
            logger.error(f'事件循环异常: {e}', exc_info=True)
        finally:
            try:
                pending = asyncio.all_tasks(self._loop)
                for t in pending:
                    t.cancel()
                self._loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            self._loop.close()
            self._loop_ready.clear()
            logger.info('事件循环已关闭')

    def _schedule_bot_start(self, bot_config):
        token = bot_config.get('token', '')
        remark = bot_config.get('remark', token[:10])
        handler = TelegramBotHandler(self.config, bot_config)

        handler._notify_cb = (
            lambda bid, uid, text: self.message_received.emit(bid, uid, text))
        handler._status_cb = (
            lambda connected: self.bot_status_changed.emit(
                token, remark, connected))

        async def _runner():
            try:
                await handler.start()
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(
                    f'bot [{remark}] 异常退出: {e}', exc_info=True)
            finally:
                with self._lock:
                    self._bots.pop(token, None)

        task = self._loop.create_task(_runner())
        with self._lock:
            self._bots[token] = {
                'config': bot_config, 'handler': handler, 'task': task
            }
        self.bot_status_changed.emit(token, remark, None)
        logger.info(f'bot已调度: {remark}')

    def add_bot(self, bot_config):
        token = bot_config.get('token', '')
        with self._lock:
            if token in self._bots:
                return False, '该机器人已存在且正在运行'

        bots = self.config.get('bots', [])
        bots.append(bot_config)
        self.config['bots'] = bots

        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(
                lambda: self._schedule_bot_start(bot_config))
        elif self._loop and not self._loop.is_running():
            self._loop.call_soon_threadsafe(
                lambda: self._schedule_bot_start(bot_config))
        else:
            return True, '机器人已保存（将在重启管理器后生效）'

        return True, '机器人已添加'

    def remove_bot(self, token):
        with self._lock:
            info = self._bots.pop(token, None)

        if info:
            handler = info.get('handler')
            if handler:
                handler.shutdown()
            task = info.get('task')
            if task and not task.done():
                task.cancel()
            self.bot_status_changed.emit(
                token,
                info.get('config', {}).get('remark', token[:10]),
                False)

        before = len(self.config.get('bots', []))
        self.config['bots'] = [
            b for b in self.config.get('bots', [])
            if b.get('token') != token
        ]
        if len(self.config['bots']) == before and not info:
            return False, '机器人不存在'
        return True, '机器人已移除'

    def restart_bot(self, token):
        bot_config = None
        for b in self.config.get('bots', []):
            if b.get('token') == token:
                bot_config = b.copy()
                break
        if not bot_config:
            return False, '机器人配置未找到'

        self.remove_bot(token)
        return self.add_bot(bot_config)

    def is_bot_running(self, token):
        with self._lock:
            return token in self._bots

    def get_bot_stats(self, token):
        with self._lock:
            info = self._bots.get(token)
        if info and info.get('handler'):
            return info['handler'].get_stats()
        return {}

    def get_all_bot_stats(self):
        with self._lock:
            snapshot = dict(self._bots)
        result = {}
        for token, info in snapshot.items():
            handler = info.get('handler')
            if handler:
                result[token] = {
                    'config': info['config'],
                    'stats': handler.get_stats(),
                }
        return result

    def get_user_disk_usage(self, token):
        usage_data = {}
        if os.path.exists(BOT_DIR):
            for uid in os.listdir(BOT_DIR):
                user_dir = os.path.join(BOT_DIR, uid)
                if os.path.isdir(user_dir):
                    usage_data[uid] = calculate_user_usage(uid)
        return usage_data

    def _update_stats(self):
        stats = self.get_all_bot_stats()
        total_up = sum(
            s['stats'].get('upload_bytes', 0) for s in stats.values()
        )
        total_down = sum(
            s['stats'].get('download_bytes', 0) for s in stats.values()
        )

        now = time.time()
        self._global_stats['last_10min_upload'].append(
            (now, total_up - self._global_stats.get('_prev_up', total_up))
        )
        self._global_stats['last_10min_download'].append(
            (now, total_down - self._global_stats.get('_prev_down', total_down))
        )

        cutoff = now - 600
        self._global_stats['last_10min_upload'] = [
            x for x in self._global_stats['last_10min_upload'] if x[0] > cutoff
        ]
        self._global_stats['last_10min_download'] = [
            x for x in self._global_stats['last_10min_download'] if x[0] > cutoff
        ]

        self._global_stats['_prev_up'] = total_up
        self._global_stats['_prev_down'] = total_down
        self._global_stats['total_upload_bytes'] = total_up
        self._global_stats['total_download_bytes'] = total_down

        upload_10min = sum(x[1] for x in self._global_stats['last_10min_upload'])
        download_10min = sum(
            x[1] for x in self._global_stats['last_10min_download'])
        self._global_stats['upload_speed'] = upload_10min
        self._global_stats['download_speed'] = download_10min

        self.stats_updated.emit(self._global_stats.copy())

    def get_global_stats(self):
        return self._global_stats.copy()

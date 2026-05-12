import asyncio
import os
import re
import tempfile
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
import httpx

from bot.storage import StorageManager
from bot.user_manager import UserManager
from utils.logger import logger
from utils.helpers import get_greeting, format_size

WAITING_UPLOAD, WAITING_DOWNLOAD = range(2)

UPLOAD_FILTER = (
    filters.Document.ALL | filters.PHOTO | filters.VIDEO |
    filters.AUDIO | filters.VOICE | filters.VIDEO_NOTE
)


class TelegramBotHandler:
    def __init__(self, config, bot_config):
        self.config = config
        self.bot_config = bot_config
        self.token = bot_config.get('token', '')
        self.bot_name = bot_config.get('remark', self.token[:10])
        self.storage = StorageManager()
        self.user_manager = UserManager()
        self.app = None
        self._stats = {
            'upload_bytes': 0, 'download_bytes': 0,
            'upload_count': 0, 'download_count': 0
        }
        self._running = False
        self._connected = False
        self._notify_cb = None
        self._status_cb = None
        self._last_error = ''

    def is_connected(self):
        return self._connected

    def get_stats(self):
        return self._stats.copy()

    def get_last_error(self):
        return self._last_error

    async def _build_app(self):
        proxy = self.config.get('proxy', {})
        self._proxy_url = None
        if proxy.get('enabled'):
            host = proxy.get('host', '').strip()
            port = proxy.get('port', 0)
            ptype = proxy.get('type', 'http')
            if host and port:
                self._proxy_url = f'{ptype}://{host}:{port}'

        try:
            token = self.token
            if self._proxy_url:
                import os as _os
                _os.environ['HTTPS_PROXY'] = self._proxy_url
                _os.environ['HTTP_PROXY'] = self._proxy_url
                logger.info(f'[{self.bot_name}] 代理: {self._proxy_url}')
            else:
                logger.info(f'[{self.bot_name}] 直连模式')

            app = (Application.builder().token(token)
                   .connect_timeout(20.0)
                   .read_timeout(30.0)
                   .build())
        except Exception as e:
            self._last_error = f'构建失败: {e}'
            logger.error(f'[{self.bot_name}] {self._last_error}')
            raise

        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler(['up', 'update'], self.cmd_upload),
                CommandHandler(['dl', 'download'], self.cmd_download),
            ],
            states={
                WAITING_UPLOAD: [
                    MessageHandler(UPLOAD_FILTER, self.handle_upload),
                    CommandHandler('cancel', self.cmd_cancel),
                ],
                WAITING_DOWNLOAD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   self.handle_download),
                    CommandHandler('cancel', self.cmd_cancel),
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cmd_cancel)],
        )

        app.add_handler(CommandHandler(['s', 'start'], self.cmd_start))
        app.add_handler(CommandHandler(['q', 'query'], self.cmd_query))
        app.add_handler(CommandHandler(['h', 'help'], self.cmd_help))
        app.add_handler(conv_handler)

        logger.info(f'[{self.bot_name}] 处理器注册完成')
        return app

    async def start(self):
        try:
            self.app = await self._build_app()
            self._running = True
            logger.info(f'[{self.bot_name}] 正在连接Telegram...')

            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
            )

            self._connected = True
            logger.info(f'[{self.bot_name}] 已成功上线 ✅')
            if self._status_cb:
                try:
                    self._status_cb(True)
                except Exception:
                    pass

            while self._running:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info(f'[{self.bot_name}] 任务被取消')
        except Exception as e:
            self._last_error = str(e)[:120]
            logger.error(
                f'[{self.bot_name}] 运行异常: {self._last_error}', exc_info=True)
        finally:
            self._running = False
            self._connected = False
            if self._status_cb:
                try:
                    self._status_cb(False)
                except Exception:
                    pass
            await self._cleanup()

    async def _cleanup(self):
        if self.app:
            try:
                if self.app.updater and self.app.updater.running:
                    await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
            except Exception as e:
                logger.error(f'[{self.bot_name}] 清理异常: {e}')
            self.app = None
            logger.info(f'[{self.bot_name}] 已离线')

    def shutdown(self):
        self._running = False

    def _notify(self, user_id, text):
        if self._notify_cb:
            try:
                self._notify_cb(self.bot_name, str(user_id), text)
            except Exception:
                pass

    async def cmd_start(self, update: Update,
                        context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id

        await self.user_manager.register_user(
            user_id, user.username or '',
            user.first_name or '', user.last_name or '')

        access, msg = await self.user_manager.check_access(
            user_id, self.config)
        if not access:
            await update.message.reply_text(msg)
            return

        greeting = get_greeting()
        usage_bytes = await self.storage.get_user_usage(user_id)
        limit_gb = await self.storage.get_user_limits(
            user_id, self.config.get('storage', {}).get('default_capacity_gb', 1.0))
        limit_bytes = limit_gb * 1024 ** 3
        available_bytes = max(0, limit_bytes - usage_bytes)

        await update.message.reply_text(
            f'🎉{greeting}🎉\n'
            f'❀欢迎{user_id}使用清风网盘❀\n'
            f'目前可用空间为 {format_size(available_bytes)}\n'
            f'已经使用 {format_size(usage_bytes)}')
        self._notify(user_id, '/start')
        logger.info(f'用户 {user_id} 执行 /start')

    async def cmd_upload(self, update: Update,
                         context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        access, msg = await self.user_manager.check_access(
            user_id, self.config)
        if not access:
            await update.message.reply_text(msg)
            return ConversationHandler.END

        await update.message.reply_text('请在1分钟内发送所需上传的文件')
        self._notify(user_id, '/upload')
        return WAITING_UPLOAD

    async def handle_upload(self, update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        message = update.message

        file_obj = None
        file_name = ''

        if message.document:
            file_obj = message.document
            file_name = file_obj.file_name or f'doc_{file_obj.file_unique_id[:8]}'
        elif message.photo:
            file_obj = message.photo[-1]
            file_name = f'photo_{file_obj.file_unique_id[:8]}.jpg'
        elif message.video:
            file_obj = message.video
            file_name = file_obj.file_name or f'video_{file_obj.file_unique_id[:8]}.mp4'
        elif message.audio:
            file_obj = message.audio
            file_name = file_obj.file_name or f'audio_{file_obj.file_unique_id[:8]}.mp3'
        elif message.voice:
            file_obj = message.voice
            file_name = f'voice_{file_obj.file_unique_id[:8]}.ogg'
        elif message.video_note:
            file_obj = message.video_note
            file_name = f'vn_{file_obj.file_unique_id[:8]}.mp4'
        else:
            await message.reply_text('不支持的文件类型，请重新发送')
            return WAITING_UPLOAD

        file_size = getattr(file_obj, 'file_size', 0) or 0

        progress_msg = await message.reply_text('⏳ 接收中... 0%')
        progress_task = None
        tmp_path = None

        async def _update_progress():
            nonlocal tmp_path
            for i in range(1, 101, 5):
                try:
                    if tmp_path and os.path.exists(tmp_path):
                        current = os.path.getsize(tmp_path)
                        if file_size > 0:
                            pct = min(current / file_size * 100, 99.9)
                            await progress_msg.edit_text(
                                f'⏳ 接收中... {pct:.1f}%  '
                                f'({current}/{file_size} bytes)')
                        else:
                            await progress_msg.edit_text(
                                f'⏳ 接收中... {current} bytes')
                    else:
                        await progress_msg.edit_text(
                            f'⏳ 接收中... {min(i, 95)}%')
                except Exception:
                    pass
                await asyncio.sleep(5)

        try:
            getfile_url = f'https://api.telegram.org/bot{self.token}/getFile'
            httpx_kwargs = {'timeout': 30.0}
            if self._proxy_url:
                httpx_kwargs['proxy'] = self._proxy_url
            async with httpx.AsyncClient(**httpx_kwargs) as client:
                resp = await client.post(
                    getfile_url,
                    data={'file_id': file_obj.file_id})
                result = resp.json()
                if result.get('ok'):
                    file_path = result['result']['file_path']
                    actual_file_size = result['result'].get('file_size', 0)
                    if actual_file_size > 0:
                        file_size = actual_file_size
                elif 'file is too big' in str(result.get('description', '')).lower():
                    return await self._telethon_download(
                        update, message, user_id, file_name,
                        file_size, progress_msg, progress_task, tmp_path)
                else:
                    raise Exception(
                        result.get('description', f'getFile HTTP {resp.status_code}'))

            download_url = (
                f'https://api.telegram.org/file/bot{self.token}/{file_path}')

            fd, tmp_path = tempfile.mkstemp(suffix='_' + file_name)
            os.close(fd)

            progress_task = asyncio.create_task(_update_progress())

            dl_kwargs = {'timeout': 600.0, 'follow_redirects': True}
            if self._proxy_url:
                dl_kwargs['proxy'] = self._proxy_url
            async with httpx.AsyncClient(**dl_kwargs) as client:
                async with client.stream('GET', download_url) as resp:
                    if resp.status_code != 200:
                        raise Exception(
                            f'下载失败 HTTP {resp.status_code}')
                    with open(tmp_path, 'wb') as f:
                        async for chunk in resp.aiter_bytes(65536):
                            f.write(chunk)

            if progress_task and not progress_task.done():
                progress_task.cancel()

            actual_size = os.path.getsize(tmp_path)
            with open(tmp_path, 'rb') as f:
                file_data = f.read()

            success, result_msg = await self.storage.save_file(
                str(user_id), file_name, file_data, self.config)

            await message.reply_text(result_msg)
            if success:
                self._stats['upload_bytes'] += actual_size
                self._stats['upload_count'] += 1
                await self.user_manager.update_user_stats(
                    user_id, actual_size)

        except Exception as e:
            logger.error(f'下载文件失败: {e}')
            if progress_task and not progress_task.done():
                progress_task.cancel()
            await message.reply_text(f'文件下载失败: {e}')
            return ConversationHandler.END
        finally:
            try:
                await progress_msg.delete()
            except Exception:
                pass
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        logger.info(f'用户 {user_id} 上传: {file_name} - {result_msg}')
        return ConversationHandler.END

    async def _telethon_download(self, update, message, user_id,
                                  file_name, file_size,
                                  progress_msg, progress_task, tmp_path):
        telethon_cfg = self.config.get('telethon', {})
        api_id_str = telethon_cfg.get('api_id', '').strip()
        api_hash = telethon_cfg.get('api_hash', '').strip()

        if not api_id_str or not api_hash:
            await message.reply_text(
                '文件超过 20MB，Bot API 无法下载。\n'
                '请在设置中填写 api_id 和 api_hash\n'
                '(https://my.telegram.org/apps) 以启用大文件下载。')
            return ConversationHandler.END

        try:
            api_id = int(api_id_str)
        except ValueError:
            await message.reply_text('api_id 格式错误，必须是纯数字。')
            return ConversationHandler.END

        from telethon import TelegramClient

        try:
            await progress_msg.delete()
        except Exception:
            pass
        progress_msg = await message.reply_text('⏳ MTProto 大文件下载中...')

        telethon_proxy = None
        if self._proxy_url:
            m = re.match(r'(\w+)://([^:]+):(\d+)', self._proxy_url)
            if m:
                telethon_proxy = (m.group(1), m.group(2), int(m.group(3)))

        try:
            chat_id = update.effective_chat.id
            msg_id = message.message_id

            tmp_path = None
            client = TelegramClient(
                f'bot_session_{self.token[:10]}',
                api_id, api_hash,
                proxy=telethon_proxy
            )
            await client.start(bot_token=self.token)

            tg_msg = await client.get_messages(chat_id, ids=msg_id)
            fd, tmp_path = tempfile.mkstemp(suffix='_' + file_name)
            os.close(fd)
            await client.download_media(tg_msg, file=tmp_path)
            await client.disconnect()

            actual_size = os.path.getsize(tmp_path)
            with open(tmp_path, 'rb') as f:
                file_data = f.read()

            try:
                await progress_msg.delete()
            except Exception:
                pass

            success, result_msg = await self.storage.save_file(
                str(user_id), file_name, file_data, self.config)
            await message.reply_text(result_msg)

            if success:
                self._stats['upload_bytes'] += actual_size
                self._stats['upload_count'] += 1
                await self.user_manager.update_user_stats(
                    user_id, actual_size)

            logger.info(
                f'用户 {user_id} MTProto上传: {file_name} - {result_msg}')

        except ImportError:
            await message.reply_text(
                'Telethon 未安装。请运行: pip install telethon')
        except Exception as e:
            logger.error(f'MTProto下载失败: {e}', exc_info=True)
            await message.reply_text(f'大文件下载失败: {e}')
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            try:
                await progress_msg.delete()
            except Exception:
                pass

        return ConversationHandler.END

    async def cmd_download(self, update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        access, msg = await self.user_manager.check_access(
            user_id, self.config)
        if not access:
            await update.message.reply_text(msg)
            return ConversationHandler.END

        files = await self.storage.list_user_files(str(user_id))
        if not files:
            await update.message.reply_text('你还没有上传任何文件')
            return ConversationHandler.END

        lines = ['请发送需要下载的文件ID']
        for idx, name, size in files:
            lines.append(f'{idx} {name}')

        await update.message.reply_text('\n'.join(lines))
        self._notify(user_id, '/download')
        return WAITING_DOWNLOAD

    async def handle_download(self, update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()

        try:
            file_index = int(text)
        except ValueError:
            await update.message.reply_text('请输入有效的文件ID数字')
            return WAITING_DOWNLOAD

        file_path, file_name = await self.storage.get_file_data(
            str(user_id), file_index)
        if file_path is None:
            await update.message.reply_text('文件不存在，请重新输入')
            return WAITING_DOWNLOAD

        import os
        file_size = os.path.getsize(file_path)
        self._stats['download_bytes'] += file_size
        self._stats['download_count'] += 1

        try:
            with open(file_path, 'rb') as f:
                await update.message.reply_document(document=f, filename=file_name)
            logger.info(f'用户 {user_id} 下载: {file_name}')
        except Exception as e:
            logger.error(f'发送文件失败: {e}')
            await update.message.reply_text('文件发送失败，请稍后再试')

        return ConversationHandler.END

    async def cmd_query(self, update: Update,
                        context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        access, msg = await self.user_manager.check_access(
            user_id, self.config)
        if not access:
            await update.message.reply_text(msg)
            return

        usage_bytes = await self.storage.get_user_usage(user_id)
        limit_gb = await self.storage.get_user_limits(
            user_id, self.config.get('storage', {}).get('default_capacity_gb', 1.0))

        lines = [f'{format_size(usage_bytes)}/{limit_gb}GB']
        files = await self.storage.list_user_files(str(user_id))
        for idx, name, size in files:
            lines.append(f'{idx} {name}')

        await update.message.reply_text('\n'.join(lines))
        self._notify(user_id, '/query')

    async def cmd_help(self, update: Update,
                       context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            '❀欢迎使用清风网盘❀\n'
            '指令:\n'
            '/s /start 启动\n'
            '/up /update 上传\n'
            '/dl /download 下载\n'
            '/q /query 查询容量\n'
            '作者tg:t.me/ssqls1337\n'
            '项目为免费开源 请不要在任何地方售卖\n'
            '项目链接:https://github.com/ssqls666/Telegram_Storage_Bot')

    async def cmd_cancel(self, update: Update,
                         context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('操作已取消')
        return ConversationHandler.END

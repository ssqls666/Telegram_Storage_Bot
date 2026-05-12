from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFormLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog,
    QDialogButtonBox, QAbstractItemView
)
from PyQt5.QtGui import QFont, QColor

from utils.helpers import format_size, save_config
from utils.logger import logger


def _msg_box(parent, title, text, icon=QMessageBox.Information):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(icon)
    box.setStyleSheet("""
        QMessageBox { background-color: #FFFFFF; }
        QMessageBox QLabel { color: #1E293B; font-size: 14px; }
        QMessageBox QPushButton {
            background-color: #4A90D9; color: white;
            padding: 8px 28px; border-radius: 6px;
            font-size: 13px; font-weight: bold; min-width: 80px;
        }
        QMessageBox QPushButton:hover { background-color: #3B7EC9; }
    """)
    return box


def _confirm_box(parent, title, text):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    box.button(QMessageBox.Yes).setText('确定')
    box.button(QMessageBox.No).setText('取消')
    box.setStyleSheet("""
        QMessageBox { background-color: #FFFFFF; }
        QMessageBox QLabel { color: #1E293B; font-size: 14px; }
        QMessageBox QPushButton {
            background-color: #4A90D9; color: white;
            padding: 8px 28px; border-radius: 6px;
            font-size: 13px; font-weight: bold; min-width: 80px;
        }
        QMessageBox QPushButton:hover { background-color: #3B7EC9; }
    """)
    return box.exec_() == QMessageBox.Yes


class AddBotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加 Telegram 机器人')
        self.setMinimumWidth(480)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #334155; font-size: 13px; }
            QLineEdit {
                padding: 8px 12px; border: 1px solid #E2E8F0;
                border-radius: 6px; font-size: 13px; color: #334155;
            }
            QLineEdit:focus { border: 2px solid #4A90D9; }
            QPushButton {
                background-color: #4A90D9; color: white; padding: 8px 20px;
                border-radius: 6px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3B7EC9; }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel('🤖  添加新机器人')
        title.setFont(QFont('Microsoft YaHei', 15, QFont.Bold))
        title.setStyleSheet('color: #1E293B;')
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText('输入 Telegram Bot API Token')
        form.addRow('Bot Token：', self.token_input)

        self.remark_input = QLineEdit()
        self.remark_input.setPlaceholderText('备注名称（可选）')
        form.addRow('备  注：', self.remark_input)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton('取消')
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9; color: #475569;
                padding: 8px 20px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton('确认添加')
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def get_bot_config(self):
        return {
            'token': self.token_input.text().strip(),
            'remark': self.remark_input.text().strip()
            or self.token_input.text().strip()[:15],
        }


class UserUsageDialog(QDialog):
    def __init__(self, token, bot_manager, parent=None):
        super().__init__(parent)
        self.token = token
        self.bot_manager = bot_manager
        self.setWindowTitle('用户存储详情')
        self.setMinimumSize(680, 460)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #334155; }
            QTableWidget { border: 1px solid #E2E8F0; border-radius: 8px; gridline-color: #F1F5F9; }
            QTableWidget::item { padding: 8px 12px; }
            QHeaderView::section {
                background-color: #F8FAFC; padding: 10px; border: none;
                border-bottom: 2px solid #E2E8F0; font-weight: bold; color: #64748B;
            }
            QPushButton {
                background-color: #4A90D9; color: white; padding: 8px 20px;
                border-radius: 6px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3B7EC9; }
        """)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel('📊  各用户存储使用详情')
        title.setFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        title.setStyleSheet('color: #1E293B;')
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ['用户ID', '已使用', '可用容量', '使用率(%)', '文件数'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton('关  闭')
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _load_data(self):
        usage_data = self.bot_manager.get_user_disk_usage(self.token)
        self.table.setRowCount(len(usage_data))

        try:
            cap_gb = float(self.bot_manager.config.get(
                'storage', {}).get('default_capacity_gb', 1.0))
        except (ValueError, TypeError):
            cap_gb = 1.0

        import os
        from utils.helpers import BOT_DIR

        for row, (uid, usage) in enumerate(usage_data.items()):
            cap_bytes = cap_gb * 1024 ** 3
            ratio = (usage / cap_bytes * 100) if cap_bytes > 0 else 0

            user_dir = os.path.join(BOT_DIR, uid)
            file_count = 0
            if os.path.isdir(user_dir):
                file_count = len([
                    f for f in os.listdir(user_dir)
                    if os.path.isfile(os.path.join(user_dir, f))])

            items = [
                QTableWidgetItem(str(uid)),
                QTableWidgetItem(format_size(usage)),
                QTableWidgetItem(f'{cap_gb} GB'),
                QTableWidgetItem(f'{ratio:.1f}'),
                QTableWidgetItem(str(file_count)),
            ]

            color = QColor('#EF4444') if ratio >= 90 else (
                QColor('#F59E0B') if ratio >= 70 else None)
            if color:
                for it in items:
                    it.setForeground(color)

            for col, it in enumerate(items):
                self.table.setItem(row, col, it)


class BotPage(QWidget):
    bot_added = pyqtSignal(dict)
    bot_removed = pyqtSignal(str)

    def __init__(self, config, bot_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.bot_manager = bot_manager
        self._init_ui()
        self._refresh_bot_list()

        self.bot_manager.bot_status_changed.connect(self._on_bot_status)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_bot_list)
        self._refresh_timer.start(5000)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        top_row = QHBoxLayout()
        title = QLabel('🤖  机器人管理')
        title.setFont(QFont('Microsoft YaHei', 18, QFont.Bold))
        title.setStyleSheet('color: #1E293B;')
        top_row.addWidget(title)
        top_row.addStretch()

        self.restart_btn = QPushButton('🔄  重启全部')
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #EBF4FF; color: #4A90D9;
                padding: 10px 20px; border-radius: 8px;
                font-size: 13px; font-weight: bold; border: 1px solid #BFDBFE;
            }
            QPushButton:hover { background-color: #DBEAFE; }
        """)
        self.restart_btn.clicked.connect(self._restart_all)
        top_row.addWidget(self.restart_btn)

        self.add_btn = QPushButton('➕  添加机器人')
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22C55E, stop:1 #16A34A);
                color: white; padding: 10px 24px; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16A34A, stop:1 #15803D);
            }
        """)
        self.add_btn.clicked.connect(self._add_bot)
        top_row.addWidget(self.add_btn)
        layout.addLayout(top_row)

        self.bot_table = QTableWidget()
        self.bot_table.setColumnCount(5)
        self.bot_table.setHorizontalHeaderLabels(
            ['Bot Token', '备注名称', '运行状态', '错误信息', '操作'])
        self.bot_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch)
        self.bot_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch)
        self.bot_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents)
        self.bot_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch)
        self.bot_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents)
        self.bot_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bot_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.bot_table.setAlternatingRowColors(True)
        self.bot_table.verticalHeader().setVisible(False)
        layout.addWidget(self.bot_table)

        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC; border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        info_layout = QHBoxLayout(info_card)
        info_layout.setContentsMargins(16, 10, 16, 10)
        self.info_label = QLabel(
            '💡  添加机器人后需在设置中配置代理（中国大陆用户必须）')
        self.info_label.setStyleSheet(
            'color: #64748B; font-size: 12px; border: none; background: transparent;')
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_card)

    def _on_bot_status(self, token, remark, status):
        self._refresh_bot_list()

    def _restart_all(self):
        self.bot_manager.stop_all()
        time.sleep(0.5)
        self.bot_manager.start_all()

    def _restart_single(self, token):
        success, msg = self.bot_manager.restart_bot(token)
        if success:
            save_config(self.config)
            self._refresh_bot_list()
        _msg_box(self, '成功' if success else '失败', msg,
                 QMessageBox.Information if success else QMessageBox.Warning).exec_()

    def _add_bot(self):
        dlg = AddBotDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        bot_config = dlg.get_bot_config()
        if not bot_config['token']:
            _msg_box(self, '提示', '请输入 Bot Token', QMessageBox.Warning).exec_()
            return
        success, msg_text = self.bot_manager.add_bot(bot_config)
        if success:
            save_config(self.config)
            self.bot_added.emit(bot_config)
            self._refresh_bot_list()
        _msg_box(
            self,
            '成功' if success else '提示',
            msg_text,
            QMessageBox.Information if success else QMessageBox.Warning
        ).exec_()

    def _remove_bot(self, token):
        if not _confirm_box(self, '确认删除',
                            f'确定要删除该机器人吗？\n\nToken: {token[:20]}...'):
            return
        success, msg_text = self.bot_manager.remove_bot(token)
        if success:
            save_config(self.config)
            self.bot_removed.emit(token)
            self._refresh_bot_list()
        else:
            _msg_box(self, '提示', msg_text, QMessageBox.Warning).exec_()

    def _show_usage(self, token):
        dlg = UserUsageDialog(token, self.bot_manager, self)
        dlg.exec_()

    def _refresh_bot_list(self):
        bots = self.config.get('bots', [])
        self.bot_table.setRowCount(len(bots))

        for row, bot in enumerate(bots):
            token = bot.get('token', '')
            remark = bot.get('remark', '')

            token_item = QTableWidgetItem(
                token[:24] + '...' if len(token) > 24 else token)
            token_item.setData(Qt.UserRole, token)
            token_item.setToolTip(token)
            self.bot_table.setItem(row, 0, token_item)

            self.bot_table.setItem(row, 1, QTableWidgetItem(remark or '未备注'))

            is_running = self.bot_manager.is_bot_running(token)
            if not is_running:
                status_text = '○ 离线'
                status_color = QColor('#EF4444')
            else:
                with self.bot_manager._lock:
                    info = self.bot_manager._bots.get(token)
                handler = info.get('handler') if info else None
                if handler and handler.is_connected():
                    status_text = '● 运行中'
                    status_color = QColor('#22C55E')
                else:
                    status_text = '◉ 连接中...'
                    status_color = QColor('#F59E0B')
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_color)
            self.bot_table.setItem(row, 2, status_item)

            err_text = ''
            with self.bot_manager._lock:
                info = self.bot_manager._bots.get(token)
            if info:
                handler = info.get('handler')
                if handler:
                    err_text = handler.get_last_error()
            err_item = QTableWidgetItem(
                err_text[:60] if err_text else '')
            if err_text:
                err_item.setForeground(QColor('#EF4444'))
                err_item.setToolTip(err_text)
            self.bot_table.setItem(row, 3, err_item)

            ops_widget = QWidget()
            ops_layout = QHBoxLayout(ops_widget)
            ops_layout.setContentsMargins(2, 2, 2, 2)
            ops_layout.setSpacing(6)

            restart_single_btn = QPushButton('🔄')
            restart_single_btn.setToolTip('重启此机器人')
            restart_single_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F0FDF4; color: #22C55E;
                    padding: 5px 10px; border-radius: 5px; font-size: 12px;
                    border: 1px solid #BBF7D0;
                }
                QPushButton:hover { background-color: #DCFCE7; }
            """)
            restart_single_btn.clicked.connect(
                lambda checked, t=token: self._restart_single(t))
            ops_layout.addWidget(restart_single_btn)

            usage_btn = QPushButton('📊 用量')
            usage_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EBF4FF; color: #4A90D9;
                    padding: 5px 12px; border-radius: 5px; font-size: 12px;
                    font-weight: bold; border: 1px solid #BFDBFE;
                }
                QPushButton:hover { background-color: #DBEAFE; }
            """)
            usage_btn.clicked.connect(
                lambda checked, t=token: self._show_usage(t))
            ops_layout.addWidget(usage_btn)

            del_btn = QPushButton('🗑 删除')
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FEE2E2; color: #EF4444;
                    padding: 5px 12px; border-radius: 5px; font-size: 12px;
                    font-weight: bold; border: 1px solid #FECACA;
                }
                QPushButton:hover { background-color: #FECACA; }
            """)
            del_btn.clicked.connect(
                lambda checked, t=token: self._remove_bot(t))
            ops_layout.addWidget(del_btn)

            self.bot_table.setCellWidget(row, 4, ops_widget)
            self.bot_table.setRowHeight(row, 44)

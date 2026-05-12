from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QMessageBox, QGraphicsOpacityEffect
)
from PyQt5.QtGui import QFont

from gui.dashboard_page import DashboardPage
from gui.settings_page import SettingsPage
from gui.bot_page import BotPage
from gui.files_page import FilesPage
from gui.theme_manager import ThemeManager
from bot.bot_manager import BotManager
from utils.helpers import load_config, save_config
from utils.logger import logger


class SidebarButton(QPushButton):
    def __init__(self, text, icon='', key='', parent=None):
        super().__init__(f'  {icon}  {text}', parent)
        self._key = key
        self._active = False
        self._hover = False
        self.setCheckable(True)
        self.setFont(QFont('Microsoft YaHei', 10))
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)
        self.update_style(False)

    def update_style(self, active):
        self._active = active
        if active:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4A90D9, stop:1 #3B7EC9);
                    color: white;
                    border: none;
                    text-align: left;
                    padding: 10px 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #94A3B8;
                    border: none;
                    text-align: left;
                    padding: 10px 16px;
                    border-radius: 8px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2D3748;
                    color: #E2E8F0;
                }
            """)


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.theme_manager = ThemeManager(config)
        self.bot_manager = BotManager(config)

        self.setWindowTitle('清风网盘 - Telegram 文件储存机器人')
        self.setMinimumSize(1200, 750)
        self.resize(1320, 840)

        self.setStyleSheet(self.theme_manager.main_style())

        self._init_ui()
        self._connect_signals()

        self.bot_manager.start_all()
        self.bot_manager.message_received.connect(self._on_message)
        self._active_toasts = []
        logger.info('GUI主窗口初始化完成')

    def _on_message(self, bot_id, user_id, text):
        for old in self._active_toasts:
            try:
                old.deleteLater()
            except RuntimeError:
                pass
        self._active_toasts.clear()

        toast = QLabel(
            f'📩 [{bot_id}]  用户 {user_id}  →  {text}')
        toast.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1E293B, stop:1 #334155);
                color: #E2E8F0;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        toast.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        toast.setAttribute(Qt.WA_ShowWithoutActivating)
        toast.setAttribute(Qt.WA_TransparentForMouseEvents)
        toast.adjustSize()

        geo = self.geometry()
        x = geo.right() - toast.width() - 30
        y = geo.top() + 60
        toast.move(x, y)
        toast.show()

        self._active_toasts.append(toast)

        effect = QGraphicsOpacityEffect(toast)
        toast.setGraphicsEffect(effect)
        effect.setOpacity(0)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(300)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()

        def _fade_out(t=toast):
            if t not in self._active_toasts:
                return
            self._active_toasts.remove(t)
            fade = QPropertyAnimation(t.graphicsEffect(), b"opacity")
            fade.setDuration(500)
            fade.setStartValue(1)
            fade.setEndValue(0)
            fade.setEasingCurve(QEasingCurve.InCubic)
            fade.finished.connect(t.deleteLater)
            fade.start()
        QTimer.singleShot(3500, _fade_out)

        logger.info(f'消息通知: [{bot_id}] {user_id}: {text}')

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1A1B2E, stop:1 #16172B);
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 20)
        sidebar_layout.setSpacing(4)

        logo = QLabel('  🍃 清风网盘')
        logo.setFont(QFont('Microsoft YaHei', 15, QFont.Bold))
        logo.setStyleSheet('color: #FFFFFF; padding: 6px 4px 24px 4px;')
        sidebar_layout.addWidget(logo)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('background-color: #2D3748; max-height: 1px;')
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(14)

        self.nav_buttons = {}
        nav_items = [
            ('dashboard', '仪表盘', '📊'),
            ('settings', '设  置', '⚙️'),
            ('bots', '机 器 人', '🤖'),
            ('files', '文  件', '📁'),
        ]

        for key, text, icon in nav_items:
            btn = SidebarButton(text, icon, key)
            btn.clicked.connect(lambda checked, k=key: self._switch_page(k))
            self.nav_buttons[key] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        version_label = QLabel('v2.2.0')
        version_label.setStyleSheet('color: #5A6070; font-size: 10px; padding: 8px;')
        version_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version_label)

        main_layout.addWidget(sidebar)

        content_area = QFrame()
        content_area.setStyleSheet('background-color: #F0F2F5;')
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet('background-color: transparent;')

        self.dashboard_page = DashboardPage(self.config, self.bot_manager)
        self.settings_page = SettingsPage(self.config)
        self.bot_page = BotPage(self.config, self.bot_manager)
        self.files_page = FilesPage(self.config)

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.bot_page)
        self.stack.addWidget(self.files_page)

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_area, 1)

        self._switch_page('dashboard', animate=False)

    def _connect_signals(self):
        self.settings_page.config_changed.connect(self._on_config_changed)
        self.bot_page.bot_added.connect(self._on_bot_added)
        self.bot_page.bot_removed.connect(self._on_bot_removed)

    def _switch_page(self, key, animate=True):
        page_map = {'dashboard': 0, 'settings': 1, 'bots': 2, 'files': 3}
        index = page_map.get(key, 0)

        current_widget = self.stack.currentWidget()
        next_widget = self.stack.widget(index)

        if animate and current_widget and next_widget and current_widget != next_widget:
            self._animate_page_switch(current_widget, next_widget, index)

        self.stack.setCurrentIndex(index)

        for k, btn in self.nav_buttons.items():
            btn.update_style(k == key)
            btn.setChecked(k == key)

    def _animate_page_switch(self, old_widget, new_widget, index):
        old_effect = QGraphicsOpacityEffect(old_widget)
        old_widget.setGraphicsEffect(old_effect)
        old_anim = QPropertyAnimation(old_effect, b"opacity")
        old_anim.setDuration(150)
        old_anim.setStartValue(1.0)
        old_anim.setEndValue(0.0)
        old_anim.setEasingCurve(QEasingCurve.OutQuad)
        old_anim.start()

        geo = new_widget.geometry()
        new_widget.move(geo.x() + 30, geo.y())
        new_effect = QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(new_effect)
        new_effect.setOpacity(0.0)

        opacity_anim = QPropertyAnimation(new_effect, b"opacity")
        opacity_anim.setDuration(300)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        opacity_anim.start()

        pos_anim = QPropertyAnimation(new_widget, b"pos")
        pos_anim.setDuration(300)
        pos_anim.setStartValue(new_widget.pos())
        pos_anim.setEndValue(QPoint(geo.x(), geo.y()))
        pos_anim.setEasingCurve(QEasingCurve.OutCubic)
        pos_anim.start()

        self._active_anims = (old_anim, opacity_anim, pos_anim)

    def _on_config_changed(self):
        save_config(self.config)
        self.bot_manager.stop_all()
        self.bot_manager.start_all()
        self.bot_page._refresh_bot_list()
        logger.info('配置已更新，所有机器人已重启')

    def _on_bot_added(self, bot_config):
        logger.info(f'机器人已添加: {bot_config.get("remark", "")}')

    def _on_bot_removed(self, token):
        logger.info(f'机器人已移除: {token[:10]}...')

    def closeEvent(self, event):
        box = QMessageBox(self)
        box.setWindowTitle('确认退出')
        box.setText('确定要退出清风网盘吗？\n所有机器人将停止运行。')
        box.setIcon(QMessageBox.Question)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        box.button(QMessageBox.Yes).setText('退出')
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
        if box.exec_() == QMessageBox.Yes:
            self.bot_manager.stop_all()
            save_config(self.config)
            logger.info('程序正常退出')
            event.accept()
        else:
            event.ignore()

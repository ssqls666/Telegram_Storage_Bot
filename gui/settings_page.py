from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFormLayout, QLabel, QLineEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
    QFrame, QMessageBox, QTextEdit, QScrollArea
)
from PyQt5.QtGui import QFont

from utils.helpers import save_config
from utils.logger import logger


class ProxyTestThread(QThread):
    result_ready = pyqtSignal(bool, str)

    def __init__(self, proxy_type, host, port, parent=None):
        super().__init__(parent)
        self._ptype = proxy_type
        self._host = host
        self._port = port

    def run(self):
        import urllib.request
        import ssl
        try:
            proxy_url = f'{self._ptype}://{self._host}:{self._port}'
            proxy_handler = urllib.request.ProxyHandler({
                'http': proxy_url,
                'https': proxy_url,
            })
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            opener = urllib.request.build_opener(
                proxy_handler, urllib.request.HTTPSHandler(context=ctx))
            urllib.request.install_opener(opener)
            response = urllib.request.urlopen(
                'https://api.telegram.org', timeout=8)
            if response.status == 200:
                self.result_ready.emit(
                    True, f'连接成功！(HTTP {response.status})')
            else:
                self.result_ready.emit(
                    False, f'服务器响应异常: HTTP {response.status}')
        except Exception as e:
            self.result_ready.emit(False, f'连接失败: {str(e)[:80]}')


class SettingsPage(QWidget):
    config_changed = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        title = QLabel('⚙️  系统设置')
        title.setFont(QFont('Microsoft YaHei', 18, QFont.Bold))
        title.setStyleSheet('color: #1E293B; padding: 4px 0;')
        layout.addWidget(title)

        self._create_proxy_section(layout)
        self._create_telethon_section(layout)
        self._create_storage_section(layout)
        self._create_admin_section(layout)
        self._create_access_section(layout)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton('💾  保存设置')
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22C55E, stop:1 #16A34A);
                color: white;
                padding: 11px 32px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16A34A, stop:1 #15803D);
            }
        """)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)
        layout.addStretch()

    def _section_label(self, text):
        l = QLabel(text)
        l.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
        l.setStyleSheet('color: #334155; padding: 6px 0 2px 0;')
        return l

    def _form_group(self):
        g = QGroupBox()
        g.setStyleSheet("""
            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                margin-top: 12px;
                padding: 20px 16px 12px 16px;
                font-size: 13px;
                font-weight: bold;
                color: #475569;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
        """)
        return g

    def _create_proxy_section(self, parent_layout):
        parent_layout.addWidget(self._section_label('🌐  代理设置'))
        group = self._form_group()
        gl = QVBoxLayout(group)
        gl.setSpacing(10)

        self.proxy_enabled = QCheckBox('启用代理服务器')
        self.proxy_enabled.setChecked(self.config.get('proxy', {}).get('enabled', False))
        self.proxy_enabled.setStyleSheet('font-weight: normal; color: #334155;')
        gl.addWidget(self.proxy_enabled)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.proxy_type = QComboBox()
        self.proxy_type.addItems(['http', 'socks5', 'socks4'])
        self.proxy_type.setCurrentText(self.config.get('proxy', {}).get('type', 'http'))
        self.proxy_type.setStyleSheet('QComboBox { min-width: 120px; }')
        form.addRow('代理类型：', self.proxy_type)

        self.proxy_host = QLineEdit()
        self.proxy_host.setText(self.config.get('proxy', {}).get('host', '127.0.0.1'))
        self.proxy_host.setPlaceholderText('127.0.0.1')
        form.addRow('主机地址：', self.proxy_host)

        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(self.config.get('proxy', {}).get('port', 10808))
        self.proxy_port.setStyleSheet('QSpinBox { min-width: 100px; }')
        form.addRow('端口号：', self.proxy_port)

        gl.addLayout(form)

        test_row = QHBoxLayout()
        test_row.addStretch()
        self.proxy_test_btn = QPushButton('🔗  测试代理连接')
        self.proxy_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #EBF4FF; color: #4A90D9;
                padding: 7px 16px; border-radius: 6px;
                font-size: 12px; font-weight: bold;
                border: 1px solid #BFDBFE;
            }
            QPushButton:hover { background-color: #DBEAFE; }
            QPushButton:disabled { background-color: #F1F5F9; color: #94A3B8; border-color: #E2E8F0; }
        """)
        self.proxy_test_btn.clicked.connect(self._test_proxy)
        test_row.addWidget(self.proxy_test_btn)

        self.proxy_status_label = QLabel('')
        self.proxy_status_label.setStyleSheet(
            'color: #9CA3AF; font-size: 11px; border: none; background: transparent;')
        test_row.addWidget(self.proxy_status_label)
        test_row.addStretch()
        gl.addLayout(test_row)

        parent_layout.addWidget(group)

    def _test_proxy(self):
        ptype = self.proxy_type.currentText()
        host = self.proxy_host.text().strip()
        port = self.proxy_port.value()
        if not host:
            m = QMessageBox(self)
            m.setWindowTitle('提示')
            m.setText('请输入代理主机地址')
            m.setIcon(QMessageBox.Warning)
            m.setStyleSheet("""
                QMessageBox { background-color: white; }
                QMessageBox QLabel { color: #2C3E50; font-size: 14px; }
                QMessageBox QPushButton {
                    background-color: #4A90D9; color: white; padding: 8px 24px;
                    border-radius: 6px; font-size: 13px; min-width: 80px;
                }
            """)
            m.exec_()
            return

        self.proxy_test_btn.setEnabled(False)
        self.proxy_test_btn.setText('⏳  测试中...')
        self.proxy_status_label.setText('正在连接 api.telegram.org ...')
        self.proxy_status_label.setStyleSheet(
            'color: #F59E0B; font-size: 11px; border: none; background: transparent;')

        self._test_thread = ProxyTestThread(ptype, host, port)
        self._test_thread.result_ready.connect(self._on_proxy_test_result)
        self._test_thread.start()

    def _on_proxy_test_result(self, success, msg):
        self.proxy_test_btn.setEnabled(True)
        self.proxy_test_btn.setText('🔗  测试代理连接')
        if success:
            self.proxy_status_label.setText(f'✅ {msg}')
            self.proxy_status_label.setStyleSheet(
                'color: #22C55E; font-size: 11px; border: none; background: transparent;')
        else:
            self.proxy_status_label.setText(f'❌ {msg}')
            self.proxy_status_label.setStyleSheet(
                'color: #EF4444; font-size: 11px; border: none; background: transparent;')

    def _create_storage_section(self, parent_layout):
        parent_layout.addWidget(self._section_label('💾  存储配额'))
        group = self._form_group()
        form = QFormLayout(group)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.storage_capacity = QDoubleSpinBox()
        self.storage_capacity.setRange(0.1, 999999)
        self.storage_capacity.setValue(
            self.config.get('storage', {}).get('default_capacity_gb', 1.0))
        self.storage_capacity.setSuffix(' GB')
        self.storage_capacity.setStyleSheet('QDoubleSpinBox { min-width: 120px; }')
        form.addRow('默认用户容量：', self.storage_capacity)

        parent_layout.addWidget(group)

    def _create_telethon_section(self, parent_layout):
        parent_layout.addWidget(self._section_label('🔧  大文件下载 (Telethon/MTProto)'))
        group = self._form_group()
        gl = QVBoxLayout(group)

        hint = QLabel(
            'Telegram Bot API 限制文件下载最大 20MB。\n'
            '超过限制的文件通过 MTProto 协议下载（需要 api_id/api_hash）。\n'
            '在 https://my.telegram.org/apps 获取。')
        hint.setStyleSheet('color: #94A3B8; font-size: 11px; font-weight: normal; padding-bottom: 6px;')
        gl.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        telethon = self.config.get('telethon', {})
        self.api_id_input = QLineEdit()
        self.api_id_input.setText(str(telethon.get('api_id', '')))
        self.api_id_input.setPlaceholderText('例如: 12345678')
        form.addRow('API ID：', self.api_id_input)

        self.api_hash_input = QLineEdit()
        self.api_hash_input.setText(telethon.get('api_hash', ''))
        self.api_hash_input.setPlaceholderText('例如: a1b2c3d4e5f6...')
        self.api_hash_input.setEchoMode(QLineEdit.Password)
        form.addRow('API Hash：', self.api_hash_input)

        gl.addLayout(form)
        parent_layout.addWidget(group)

    def _create_admin_section(self, parent_layout):
        parent_layout.addWidget(self._section_label('👑  管理员设置'))
        group = self._form_group()
        gl = QVBoxLayout(group)

        hint = QLabel('管理员用户ID（每行一个）：')
        hint.setStyleSheet('color: #94A3B8; font-size: 12px; font-weight: normal;')
        gl.addWidget(hint)

        self.admin_list = QTextEdit()
        self.admin_list.setMaximumHeight(90)
        self.admin_list.setPlaceholderText('输入管理员 Telegram 用户ID...')
        admins = self.config.get('admins', [])
        self.admin_list.setPlainText('\n'.join(str(a) for a in admins))
        gl.addWidget(self.admin_list)

        parent_layout.addWidget(group)

    def _create_access_section(self, parent_layout):
        parent_layout.addWidget(self._section_label('🔒  访问控制'))
        group = self._form_group()
        gl = QVBoxLayout(group)
        gl.setSpacing(8)

        mode_row = QHBoxLayout()
        self.whitelist_mode = QCheckBox('白名单模式（仅允许列表内用户使用）')
        self.whitelist_mode.setChecked(
            self.config.get('storage', {}).get('whitelist_mode', False))
        self.whitelist_mode.setStyleSheet('font-weight: normal; color: #334155;')
        self.whitelist_mode.toggled.connect(self._on_mode_toggled)
        mode_row.addWidget(self.whitelist_mode)

        self.blacklist_mode = QCheckBox('黑名单模式（禁止列表内用户使用）')
        self.blacklist_mode.setChecked(
            self.config.get('storage', {}).get('blacklist_mode', True))
        self.blacklist_mode.setStyleSheet('font-weight: normal; color: #334155;')
        self.blacklist_mode.toggled.connect(self._on_blacklist_toggled)
        mode_row.addWidget(self.blacklist_mode)
        mode_row.addStretch()
        gl.addLayout(mode_row)

        gl.addWidget(QLabel('白名单用户ID（每行一个）：'))
        self.allowed_list = QTextEdit()
        self.allowed_list.setMaximumHeight(70)
        self.allowed_list.setPlaceholderText('输入允许访问的用户ID...')
        allowed = self.config.get('storage', {}).get('allowed_users', [])
        self.allowed_list.setPlainText('\n'.join(str(a) for a in allowed))
        gl.addWidget(self.allowed_list)

        gl.addWidget(QLabel('黑名单用户ID（每行一个）：'))
        self.blocked_list = QTextEdit()
        self.blocked_list.setMaximumHeight(70)
        self.blocked_list.setPlaceholderText('输入禁止访问的用户ID...')
        blocked = self.config.get('storage', {}).get('blocked_users', [])
        self.blocked_list.setPlainText('\n'.join(str(b) for b in blocked))
        gl.addWidget(self.blocked_list)

        parent_layout.addWidget(group)

    def _on_mode_toggled(self, checked):
        if checked:
            self.blacklist_mode.setChecked(False)

    def _on_blacklist_toggled(self, checked):
        if checked:
            self.whitelist_mode.setChecked(False)

    def _save_settings(self):
        try:
            self.config['proxy'] = {
                'enabled': self.proxy_enabled.isChecked(),
                'type': self.proxy_type.currentText(),
                'host': self.proxy_host.text().strip(),
                'port': self.proxy_port.value(),
            }

            if 'storage' not in self.config:
                self.config['storage'] = {}
            self.config['storage']['default_capacity_gb'] = self.storage_capacity.value()
            self.config['storage']['whitelist_mode'] = self.whitelist_mode.isChecked()
            self.config['storage']['blacklist_mode'] = self.blacklist_mode.isChecked()

            self.config['telethon'] = {
                'api_id': self.api_id_input.text().strip(),
                'api_hash': self.api_hash_input.text().strip(),
            }

            admin_text = self.admin_list.toPlainText().strip()
            self.config['admins'] = [
                int(a) for a in admin_text.split('\n') if a.strip().isdigit()]

            allowed_text = self.allowed_list.toPlainText().strip()
            self.config['storage']['allowed_users'] = [
                int(a) for a in allowed_text.split('\n') if a.strip().isdigit()]

            blocked_text = self.blocked_list.toPlainText().strip()
            self.config['storage']['blocked_users'] = [
                int(b) for b in blocked_text.split('\n') if b.strip().isdigit()]

            save_config(self.config)
            self.config_changed.emit()

            msg = QMessageBox(self)
            msg.setWindowTitle('成功')
            msg.setText('设置已保存！\n所有机器人将自动重启以应用新配置。')
            msg.setIcon(QMessageBox.Information)
            msg.setStyleSheet("""
                QMessageBox { background-color: white; }
                QMessageBox QLabel { color: #2C3E50; font-size: 14px; min-width: 200px; }
                QMessageBox QPushButton {
                    background-color: #4A90D9; color: white; padding: 8px 24px;
                    border-radius: 6px; font-size: 13px; min-width: 80px;
                }
                QMessageBox QPushButton:hover { background-color: #3B7EC9; }
            """)
            msg.exec_()
            logger.info('设置已保存')
        except Exception as e:
            msg = QMessageBox(self)
            msg.setWindowTitle('错误')
            msg.setText(f'保存失败：{e}')
            msg.setIcon(QMessageBox.Critical)
            msg.setStyleSheet("""
                QMessageBox { background-color: white; }
                QMessageBox QLabel { color: #2C3E50; font-size: 14px; }
                QMessageBox QPushButton {
                    background-color: #EF4444; color: white; padding: 8px 24px;
                    border-radius: 6px; font-size: 13px; min-width: 80px;
                }
            """)
            msg.exec_()
            logger.error(f'保存设置失败: {e}')

import os

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox,
    QSplitter, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QMenu, QAction, QProgressBar
)
from PyQt5.QtGui import QFont, QColor, QCursor

from utils.helpers import BOT_DIR, format_size, calculate_user_usage, delete_user_file, get_user_files
from utils.logger import logger


def _confirm(parent, title, text):
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


def _info(parent, title, text):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(QMessageBox.Information)
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
    box.exec_()


class FilesPage(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._init_ui()
        self._refresh_users()
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self._refresh_users)
        self._auto_refresh_timer.start(15000)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        title = QLabel('📁  文件管理')
        title.setFont(QFont('Microsoft YaHei', 18, QFont.Bold))
        title.setStyleSheet('color: #1E293B;')
        top_row.addWidget(title)

        top_row.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('🔍  搜索文件名...')
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 14px; border: 1px solid #E2E8F0;
                border-radius: 8px; font-size: 13px; min-width: 220px;
                color: #334155; background: white;
            }
            QLineEdit:focus { border: 2px solid #4A90D9; }
        """)
        self.search_input.textChanged.connect(self._on_search)
        top_row.addWidget(self.search_input)

        refresh_btn = QPushButton('🔄  刷新')
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9; color: #475569;
                padding: 8px 18px; border-radius: 8px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        refresh_btn.clicked.connect(self._refresh_users)
        top_row.addWidget(refresh_btn)

        layout.addLayout(top_row)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E2E8F0; }")

        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background: #FFFFFF; border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        left_header = QLabel('👥  用户列表')
        left_header.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        left_header.setStyleSheet('color: #1E293B; border: none; background: transparent;')
        left_layout.addWidget(left_header)

        self.user_tree = QTreeWidget()
        self.user_tree.setHeaderHidden(True)
        self.user_tree.setIndentation(16)
        self.user_tree.setStyleSheet("""
            QTreeWidget {
                border: none; background: transparent;
                font-size: 13px; color: #334155;
            }
            QTreeWidget::item {
                padding: 6px 8px; border-radius: 6px;
            }
            QTreeWidget::item:selected {
                background-color: #EBF4FF; color: #1E293B;
            }
            QTreeWidget::item:hover {
                background-color: #F8FAFC;
            }
        """)
        self.user_tree.itemClicked.connect(self._on_user_clicked)
        left_layout.addWidget(self.user_tree)

        left_info = QLabel('共 0 个用户')
        left_info.setStyleSheet(
            'color: #94A3B8; font-size: 11px; padding: 4px; border: none; background: transparent;')
        left_layout.addWidget(left_info)
        self.left_info_label = left_info

        splitter.addWidget(left_panel)

        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background: #FFFFFF; border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 12, 16, 12)
        right_layout.setSpacing(8)

        right_header = QHBoxLayout()
        self.file_title = QLabel('📄  选择一个用户查看文件')
        self.file_title.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        self.file_title.setStyleSheet('color: #1E293B; border: none; background: transparent;')
        right_header.addWidget(self.file_title)
        right_header.addStretch()

        self.delete_selected_btn = QPushButton('🗑  删除选中')
        self.delete_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2; color: #EF4444;
                padding: 6px 14px; border-radius: 6px;
                font-size: 12px; font-weight: bold; border: 1px solid #FECACA;
            }
            QPushButton:hover { background-color: #FECACA; }
        """)
        self.delete_selected_btn.clicked.connect(self._delete_selected_files)
        self.delete_selected_btn.setVisible(False)
        right_header.addWidget(self.delete_selected_btn)

        self.delete_all_btn = QPushButton('⚠ 清空全部')
        self.delete_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEF2F2; color: #DC2626;
                padding: 6px 14px; border-radius: 6px;
                font-size: 12px; font-weight: bold; border: 1px solid #FECACA;
            }
            QPushButton:hover { background-color: #FEE2E2; }
        """)
        self.delete_all_btn.clicked.connect(self._delete_all_files)
        self.delete_all_btn.setVisible(False)
        right_header.addWidget(self.delete_all_btn)

        right_layout.addLayout(right_header)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(['文件名', '大小', '修改时间', ''])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.file_table.setColumnWidth(3, 40)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self._show_context_menu)
        self.file_table.itemSelectionChanged.connect(self._on_selection_changed)
        right_layout.addWidget(self.file_table)

        right_info = QHBoxLayout()

        self.file_count_label = QLabel('')
        self.file_count_label.setStyleSheet(
            'color: #94A3B8; font-size: 12px; border: none; background: transparent;')
        right_info.addWidget(self.file_count_label)
        right_info.addStretch()

        usage_bar = QProgressBar()
        usage_bar.setMaximumHeight(8)
        usage_bar.setTextVisible(False)
        usage_bar.setStyleSheet("""
            QProgressBar {
                background-color: #F1F5F9; border: none; border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4A90D9, stop:1 #3B7EC9);
                border-radius: 4px;
            }
        """)
        right_info.addWidget(usage_bar)
        self.usage_bar = usage_bar

        self.usage_label = QLabel('')
        self.usage_label.setStyleSheet(
            'color: #64748B; font-size: 11px; border: none; background: transparent;')
        right_info.addWidget(self.usage_label)

        right_layout.addLayout(right_info)

        splitter.addWidget(right_panel)
        splitter.setSizes([260, 640])
        layout.addWidget(splitter, 1)

        self._current_user_id = None

    def _refresh_users(self):
        self.user_tree.clear()
        if not os.path.exists(BOT_DIR):
            self.left_info_label.setText('共 0 个用户')
            return

        user_dirs = []
        for uid in os.listdir(BOT_DIR):
            user_dir = os.path.join(BOT_DIR, uid)
            if os.path.isdir(user_dir):
                files = [f for f in os.listdir(user_dir)
                        if os.path.isfile(os.path.join(user_dir, f))]
                total_size = sum(os.path.getsize(os.path.join(user_dir, f))
                               for f in files)
                user_dirs.append((uid, len(files), total_size))

        user_dirs.sort(key=lambda x: x[0])

        for uid, file_count, total_size in user_dirs:
            item = QTreeWidgetItem()
            item.setText(0, f'👤  {uid}')
            item.setData(0, Qt.UserRole, uid)
            item.setToolTip(0, f'用户ID: {uid}\n文件数: {file_count}\n总大小: {format_size(total_size)}')

            child = QTreeWidgetItem(item)
            child.setText(0, f'📄  {file_count} 个文件')
            child.setData(0, Qt.UserRole, uid)
            child.setFlags(child.flags() & ~Qt.ItemIsSelectable)

            child2 = QTreeWidgetItem(item)
            child2.setText(0, f'💾  {format_size(total_size)}')
            child2.setData(0, Qt.UserRole, uid)
            child2.setFlags(child2.flags() & ~Qt.ItemIsSelectable)

            self.user_tree.addTopLevelItem(item)

        self.left_info_label.setText(f'共 {len(user_dirs)} 个用户')

    def _on_user_clicked(self, item, column):
        uid = item.data(0, Qt.UserRole)
        if uid:
            self._current_user_id = uid
            self._load_user_files(uid)

    def _load_user_files(self, uid):
        files = get_user_files(str(uid))
        search_text = self.search_input.text().strip().lower()

        if search_text:
            files = [f for f in files if search_text in f['name'].lower()]

        files.sort(key=lambda x: x['name'].lower())

        self.file_title.setText(f'📄  {uid} 的文件')

        cap_gb = self.config.get('storage', {}).get('default_capacity_gb', 1.0)
        total_used = calculate_user_usage(str(uid))
        cap_bytes = cap_gb * 1024 ** 3
        ratio = int((total_used / cap_bytes * 100) if cap_bytes > 0 else 0)
        self.usage_bar.setValue(min(ratio, 100))
        self.usage_label.setText(
            f'{format_size(total_used)} / {cap_gb} GB  ({ratio}%)')

        self.file_table.setRowCount(len(files))
        for row, f in enumerate(files):
            name_item = QTableWidgetItem(f['name'])
            name_item.setData(Qt.UserRole, f['name'])
            self.file_table.setItem(row, 0, name_item)

            size_item = QTableWidgetItem(format_size(f['size']))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.file_table.setItem(row, 1, size_item)

            mtime = os.path.getmtime(f['path'])
            from datetime import datetime
            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            time_item = QTableWidgetItem(mtime_str)
            self.file_table.setItem(row, 2, time_item)

            cb_item = QTableWidgetItem()
            cb_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            cb_item.setCheckState(Qt.Unchecked)
            self.file_table.setItem(row, 3, cb_item)

            self.file_table.setRowHeight(row, 34)

        self.file_count_label.setText(
            f'共 {len(files)} 个文件  |  '
            f'总大小: {format_size(sum(f["size"] for f in files))}'
        )

        has_files = len(files) > 0
        self.delete_selected_btn.setVisible(has_files)
        self.delete_all_btn.setVisible(has_files)

    def _on_search(self, text):
        if self._current_user_id:
            self._load_user_files(self._current_user_id)

    def _on_selection_changed(self):
        pass

    def _get_checked_files(self):
        checked = []
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 3)
            name_item = self.file_table.item(row, 0)
            if item and item.checkState() == Qt.Checked and name_item:
                checked.append(name_item.data(Qt.UserRole))
        return checked

    def _delete_selected_files(self):
        if not self._current_user_id:
            return
        checked = self._get_checked_files()
        if not checked:
            _info(self, '提示', '请先勾选要删除的文件')
            return

        if _confirm(self, '确认删除',
                    f'确定要删除选中的 {len(checked)} 个文件吗？\n此操作不可恢复！'):
            for filename in checked:
                delete_user_file(str(self._current_user_id), filename)
                logger.info(f'删除文件: {self._current_user_id}/{filename}')
            self._load_user_files(self._current_user_id)
            self._refresh_users()

    def _delete_all_files(self):
        if not self._current_user_id:
            return
        if _confirm(self, '⚠ 危险操作',
                    f'确定要清空用户 {self._current_user_id} 的所有文件吗？\n此操作不可恢复！'):
            files = get_user_files(str(self._current_user_id))
            for f in files:
                delete_user_file(str(self._current_user_id), f['name'])
            logger.info(f'清空用户文件: {self._current_user_id}')
            self._load_user_files(self._current_user_id)
            self._refresh_users()

    def _show_context_menu(self, pos):
        if not self._current_user_id:
            return
        row = self.file_table.rowAt(pos.y())
        if row < 0:
            return
        name_item = self.file_table.item(row, 0)
        if not name_item:
            return
        filename = name_item.data(Qt.UserRole)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white; border: 1px solid #E2E8F0; border-radius: 8px;
                padding: 4px;
            }
            QMenu::item { padding: 8px 24px; font-size: 13px; color: #334155; }
            QMenu::item:selected { background: #EBF4FF; border-radius: 4px; }
            QMenu::separator { height: 1px; background: #E2E8F0; margin: 4px 8px; }
        """)

        delete_action = QAction('🗑  删除此文件', menu)
        delete_action.triggered.connect(
            lambda: self._delete_single_file(filename))
        menu.addAction(delete_action)

        menu.addSeparator()

        select_all_action = QAction('✅  全选', menu)
        select_all_action.triggered.connect(self._select_all_files)
        menu.addAction(select_all_action)

        deselect_all_action = QAction('⬜  取消全选', menu)
        deselect_all_action.triggered.connect(self._deselect_all_files)
        menu.addAction(deselect_all_action)

        menu.exec_(QCursor.pos())

    def _delete_single_file(self, filename):
        if not self._current_user_id:
            return
        if _confirm(self, '确认删除', f'确定要删除 "{filename}" 吗？'):
            delete_user_file(str(self._current_user_id), filename)
            logger.info(f'删除文件: {self._current_user_id}/{filename}')
            self._load_user_files(self._current_user_id)
            self._refresh_users()

    def _select_all_files(self):
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 3)
            if item:
                item.setCheckState(Qt.Checked)

    def _deselect_all_files(self):
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 3)
            if item:
                item.setCheckState(Qt.Unchecked)

from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy
)
from PyQt5.QtGui import QFont

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

from utils.helpers import format_size, calculate_total_usage
from utils.logger import logger


class PieChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(3.2, 3.2), dpi=90, facecolor='none')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet('background: transparent;')
        self.ax = self.figure.add_subplot(111)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setMinimumHeight(250)

    def update_chart(self, used, total, used_label='', total_label=''):
        self.ax.clear()
        if total <= 0:
            total = 1
        sizes = [used, max(0, total - used)]
        colors = ['#3B82F6', '#E5E7EB']
        explode = (0.04, 0)

        self.ax.pie(
            sizes, labels=None, colors=colors, explode=explode,
            startangle=90, pctdistance=0.6,
            wedgeprops={'edgecolor': 'white', 'linewidth': 3, 'antialiased': True}
        )

        self.ax.add_artist(
            matplotlib.patches.Circle((0, 0), 0.58, fc='white', ec='#F3F4F6', linewidth=1)
        )
        pct = (used / total * 100) if total > 0 else 0
        self.ax.text(0, 0.06, f'{pct:.1f}%', ha='center', va='center',
                     fontsize=20, fontweight='bold', color='#111827')
        self.ax.text(0, -0.18, '已使用', ha='center', va='center',
                     fontsize=9, color='#9CA3AF')

        for i, (label, c) in enumerate(zip(
            [f'已用 {used_label}', f'可用 {total_label}'],
            ['#3B82F6', '#9CA3AF']
        )):
            self.ax.text(-1.35, 0.7 - i * 0.28, '●', fontsize=10, color=c, va='center')
            self.ax.text(-1.18, 0.7 - i * 0.28, label, fontsize=8, color='#6B7280', va='center')

        self.ax.set_aspect('equal')
        self.ax.set_xlim(-1.5, 1.5)
        self.figure.patch.set_alpha(0)
        self.figure.tight_layout(pad=0.3)
        self.canvas.draw()


class LineChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5.2, 3.2), dpi=90, facecolor='none')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet('background: transparent;')
        self.ax = self.figure.add_subplot(111)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setMinimumHeight(250)

    def update_chart(self, upload_data, download_data):
        self.ax.clear()
        self.ax.set_facecolor('none')

        if upload_data:
            times_u = [datetime.fromtimestamp(x[0]).strftime('%M:%S')
                       for x in upload_data]
            vals_u = [x[1] for x in upload_data]
            self.ax.fill_between(range(len(times_u)), vals_u, alpha=0.08,
                                 color='#3B82F6')
            self.ax.plot(times_u, vals_u, color='#3B82F6', linewidth=2,
                         marker='o', markersize=3, label='上传', zorder=5)

        if download_data:
            times_d = [datetime.fromtimestamp(x[0]).strftime('%M:%S')
                       for x in download_data]
            vals_d = [x[1] for x in download_data]
            self.ax.fill_between(range(len(times_d)), vals_d, alpha=0.08,
                                 color='#10B981')
            self.ax.plot(times_d, vals_d, color='#10B981', linewidth=2,
                         marker='o', markersize=3, label='下载', zorder=5)

        self.ax.tick_params(axis='x', rotation=30, labelsize=7, colors='#9CA3AF')
        self.ax.tick_params(axis='y', labelsize=8, colors='#9CA3AF')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#E5E7EB')
        self.ax.spines['bottom'].set_color('#E5E7EB')
        if upload_data or download_data:
            self.ax.legend(loc='upper left', fontsize=8, framealpha=0.4,
                           edgecolor='#E5E7EB')
        self.ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.5)
        self.figure.patch.set_alpha(0)
        self.figure.tight_layout(pad=1)
        self.canvas.draw()


class StatCard(QFrame):
    _icons = {
        'total_upload': '📤', 'total_download': '📥',
        'upload_10min': '⚡', 'download_10min': '🔻'
    }

    def __init__(self, key, title, color, parent=None):
        super().__init__(parent)
        self._key = key
        self.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }}
        """)
        self.setMinimumHeight(72)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        icon_label = QLabel(self._icons.get(key, '📊'))
        icon_label.setFont(QFont('Segoe UI Emoji', 18))
        icon_label.setFixedWidth(36)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet('border: none; background: transparent;')
        layout.addWidget(icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)

        tl = QLabel(title)
        tl.setStyleSheet(
            'color: #9CA3AF; font-size: 11px; border: none; background: transparent;')
        text_col.addWidget(tl)

        self.value_label = QLabel('0 B')
        self.value_label.setStyleSheet(
            'color: #111827; font-size: 18px; font-weight: 700; '
            'border: none; background: transparent;')
        text_col.addWidget(self.value_label)

        layout.addLayout(text_col)

    def set_value(self, text):
        self.value_label.setText(text)


class DashboardPage(QWidget):
    def __init__(self, config, bot_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.bot_manager = bot_manager
        self.bot_manager.stats_updated.connect(self.on_stats_updated)
        self._init_ui()

        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:0.5 #6366F1, stop:1 #8B5CF6);
                border-radius: 12px;
            }
        """)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(24, 14, 24, 14)
        self.welcome_label = QLabel()
        self.welcome_label.setFont(QFont('Microsoft YaHei', 17, QFont.Bold))
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet(
            'color: #FFFFFF; background: transparent; border: none;')
        header_layout.addWidget(self.welcome_label)
        layout.addWidget(header_card)
        self._update_time()

        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.stat_cards = {}
        card_defs = [
            ('total_upload', '总上传量', '#3B82F6'),
            ('total_download', '总下载量', '#10B981'),
            ('upload_10min', '10分钟上传', '#F59E0B'),
            ('download_10min', '10分钟下载', '#8B5CF6'),
        ]
        for key, title, color in card_defs:
            card = StatCard(key, title, color)
            self.stat_cards[key] = card
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(14)

        for chart_title, widget_class, label_key in [
            ('📊  存储使用量', PieChartWidget, 'pie'),
            ('📈  网络使用量', LineChartWidget, 'line'),
        ]:
            card = QFrame()
            card.setStyleSheet(
                'background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;')
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            cl.setSpacing(4)

            ct = QLabel(chart_title)
            ct.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
            ct.setStyleSheet(
                'color: #111827; border: none; background: transparent;')
            cl.addWidget(ct)

            if label_key == 'pie':
                self.pie_chart = widget_class()
                cl.addWidget(self.pie_chart)
                self.pie_label = QLabel('[0 B / 1 GB]')
                self.pie_label.setAlignment(Qt.AlignCenter)
                self.pie_label.setStyleSheet(
                    'color: #9CA3AF; font-size: 12px; padding: 2px; '
                    'border: none; background: transparent;')
                cl.addWidget(self.pie_label)
            else:
                self.line_chart = widget_class()
                cl.addWidget(self.line_chart)
                self.line_label = QLabel('[10min内: 上传0B / 下载0B]')
                self.line_label.setAlignment(Qt.AlignCenter)
                self.line_label.setStyleSheet(
                    'color: #9CA3AF; font-size: 12px; padding: 2px; '
                    'border: none; background: transparent;')
                cl.addWidget(self.line_label)

            charts_layout.addWidget(card, 1)

        layout.addLayout(charts_layout, 1)

        self.pie_chart.update_chart(0, 1, '0 B', '1 GB')
        self.line_chart.update_chart([], [])

    def _update_time(self):
        now = datetime.now().strftime('%Y年%m月%d日  %H:%M:%S')
        self.welcome_label.setText(f'🎉  欢迎使用清风网盘    {now}  🎉')

    def on_stats_updated(self, stats):
        try:
            cap_gb = self.config.get('storage', {}).get('default_capacity_gb', 1.0)
            total_used = calculate_total_usage()
            total_bytes = cap_gb * 1024 ** 3
            avail = max(0, total_bytes - total_used)

            self.pie_chart.update_chart(total_used, total_bytes,
                                        format_size(total_used), format_size(avail))
            self.pie_label.setText(
                f'[ {format_size(total_used)} / {format_size(total_bytes)} ]')

            up_data = stats.get('last_10min_upload', [])
            down_data = stats.get('last_10min_download', [])
            self.line_chart.update_chart(up_data, down_data)

            up_10 = sum(x[1] for x in up_data)
            down_10 = sum(x[1] for x in down_data)
            self.line_label.setText(
                f'[ 10min内: 上传 {format_size(up_10)}  /  '
                f'下载 {format_size(down_10)} ]')

            self.stat_cards['total_upload'].set_value(
                format_size(stats.get('total_upload_bytes', 0)))
            self.stat_cards['total_download'].set_value(
                format_size(stats.get('total_download_bytes', 0)))
            self.stat_cards['upload_10min'].set_value(format_size(up_10))
            self.stat_cards['download_10min'].set_value(format_size(down_10))
        except Exception as e:
            logger.error(f'更新仪表盘失败: {e}')

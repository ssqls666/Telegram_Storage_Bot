from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect


class ThemeManager:
    def __init__(self, config):
        self.config = config
        self.theme = config.get('theme', {})

    def get(self, key, default=None):
        return self.theme.get(key, default)

    def set(self, key, value):
        self.theme[key] = value

    def main_style(self):
        t = self.theme
        return f"""
        QMainWindow {{
            background-color: {t.get('background_color', '#F0F2F5')};
        }}
        QMainWindow QLabel {{
            color: {t.get('text_color', '#2C3E50')};
        }}
        QMainWindow QGroupBox {{
            font-size: 14px;
            font-weight: bold;
            border: 1px solid {t.get('border_color', '#E2E8F0')};
            border-radius: 10px;
            margin-top: 14px;
            padding-top: 18px;
            background-color: {t.get('card_color', '#FFFFFF')};
        }}
        QMainWindow QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 8px;
            color: {t.get('text_color', '#2C3E50')};
        }}
        QMainWindow QLineEdit, QMainWindow QSpinBox, QMainWindow QDoubleSpinBox, QMainWindow QComboBox {{
            padding: 8px 12px;
            border: 1px solid {t.get('border_color', '#E2E8F0')};
            border-radius: 6px;
            background-color: #FFFFFF;
            font-size: 13px;
            color: {t.get('text_color', '#2C3E50')};
        }}
        QMainWindow QLineEdit:focus, QMainWindow QSpinBox:focus, QMainWindow QDoubleSpinBox:focus, QMainWindow QComboBox:focus {{
            border: 2px solid {t.get('primary_color', '#4A90D9')};
        }}
        QMainWindow QTextEdit {{
            padding: 8px;
            border: 1px solid {t.get('border_color', '#E2E8F0')};
            border-radius: 6px;
            background-color: #FFFFFF;
            font-size: 13px;
            color: {t.get('text_color', '#2C3E50')};
        }}
        QMainWindow QTableWidget {{
            border: 1px solid {t.get('border_color', '#E2E8F0')};
            border-radius: 8px;
            gridline-color: #F1F5F9;
            background-color: #FFFFFF;
            selection-background-color: #EBF4FF;
            selection-color: {t.get('text_color', '#2C3E50')};
        }}
        QMainWindow QTableWidget::item {{
            padding: 8px 12px;
            border-bottom: 1px solid #F8FAFC;
        }}
        QMainWindow QHeaderView::section {{
            background-color: #F8FAFC;
            padding: 10px 12px;
            border: none;
            border-bottom: 2px solid {t.get('border_color', '#E2E8F0')};
            font-weight: bold;
            color: {t.get('text_secondary', '#64748B')};
        }}
        QMainWindow QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 6px;
            margin: 2px;
        }}
        QMainWindow QScrollBar::handle:vertical {{
            background: #CBD5E1;
            border-radius: 3px;
            min-height: 30px;
        }}
        QMainWindow QScrollBar::handle:vertical:hover {{
            background: #94A3B8;
        }}
        QMainWindow QScrollBar::add-line:vertical, QMainWindow QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QMainWindow QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 6px;
            margin: 2px;
        }}
        QMainWindow QScrollBar::handle:horizontal {{
            background: #CBD5E1;
            border-radius: 3px;
            min-width: 30px;
        }}
        QMainWindow QScrollBar::add-line:horizontal, QMainWindow QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QMainWindow QCheckBox {{
            spacing: 8px;
            font-size: 13px;
            color: {t.get('text_color', '#2C3E50')};
        }}
        QMainWindow QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid #CBD5E1;
            border-radius: 4px;
            background: white;
        }}
        QMainWindow QCheckBox::indicator:checked {{
            background-color: {t.get('primary_color', '#4A90D9')};
            border-color: {t.get('primary_color', '#4A90D9')};
        }}
        QMainWindow QComboBox::drop-down {{
            border: none;
            padding-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid {t.get('border_color', '#E2E8F0')};
            border-radius: 6px;
            background-color: #FFFFFF;
            selection-background-color: #EBF4FF;
            color: {t.get('text_color', '#2C3E50')};
            padding: 4px;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 6px 12px;
            min-height: 28px;
            color: {t.get('text_color', '#2C3E50')};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: #EBF4FF;
            color: {t.get('text_color', '#2C3E50')};
        }}
        """

    def button_style(self, bg='#4A90D9', hover='#3B7EC9', color='white'):
        return f"""
        QPushButton {{
            background-color: {bg};
            color: {color};
            border: none;
            padding: 9px 20px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background-color: {bg};
        }}
        """

    @staticmethod
    def danger_button_style():
        return """
        QPushButton {
            background-color: #EF4444;
            color: white;
            border: none;
            padding: 9px 20px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #DC2626;
        }
        """

    @staticmethod
    def success_button_style():
        return """
        QPushButton {
            background-color: #22C55E;
            color: white;
            border: none;
            padding: 9px 20px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #16A34A;
        }
        """

    @staticmethod
    def outline_button_style():
        return """
        QPushButton {
            background-color: transparent;
            color: #4A90D9;
            border: 2px solid #4A90D9;
            padding: 7px 18px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #EBF4FF;
        }
        """

    def card_style(self):
        return """
        QFrame {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
        }
        """

    def stat_card_style(self, color='#4A90D9'):
        return f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {color}15, stop:1 #FFFFFF);
            border: 1px solid #E2E8F0;
            border-left: 4px solid {color};
            border-radius: 10px;
        }}
        """

    def save(self):
        self.config['theme'] = self.theme


def animate_fade_in(widget, duration=400):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(0)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0)
    anim.setEndValue(1)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start()
    return anim


def animate_slide_up(widget, duration=400, delay=0):
    geo = widget.geometry()
    widget.move(geo.x(), geo.y() + 30)
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration)
    anim.setStartValue(widget.pos())
    anim.setEndValue(QPoint(geo.x(), geo.y()))
    anim.setEasingCurve(QEasingCurve.OutBack)
    if delay > 0:
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(delay, anim.start)
    else:
        anim.start()
    return anim


def animate_sequential(animations, interval=80):
    group = QParallelAnimationGroup()
    current_delay = 0
    for anim in animations:
        if hasattr(anim, 'setCurrentTime'):
            anim.setStartDelay(current_delay)
            current_delay += interval
        group.addAnimation(anim) if hasattr(group, 'addAnimation') else None
    return group

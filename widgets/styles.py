from utils.constants import *


def style_app():
    return f"""
    QWidget {{
        background-color: {DARK};
        color: {TEXT};
        font-family: 'Segoe UI', 'Ubuntu', 'Roboto', sans-serif;
        font-size: 13px;
    }}

    QMainWindow {{
        background-color: {DARK};
    }}

    QFrame {{
        border: none;
    }}

    QScrollBar:vertical {{
        background: {SURFACE};
        width: 10px;
        border-radius: 5px;
    }}

    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {ACCENT};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background: {SURFACE};
        height: 10px;
        border-radius: 5px;
    }}

    QScrollBar::handle:horizontal {{
        background: {BORDER};
        border-radius: 5px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {ACCENT};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    QToolTip {{
        background: {SURFACE3};
        color: {TEXT};
        border: 1px solid {BORDER};
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
    }}

    QMenuBar {{
        background: {SURFACE};
        border-bottom: 1px solid {BORDER};
        padding: 4px;
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 6px 12px;
        border-radius: 4px;
    }}

    QMenuBar::item:selected {{
        background: {SURFACE2};
    }}

    QMenu {{
        background: {SURFACE2};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 4px;
    }}

    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        background: {ACCENT};
        color: white;
    }}

    QMenu::separator {{
        height: 1px;
        background: {BORDER};
        margin: 4px 0;
    }}

    QMessageBox {{
        background: {SURFACE};
    }}

    QMessageBox QLabel {{
        color: {TEXT};
        font-size: 13px;
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
        min-height: 28px;
    }}
    """


def button_style(bg=SURFACE3, fg=TEXT, hover=SURFACE2, border=BORDER,
                 radius=8, padding="8px 16px", font_weight=600):
    return f"""
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: {radius}px;
        padding: {padding};
        font-weight: {font_weight};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {hover};
        border-color: {ACCENT};
    }}
    QPushButton:pressed {{
        background-color: {ACCENT};
        color: white;
    }}
    QPushButton:disabled {{
        background-color: {SURFACE};
        color: {TEXT2};
        border-color: {SURFACE2};
    }}
    QPushButton:checked {{
        background-color: {ACCENT}22;
        border-color: {ACCENT};
        color: {ACCENT};
    }}
    """


def input_style():
    return f"""
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit, QTimeEdit {{
        background-color: {SURFACE2};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px 12px;
        selection-background-color: {ACCENT};
        selection-color: white;
        font-size: 13px;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, 
    QTextEdit:focus, QDateEdit:focus, QTimeEdit:focus {{
        border-color: {ACCENT};
        background-color: {SURFACE3};
    }}
    QLineEdit:read-only {{
        background-color: {SURFACE};
        color: {TEXT2};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 4px solid {TEXT2};
        width: 0;
        height: 0;
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background: {SURFACE2};
        border: 1px solid {BORDER};
        selection-background-color: {ACCENT};
        selection-color: white;
        color: {TEXT};
        outline: none;
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button {{
        background: transparent;
        border: none;
        width: 20px;
        height: 12px;
    }}
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background: transparent;
        border: none;
        width: 20px;
        height: 12px;
    }}
    """


def table_style():
    return f"""
    QTableWidget {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        gridline-color: {SURFACE2};
        outline: none;
    }}
    QTableWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {SURFACE2};
        color: {TEXT};
    }}
    QTableWidget::item:selected {{
        background-color: {ACCENT}22;
        color: {TEXT};
    }}
    QTableWidget::item:hover {{
        background-color: {SURFACE2};
    }}
    QHeaderView::section {{
        background-color: {SURFACE2};
        color: {TEXT2};
        border: none;
        border-bottom: 1px solid {BORDER};
        padding: 10px 12px;
        font-weight: 700;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    QHeaderView::section:hover {{
        background-color: {SURFACE3};
    }}
    QTableCornerButton::section {{
        background-color: {SURFACE2};
        border: none;
    }}
    """


def tab_style():
    return f"""
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        background: {SURFACE};
        top: -1px;
    }}
    QTabBar::tab {{
        background: {SURFACE2};
        color: {TEXT2};
        border: 1px solid {BORDER};
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
        margin-right: 2px;
        font-weight: 600;
        font-size: 12px;
    }}
    QTabBar::tab:hover {{
        background: {SURFACE3};
        color: {TEXT};
    }}
    QTabBar::tab:selected {{
        background: {ACCENT};
        color: white;
        border-color: {ACCENT};
    }}
    QTabBar::tab:disabled {{
        background: {SURFACE};
        color: {TEXT2};
        border-color: {SURFACE2};
    }}
    """
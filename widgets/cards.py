from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QLinearGradient
from widgets.buttons import GhostButton, DangerButton
from utils.constants import *
from utils.helpers import format_currency


class Card(QFrame):
    """Base card widget with consistent styling"""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class TableCard(QFrame):
    """Card representing a table in the floor plan"""

    clicked = Signal(int)

    def __init__(self, table_id, number, capacity, status, order_info=None):
        super().__init__()
        self.table_id = table_id
        self.number = number
        self.capacity = capacity
        self.status = status
        self.order_info = order_info
        self.setFixedSize(160, 140)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self):
        color = STATUS_COLORS.get(self.status, TEXT2)
        self.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 2px solid {color};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background: {SURFACE2};
                border-color: {ACCENT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        # Table number
        num_lbl = QLabel(f"Table {self.number}")
        num_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEXT}; border: none;")
        num_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(num_lbl)

        # Capacity
        cap_lbl = QLabel(f"👥 {self.capacity} seats")
        cap_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT2}; border: none;")
        cap_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(cap_lbl)

        # Status badge
        badge = Badge(self.status.upper(), color)
        layout.addWidget(badge)

        # Order info
        if self.order_info:
            info = QLabel(f"#{self.order_info['id']} · {self.order_info['items']} items")
            info.setStyleSheet(f"font-size: 10px; color: {TEXT2}; border: none;")
            info.setAlignment(Qt.AlignCenter)
            layout.addWidget(info)

            amt = QLabel(f"${self.order_info['total']:.2f}")
            amt.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {color}; border: none;")
            amt.setAlignment(Qt.AlignCenter)
            layout.addWidget(amt)

    def mousePressEvent(self, event):
        self.clicked.emit(self.table_id)


class Badge(QLabel):
    """Status badge with color coding"""

    def __init__(self, text, color=ACCENT, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}22;
                color: {color};
                border: 1px solid {color}55;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)


class MetricCard(Card):
    """Card for displaying metrics/statistics"""

    def __init__(self, title, value, subtitle="", icon="", color=ACCENT, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.ArrowCursor)
        self.setFixedHeight(100)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Icon
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"""
                QLabel {{
                    background: {color}22;
                    color: {color};
                    border-radius: 20px;
                    padding: 8px;
                    font-size: 20px;
                    min-width: 40px;
                    max-width: 40px;
                    min-height: 40px;
                    max-height: 40px;
                    qproperty-alignment: AlignCenter;
                }}
            """)
            layout.addWidget(icon_label)

        # Content
        content = QVBoxLayout()
        content.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px; font-weight: 600;")
        content.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 800;")
        content.addWidget(value_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet(f"color: {TEXT2}; font-size: 11px;")
            content.addWidget(sub_label)

        layout.addLayout(content, 1)


class InfoCard(Card):
    """Card for displaying information with actions"""

    def __init__(self, title, content="", parent=None):
        super().__init__(parent)
        self.setCursor(Qt.ArrowCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT2}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        layout.addWidget(title_label)

        # Content
        self.content_label = QLabel(content)
        self.content_label.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600;")
        self.content_label.setWordWrap(True)
        layout.addWidget(self.content_label)

        # Actions (can be added later)
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setContentsMargins(0, 8, 0, 0)
        self.actions_layout.setSpacing(8)
        layout.addLayout(self.actions_layout)

    def set_content(self, content):
        self.content_label.setText(content)

    def add_action(self, button):
        self.actions_layout.addWidget(button)


class OrderCard(Card):
    """Card for displaying order information"""

    status_changed = Signal(int, str)

    def __init__(self, order_data, items_data, parent=None):
        super().__init__(parent)
        self.order_id = order_data['id']
        self.setCursor(Qt.ArrowCursor)
        self._build(order_data, items_data)

    def _build(self, order, items):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()

        # Table info
        table_text = f"Table {order['table_number']}" if not order.get('is_takeaway') else "Takeaway"
        table_label = QLabel(table_text)
        table_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEXT};")
        header.addWidget(table_label)

        # Order number
        order_label = QLabel(f"#{order['id']}")
        order_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        header.addWidget(order_label)

        header.addStretch()

        # Status badge
        status_color = ORDER_STATUS_COLORS.get(order['status'], TEXT2)
        badge = Badge(order['status'].upper(), status_color)
        header.addWidget(badge)

        layout.addLayout(header)

        # Time and waiter
        info_layout = QHBoxLayout()

        time_label = QLabel(f"🕐 {order['created_at'][11:16]}")
        time_label.setStyleSheet(f"color: {TEXT2}; font-size: 11px;")
        info_layout.addWidget(time_label)

        if order['waiter']:
            waiter_label = QLabel(f"👤 {order['waiter']}")
            waiter_label.setStyleSheet(f"color: {TEXT2}; font-size: 11px;")
            info_layout.addWidget(waiter_label)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Items
        items_label = QLabel(f"{len(items)} items • Total: {format_currency(order['total'])}")
        items_label.setStyleSheet(f"color: {ACCENT}; font-size: 14px; font-weight: 600;")
        layout.addWidget(items_label)

        # Item list (first 3 items)
        for i, item in enumerate(items[:3]):
            item_text = f"×{item['quantity']} {item['name']}"
            if i < 2 or len(items) <= 3:
                item_label = QLabel(item_text)
                item_label.setStyleSheet(f"color: {TEXT2}; font-size: 11px;")
                layout.addWidget(item_label)

        if len(items) > 3:
            more_label = QLabel(f"...and {len(items) - 3} more")
            more_label.setStyleSheet(f"color: {TEXT2}; font-size: 11px; font-style: italic;")
            layout.addWidget(more_label)

        if order.get('notes'):
            note_label = QLabel(f"📝 {order['notes']}")
            note_label.setStyleSheet(f"color: {YELLOW}; font-size: 11px;")
            note_label.setWordWrap(True)
            layout.addWidget(note_label)

        layout.addStretch()


class MenuItemRow(QFrame):
    """Row widget for menu items in order view"""

    add_clicked = Signal(int, str, float)

    def __init__(self, item_id, name, description, price):
        super().__init__()
        self.item_id = item_id
        self.item_name = name
        self.item_price = price
        self.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE2};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {ACCENT};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        info = QVBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"font-weight: 600; color: {TEXT}; border: none;")
        info.addWidget(name_lbl)

        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT2}; border: none;")
            info.addWidget(desc_lbl)

        layout.addLayout(info, 1)

        price_lbl = QLabel(f"${price:.2f}")
        price_lbl.setStyleSheet(f"font-weight: 700; color: {ACCENT}; border: none; font-size: 14px;")
        layout.addWidget(price_lbl)

        add_btn = QPushButton("＋")
        add_btn.setFixedSize(32, 32)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 18px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {ACCENT2};
            }}
        """)
        add_btn.clicked.connect(lambda: self.add_clicked.emit(self.item_id, self.item_name, self.item_price))
        layout.addWidget(add_btn)

    def mousePressEvent(self, event):
        self.add_clicked.emit(self.item_id, self.item_name, self.item_price)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                               QGridLayout, QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal, QDateTime
from database.connection import get_db
from widgets.cards import TableCard, Badge
from widgets.buttons import GhostButton
from database.models import Table, Order
from utils.constants import *
from utils.helpers import format_currency


class FloorView(QWidget):
    table_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = self._create_header()
        layout.addLayout(header)

        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {BORDER};")
        layout.addWidget(divider)

        # Floor plan
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.floor_container = QWidget()
        self.floor_container.setStyleSheet("background: transparent;")
        self.floor_layout = QGridLayout(self.floor_container)
        self.floor_layout.setSpacing(TABLE_SPACING)
        self.floor_layout.setContentsMargins(20, 20, 20, 20)

        self.scroll_area.setWidget(self.floor_container)
        layout.addWidget(self.scroll_area)

        self.refresh()

    def _create_header(self):
        header = QHBoxLayout()

        # Title
        title = QLabel("🍽 Floor Plan")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)

        header.addStretch()

        # Legend
        legend = QHBoxLayout()
        legend.setSpacing(8)

        for status, color in STATUS_COLORS.items():
            badge = Badge(status.capitalize(), color)
            legend.addWidget(badge)

        # Add reservation to legend
        res_badge = Badge("Reserved", BLUE)
        legend.addWidget(res_badge)

        header.addLayout(legend)

        # Refresh button
        refresh_btn = GhostButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        return header

    def refresh(self):
        """Refresh the floor plan display with orders and reservations"""
        # Clear existing cards
        while self.floor_layout.count():
            item = self.floor_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get all tables
        tables = Table.get_all()

        # Get active orders
        conn = get_db()
        active_orders = conn.execute("""
                                     SELECT o.table_id,
                                            o.id,
                                            o.total,
                                            o.status,
                                            COUNT(oi.id) as item_count
                                     FROM orders o
                                              LEFT JOIN order_items oi ON o.id = oi.order_id
                                     WHERE o.status NOT IN ('paid', 'cancelled')
                                     GROUP BY o.id
                                     ORDER BY o.id DESC
                                     """).fetchall()

        # Get today's active reservations (confirmed or pending)
        today = QDateTime.currentDateTime().toString("yyyy-MM-dd")
        active_reservations = conn.execute("""
                                           SELECT r.table_id,
                                                  r.id,
                                                  r.customer_name,
                                                  r.party_size,
                                                  r.reservation_time,
                                                  r.status
                                           FROM reservations r
                                           WHERE DATE (r.reservation_time) = DATE (?)
                                             AND r.status IN ('confirmed'
                                               , 'pending')
                                           ORDER BY r.reservation_time
                                           """, (today,)).fetchall()

        conn.close()

        # Create order map
        order_map = {}
        for order in active_orders:
            if order['table_id'] not in order_map:
                order_map[order['table_id']] = {
                    'id': order['id'],
                    'total': order['total'],
                    'items': order['item_count'],
                    'status': order['status']
                }

        # Create reservation map
        reservation_map = {}
        for res in active_reservations:
            if res['table_id']:  # Only if table is assigned
                res_time = QDateTime.fromString(res['reservation_time'], Qt.ISODate)
                time_str = res_time.toString("hh:mm AP")
                reservation_map[res['table_id']] = {
                    'id': res['id'],
                    'customer': res['customer_name'],
                    'party': res['party_size'],
                    'time': time_str,
                    'status': res['status']
                }

        # Add tables to grid
        cols = 4
        for idx, table in enumerate(tables):
            card = TableCard(
                table.id,
                table.number,
                table.capacity,
                table.status,
                order_map.get(table.id),
                reservation_map.get(table.id)
            )
            card.clicked.connect(lambda tid=table.id: self.table_selected.emit(tid))

            row = idx // cols
            col = idx % cols
            self.floor_layout.addWidget(card, row, col, Qt.AlignCenter)

    def handle_resize(self, width):
        """Handle window resize for responsive layout"""
        if width < BREAKPOINT_SMALL:
            cols = 3
        elif width < BREAKPOINT_MEDIUM:
            cols = 4
        else:
            cols = 5

        # Reorganize grid
        cards = []
        for i in range(self.floor_layout.count()):
            item = self.floor_layout.itemAt(i)
            if item and item.widget():
                cards.append(item.widget())

        # Clear and re-add with new column count
        while self.floor_layout.count():
            self.floor_layout.takeAt(0)

        for idx, card in enumerate(cards):
            row = idx // cols
            col = idx % cols
            self.floor_layout.addWidget(card, row, col, Qt.AlignCenter)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QScrollArea, QFrame, QPushButton)
from PySide6.QtCore import Qt, QTimer, Signal
from widgets.buttons import GhostButton
from widgets.cards import OrderCard
from utils.constants import *
from database.connection import get_db


class KitchenView(QWidget):
    """Kitchen Display System — fully corrected."""

    def __init__(self):
        super().__init__()
        # Initialize self.columns BEFORE _build() calls _create_column()
        self.columns = []
        self._build()
        self._setup_auto_refresh()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        layout.addLayout(self._create_header())

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {BORDER};")
        layout.addWidget(divider)

        # Column header labels
        col_hdr = QHBoxLayout()
        col_hdr.setSpacing(16)
        for label, color in [
            ("📨  NEW ORDERS", BLUE),
            ("🍳  PREPARING", YELLOW),
            ("✅  READY TO SERVE", GREEN),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"""
                color: {color};
                font-weight: 700;
                font-size: 13px;
                padding: 6px;
                background: {SURFACE2};
                border-radius: 6px;
            """)
            lbl.setAlignment(Qt.AlignCenter)
            col_hdr.addWidget(lbl, 1)
        layout.addLayout(col_hdr)

        # Three order columns
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(16)
        for statuses in [["sent"], ["preparing"], ["ready"]]:
            col_widget = self._create_column(statuses)
            cols_layout.addWidget(col_widget, 1)
        layout.addLayout(cols_layout, 1)

    def _create_header(self):
        header = QHBoxLayout()

        title = QLabel("🍳 Kitchen Display")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)

        header.addStretch()

        self.stats_label = QLabel("Orders: 0")
        self.stats_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        header.addWidget(self.stats_label)

        refresh_btn = GhostButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        return header

    def _create_column(self, statuses: list) -> QWidget:
        """Build one kanban column; register it in self.columns."""
        # Outer scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background: {SURFACE};
            }}
            QScrollBar:vertical {{
                background: {SURFACE};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        container = QWidget()
        container.setStyleSheet(f"background: {DARK};")

        col_layout = QVBoxLayout(container)
        col_layout.setSpacing(8)
        col_layout.setContentsMargins(8, 8, 8, 8)
        # Add stretch at the bottom so cards are added from the top
        col_layout.addStretch()

        scroll.setWidget(container)

        # Store reference to the column
        self.columns.append({
            "statuses": statuses,
            "layout": col_layout,
            "container": container,
            "scroll": scroll
        })

        return scroll

    # ── Auto-refresh ───────────────────────────────────────────────────────────

    def _setup_auto_refresh(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(KITCHEN_REFRESH_INTERVAL)

    # ── Refresh ────────────────────────────────────────────────────────────────

    def refresh(self):
        """Reload all order cards from the database."""
        # Clear all cards from each column, but keep the stretch
        for col in self.columns:
            layout = col["layout"]

            # Remove all widgets except the stretch (which is the last item)
            # We need to iterate backwards to avoid index issues
            for i in range(layout.count() - 1, -1, -1):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    # Remove the widget from the layout
                    layout.removeWidget(widget)
                    # Schedule it for deletion
                    widget.setParent(None)
                    widget.deleteLater()
                elif item and not item.widget():
                    # If it's a spacer or other non-widget item, remove it
                    # but be careful not to remove the stretch
                    if i < layout.count() - 1:  # Don't remove the last stretch
                        layout.removeItem(item)

        conn = get_db()
        order_count = 0
        max_prep = 0

        for col in self.columns:
            placeholders = ",".join("?" * len(col["statuses"]))
            orders = conn.execute(f"""
                SELECT o.*, t.number AS table_number
                FROM orders o
                JOIN tables t ON o.table_id = t.id
                WHERE o.status IN ({placeholders})
                ORDER BY o.created_at DESC
            """, col["statuses"]).fetchall()

            order_count += len(orders)

            for order in orders:
                order_dict = dict(order)
                items = conn.execute("""
                                     SELECT oi.*, mi.name, mi.prep_time
                                     FROM order_items oi
                                              JOIN menu_items mi ON oi.menu_item_id = mi.id
                                     WHERE oi.order_id = ?
                                       AND oi.status != 'served'
                                     """, (order_dict["id"],)).fetchall()

                if not items:
                    continue

                prep_times = [it["prep_time"] for it in items]
                max_prep = max(max_prep, max(prep_times, default=0))

                item_dicts = [dict(it) for it in items]
                # Create card and insert at the beginning (before the stretch)
                card = self._make_order_card(order_dict, item_dicts)
                col["layout"].insertWidget(0, card)

        conn.close()
        self.stats_label.setText(
            f"Active Orders: {order_count}  |  Max Prep: {max_prep} min"
        )

    # ── Order card ─────────────────────────────────────────────────────────────

    def _make_order_card(self, order: dict, items: list) -> QFrame:
        """
        Build a card widget for one order.
        """
        card = OrderCard(order, items)

        # Create a layout for the buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(8, 4, 8, 8)

        status = order["status"]

        if status == "sent":
            btn = QPushButton("🍳 Start Cooking")
            btn.setStyleSheet(self._action_btn_style(BLUE))
            oid = order["id"]
            btn.clicked.connect(lambda checked=False, o=oid: self._update_status(o, "preparing"))
            btn_layout.addWidget(btn)

        elif status == "preparing":
            btn = QPushButton("✅ Mark Ready")
            btn.setStyleSheet(self._action_btn_style(YELLOW))
            oid = order["id"]
            btn.clicked.connect(lambda checked=False, o=oid: self._update_status(o, "ready"))
            btn_layout.addWidget(btn)

        elif status == "ready":
            btn = QPushButton("🍽 Served")
            btn.setStyleSheet(self._action_btn_style(GREEN))
            oid = order["id"]
            btn.clicked.connect(lambda checked=False, o=oid: self._update_status(o, "served"))
            btn_layout.addWidget(btn)

        # Cancel button for non-completed orders
        if status not in ("ready", "served", "cancelled"):
            cancel_btn = QPushButton("✕ Cancel")
            cancel_btn.setStyleSheet(self._action_btn_style(RED))
            oid = order["id"]
            cancel_btn.clicked.connect(lambda checked=False, o=oid: self._update_status(o, "cancelled"))
            btn_layout.addWidget(cancel_btn)

        # Add the button layout to the card
        card_layout = card.layout()
        card_layout.addLayout(btn_layout)

        return card

    @staticmethod
    def _action_btn_style(color: str) -> str:
        return f"""
            QPushButton {{
                background: {color}22;
                color: {color};
                border: 1px solid {color}55;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{ 
                background: {color}; 
                color: white; 
            }}
            QPushButton:pressed {{
                background: {color}DD;
            }}
        """

    def _update_status(self, order_id: int, new_status: str):
        """Update order status in database"""
        conn = get_db()

        # Update order status
        conn.execute(
            "UPDATE orders SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_status, order_id)
        )

        # If order is served or cancelled, make table available
        if new_status in ("served", "cancelled"):
            conn.execute("""
                         UPDATE tables
                         SET status='available'
                         WHERE id = (SELECT table_id FROM orders WHERE id = ?)
                         """, (order_id,))

        conn.commit()
        conn.close()

        # Refresh the display
        self.refresh()
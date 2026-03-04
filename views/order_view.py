from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QScrollArea, QTableWidget,
                               QTableWidgetItem, QHeaderView, QTextEdit,
                               QDoubleSpinBox, QTabWidget, QMessageBox,
                               QComboBox, QLineEdit, QSpinBox, QSizePolicy,
                               QAbstractItemView, QApplication)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor
from widgets.buttons import AccentButton, GhostButton, DangerButton
from widgets.cards import MenuItemRow
from widgets.dialogs import BillDialog
from widgets.styles import input_style, table_style
from database.connection import get_db
from database.models import Table, Order, MenuItem
from utils.constants import *
from utils.helpers import format_currency


class OrderView(QWidget):
    """Order management view — fully corrected."""

    order_updated = Signal()

    def __init__(self):
        super().__init__()
        self.table_id = None
        self.order_id = None
        self.cart_items = []
        self._build()

        # Set up a timer to check for updates when view becomes visible
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._refresh_menu)

    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        # Refresh menu when view becomes visible
        self.update_timer.start(100)

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left — menu browser
        root.addWidget(self._create_menu_panel(), 3)

        # Right panel wrapped in QScrollArea
        order_scroll = QScrollArea()
        order_scroll.setWidgetResizable(True)
        order_scroll.setFixedWidth(420)
        order_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        order_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {SURFACE};
                border: none;
                border-left: 1px solid {BORDER};
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
        order_scroll.setWidget(self._create_order_panel())
        root.addWidget(order_scroll)

        self._set_enabled(False)

    # ── Menu panel ─────────────────────────────────────────────────────────────

    def _create_menu_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"background: {DARK}; border: none;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 12, 20)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("📋 Menu")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {TEXT};")
        hdr.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search menu…")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(input_style())
        self.search_input.textChanged.connect(self._filter_menu)
        hdr.addWidget(self.search_input)
        layout.addLayout(hdr)

        # Refresh button for menu
        refresh_btn = GhostButton("🔄 Refresh Menu")
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self._refresh_menu)
        hdr.addWidget(refresh_btn)

        self.category_tabs = QTabWidget()
        self.category_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background: {SURFACE};
            }}
            QTabBar::tab {{
                background: {SURFACE2};
                color: {TEXT2};
                border: 1px solid {BORDER};
                padding: 7px 14px;
                border-radius: 6px 6px 0 0;
                margin-right: 2px;
                font-weight: 600;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background: {ACCENT};
                color: white;
                border-color: {ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                background: {SURFACE3};
                color: {TEXT};
            }}
        """)
        self._load_menu_categories()
        layout.addWidget(self.category_tabs, 1)
        return panel

    def _refresh_menu(self):
        """Refresh the menu display"""
        # Clear all tabs
        while self.category_tabs.count():
            self.category_tabs.removeTab(0)

        # Reload categories
        self._load_menu_categories()

        # Restore search filter
        if hasattr(self, 'search_input') and self.search_input.text():
            self._filter_menu(self.search_input.text())

    def _load_menu_categories(self):
        """Load menu categories and items from database"""
        conn = get_db()
        categories = conn.execute(
            "SELECT * FROM menu_categories WHERE is_active=1 ORDER BY sort_order"
        ).fetchall()

        for cat in categories:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

            container = QWidget()
            container.setStyleSheet("background: transparent;")
            vbox = QVBoxLayout(container)
            vbox.setSpacing(8)
            vbox.setContentsMargins(8, 8, 8, 8)

            items = conn.execute(
                "SELECT * FROM menu_items WHERE category_id=? AND is_available=1 ORDER BY name",
                (cat["id"],)
            ).fetchall()

            if items:
                for item in items:
                    row = MenuItemRow(item["id"], item["name"], item["description"], item["price"])
                    row.add_clicked.connect(self._add_to_cart)
                    vbox.addWidget(row)
            else:
                # Show empty message
                empty_label = QLabel("No items available in this category")
                empty_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px; padding: 20px;")
                empty_label.setAlignment(Qt.AlignCenter)
                vbox.addWidget(empty_label)

            vbox.addStretch()
            scroll.setWidget(container)
            self.category_tabs.addTab(scroll, cat["name"])

        conn.close()

        # Process events to ensure UI updates
        QApplication.processEvents()

    def _filter_menu(self, text: str):
        text = text.lower()
        for i in range(self.category_tabs.count()):
            tab = self.category_tabs.widget(i)  # QScrollArea
            if not isinstance(tab, QScrollArea):
                continue
            container = tab.widget()
            if not container:
                continue

            # Count visible items in this category
            visible_count = 0
            for child in container.findChildren(MenuItemRow):
                visible = not text or text in child.item_name.lower()
                child.setVisible(visible)
                if visible:
                    visible_count += 1

            # Show/hide empty message if needed
            empty_labels = container.findChildren(QLabel)
            for label in empty_labels:
                if "No items available" in label.text():
                    label.setVisible(visible_count == 0)

    # ── Order panel ────────────────────────────────────────────────────────────

    def _create_order_panel(self):
        """Returns a plain QWidget placed inside the outer QScrollArea."""
        panel = QWidget()
        panel.setStyleSheet(f"background: {SURFACE};")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(10)

        # Title
        self.order_title = QLabel("Select a table")
        self.order_title.setStyleSheet(
            f"font-size: 17px; font-weight: 700; color: {TEXT}; background: transparent;"
        )
        layout.addWidget(self.order_title)

        self.table_info = QLabel("")
        self.table_info.setStyleSheet(f"color: {TEXT2}; font-size: 12px; background: transparent;")
        layout.addWidget(self.table_info)

        layout.addWidget(self._divider())

        # Waiter
        self._field_label(layout, "Waiter")
        self.waiter_input = QLineEdit()
        self.waiter_input.setPlaceholderText("Your name…")
        self.waiter_input.setFixedHeight(36)
        self.waiter_input.setStyleSheet(input_style())
        layout.addWidget(self.waiter_input)

        # Guests + Takeaway
        gr = QHBoxLayout()
        gr.setSpacing(10)

        gl = QVBoxLayout()
        self._field_label(gl, "Guests")
        self.customer_count = QSpinBox()
        self.customer_count.setRange(1, 20)
        self.customer_count.setValue(1)
        self.customer_count.setFixedHeight(36)
        self.customer_count.setStyleSheet(input_style())
        gl.addWidget(self.customer_count)
        gr.addLayout(gl)

        tl = QVBoxLayout()
        tl.addStretch()
        self.takeaway_check = QPushButton("🥡  Takeaway")
        self.takeaway_check.setCheckable(True)
        self.takeaway_check.setFixedHeight(36)
        self.takeaway_check.setStyleSheet(f"""
            QPushButton {{
                background: {SURFACE2};
                color: {TEXT2};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 12px;
            }}
            QPushButton:checked {{
                background: {ACCENT}22;
                color: {ACCENT};
                border-color: {ACCENT};
                font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {ACCENT}; }}
        """)
        tl.addWidget(self.takeaway_check)
        gr.addLayout(tl)
        layout.addLayout(gr)

        layout.addWidget(self._divider())

        # Cart header
        ch = QLabel("Order Items")
        ch.setStyleSheet(
            f"color: {TEXT2}; font-size: 11px; font-weight: 700;"
            f" letter-spacing: 1px; background: transparent;"
        )
        layout.addWidget(ch)

        # Cart table
        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(["Item", "Qty", "Price", ""])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.cart_table.setColumnWidth(1, 96)
        self.cart_table.setColumnWidth(2, 76)
        self.cart_table.setColumnWidth(3, 36)
        self.cart_table.setStyleSheet(table_style())
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cart_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.cart_table.setMinimumHeight(160)
        self.cart_table.setMaximumHeight(260)
        self.cart_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.cart_table)

        # Notes
        self._field_label(layout, "Order Notes")
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Allergies, special requests…")
        self.notes_input.setFixedHeight(60)
        self.notes_input.setStyleSheet(input_style())
        layout.addWidget(self.notes_input)

        layout.addWidget(self._divider())

        # Totals box
        totals_box = QFrame()
        totals_box.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE2};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """)
        totals_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tb = QVBoxLayout(totals_box)
        tb.setContentsMargins(14, 12, 14, 12)
        tb.setSpacing(6)

        self.subtotal_label = self._totals_row(tb, "Subtotal")
        self.tax_label = self._totals_row(tb, f"Tax ({int(TAX_RATE * 100)}%)")
        self.service_label = self._totals_row(tb, f"Service ({int(SERVICE_CHARGE_RATE * 100)}%)")

        disc_row = QHBoxLayout()
        disc_lbl = QLabel("Discount:")
        disc_lbl.setStyleSheet(f"color: {TEXT2}; font-size: 12px; background: transparent;")
        disc_row.addWidget(disc_lbl)
        disc_row.addStretch()
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setRange(0, 9999)
        self.discount_input.setDecimals(2)
        self.discount_input.setPrefix("$")
        self.discount_input.setFixedHeight(32)
        self.discount_input.setFixedWidth(100)
        self.discount_input.setStyleSheet(input_style())
        self.discount_input.valueChanged.connect(self._update_totals)
        disc_row.addWidget(self.discount_input)
        tb.addLayout(disc_row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        tb.addWidget(sep)

        grand = QHBoxLayout()
        grand_lbl = QLabel("TOTAL")
        grand_lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 15px; font-weight: 700; background: transparent;"
        )
        grand.addWidget(grand_lbl)
        grand.addStretch()
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet(
            f"color: {ACCENT}; font-size: 20px; font-weight: 800; background: transparent;"
        )
        grand.addWidget(self.total_label)
        tb.addLayout(grand)

        layout.addWidget(totals_box)
        layout.addWidget(self._divider())

        # Buttons
        r1 = QHBoxLayout()
        self.save_btn = GhostButton("💾 Save Draft")
        self.save_btn.setFixedHeight(40)
        self.send_btn = AccentButton("📤 Send to Kitchen")
        self.send_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(lambda: self._save_order("open"))
        self.send_btn.clicked.connect(lambda: self._save_order("sent"))
        r1.addWidget(self.save_btn)
        r1.addWidget(self.send_btn)
        layout.addLayout(r1)

        r2 = QHBoxLayout()
        self.bill_btn = AccentButton("🧾 Generate Bill")
        self.bill_btn.setFixedHeight(40)
        self.clear_btn = DangerButton("🗑 Clear")
        self.clear_btn.setFixedHeight(40)
        self.bill_btn.clicked.connect(self._generate_bill)
        self.clear_btn.clicked.connect(self._clear_cart)
        r2.addWidget(self.bill_btn)
        r2.addWidget(self.clear_btn)
        layout.addLayout(r2)

        layout.addSpacing(16)
        return panel

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _divider(self):
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {BORDER};")
        return line

    def _field_label(self, parent_layout, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {TEXT2}; font-size: 11px; font-weight: 600;"
            f" letter-spacing: 0.5px; background: transparent;"
        )
        parent_layout.addWidget(lbl)

    def _totals_row(self, parent_layout, label_text: str) -> QLabel:
        row = QHBoxLayout()
        lbl = QLabel(f"{label_text}:")
        lbl.setStyleSheet(f"color: {TEXT2}; font-size: 12px; background: transparent;")
        row.addWidget(lbl)
        row.addStretch()
        val = QLabel("$0.00")
        val.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 600; background: transparent;"
        )
        row.addWidget(val)
        parent_layout.addLayout(row)
        return val

    def _set_enabled(self, enabled: bool):
        for w in [self.save_btn, self.send_btn, self.bill_btn, self.clear_btn,
                  self.waiter_input, self.notes_input, self.discount_input,
                  self.customer_count, self.takeaway_check]:
            w.setEnabled(enabled)

    # ── Load table ─────────────────────────────────────────────────────────────

    def load_table(self, table_id: int):
        self.table_id = table_id
        conn = get_db()
        table = conn.execute("SELECT * FROM tables WHERE id=?", (table_id,)).fetchone()
        if not table:
            conn.close()
            return

        order = conn.execute(
            "SELECT * FROM orders WHERE table_id=? AND status NOT IN ('paid','cancelled') "
            "ORDER BY id DESC LIMIT 1",
            (table_id,)
        ).fetchone()

        self.cart_items.clear()

        if order:
            self.order_id = order["id"]
            self.waiter_input.setText(order["waiter"] or "")
            self.notes_input.setPlainText(order["notes"] or "")
            self.customer_count.setValue(order["customer_count"] or 1)
            self.takeaway_check.setChecked(bool(order["is_takeaway"]))
            self.discount_input.setValue(float(order["discount"] or 0))

            items = conn.execute(
                """SELECT oi.*, mi.name
                   FROM order_items oi
                            JOIN menu_items mi ON oi.menu_item_id = mi.id
                   WHERE oi.order_id = ?""",
                (self.order_id,)
            ).fetchall()

            for it in items:
                self.cart_items.append({
                    "item_id": it["menu_item_id"],
                    "name": it["name"],
                    "price": float(it["unit_price"]),
                    "qty": it["quantity"],
                    "notes": it["notes"] or "",
                })
        else:
            self.order_id = None
            self.waiter_input.clear()
            self.notes_input.clear()
            self.customer_count.setValue(1)
            self.takeaway_check.setChecked(False)
            self.discount_input.setValue(0.0)

        conn.close()

        self.order_title.setText(f"Table {table['number']}  —  Order")
        self.table_info.setText(
            f"Capacity: {table['capacity']}  •  Status: {table['status'].capitalize()}"
        )
        self._refresh_cart()
        self._set_enabled(True)

    # ── Cart operations ────────────────────────────────────────────────────────

    def _add_to_cart(self, item_id: int, name: str, price: float):
        for item in self.cart_items:
            if item["item_id"] == item_id:
                item["qty"] += 1
                self._refresh_cart()
                return
        self.cart_items.append({"item_id": item_id, "name": name,
                                "price": float(price), "qty": 1, "notes": ""})
        self._refresh_cart()

    def _adjust_qty(self, row: int, delta: int):
        if not (0 <= row < len(self.cart_items)):
            return
        new_qty = self.cart_items[row]["qty"] + delta
        if new_qty > 0:
            self.cart_items[row]["qty"] = new_qty
        else:
            self.cart_items.pop(row)
        self._refresh_cart()

    def _remove_item(self, row: int):
        if 0 <= row < len(self.cart_items):
            self.cart_items.pop(row)
            self._refresh_cart()

    def _refresh_cart(self):
        self.cart_table.setRowCount(0)
        self.cart_table.setRowCount(len(self.cart_items))

        # Enable horizontal scrolling with fixed column widths
        self.cart_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Keep fixed column widths but allow scrolling
        header = self.cart_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setStretchLastSection(False)

        # Set column widths
        self.cart_table.setColumnWidth(0, 150)
        self.cart_table.setColumnWidth(1, 100)
        self.cart_table.setColumnWidth(2, 100)
        self.cart_table.setColumnWidth(3, 60)

        for row, item in enumerate(self.cart_items):
            # Col 0 — name
            n = QTableWidgetItem(item["name"])
            n.setForeground(QColor(TEXT))
            self.cart_table.setItem(row, 0, n)

            # Col 1 — qty widget
            qty_w = QWidget()
            qty_w.setStyleSheet("background: transparent;")
            qty_lay = QHBoxLayout(qty_w)
            qty_lay.setContentsMargins(4, 2, 4, 2)
            qty_lay.setSpacing(4)

            minus = QPushButton("−")
            minus.setFixedSize(22, 22)
            minus.setStyleSheet(f"""
                QPushButton {{
                    background: {SURFACE3};
                    color: {TEXT};
                    border: 1px solid {BORDER};
                    border-radius: 11px;
                    font-weight: 700;
                    font-size: 14px;
                    padding: 0;
                }}
                QPushButton:hover {{ background: {RED}33; color: {RED}; border-color: {RED}; }}
            """)
            minus.clicked.connect(lambda _, r=row: self._adjust_qty(r, -1))

            qty_lbl = QLabel(str(item["qty"]))
            qty_lbl.setAlignment(Qt.AlignCenter)
            qty_lbl.setFixedWidth(24)
            qty_lbl.setStyleSheet(f"color: {TEXT}; font-weight: 600; background: transparent;")

            plus = QPushButton("+")
            plus.setFixedSize(22, 22)
            plus.setStyleSheet(f"""
                QPushButton {{
                    background: {SURFACE3};
                    color: {TEXT};
                    border: 1px solid {BORDER};
                    border-radius: 11px;
                    font-weight: 700;
                    font-size: 14px;
                    padding: 0;
                }}
                QPushButton:hover {{ background: {GREEN}33; color: {GREEN}; border-color: {GREEN}; }}
            """)
            plus.clicked.connect(lambda _, r=row: self._adjust_qty(r, 1))

            qty_lay.addWidget(minus)
            qty_lay.addWidget(qty_lbl)
            qty_lay.addWidget(plus)
            qty_lay.addStretch()
            self.cart_table.setCellWidget(row, 1, qty_w)

            # Col 2 — price
            price_val = item["price"] * item["qty"]
            p = QTableWidgetItem(format_currency(price_val))
            p.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            p.setForeground(QColor(TEXT))
            self.cart_table.setItem(row, 2, p)

            # Col 3 — delete
            del_w = QWidget()
            del_w.setStyleSheet("background: transparent;")
            del_lay = QHBoxLayout(del_w)
            del_lay.setContentsMargins(4, 2, 4, 2)

            del_btn = QPushButton("✕")
            del_btn.setFixedSize(24, 24)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {RED}22;
                    color: {RED};
                    border: none;
                    border-radius: 12px;
                    font-weight: 700;
                    font-size: 12px;
                    padding: 0;
                }}
                QPushButton:hover {{ background: {RED}; color: white; }}
            """)
            del_btn.clicked.connect(lambda _, r=row: self._remove_item(r))
            del_lay.addWidget(del_btn)
            self.cart_table.setCellWidget(row, 3, del_w)

            # Set row height
            self.cart_table.setRowHeight(row, 50)

        self._update_totals()

    def _update_totals(self):
        subtotal = sum(i["price"] * i["qty"] for i in self.cart_items)
        tax = subtotal * TAX_RATE
        service = subtotal * SERVICE_CHARGE_RATE
        discount = self.discount_input.value()
        total = max(subtotal + tax + service - discount, 0)

        self.subtotal_label.setText(format_currency(subtotal))
        self.tax_label.setText(format_currency(tax))
        self.service_label.setText(format_currency(service))
        self.total_label.setText(format_currency(total))

    def _clear_cart(self):
        if not self.cart_items:
            return
        if QMessageBox.question(self, "Clear Order",
                                "Clear all items?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.cart_items.clear()
            self._refresh_cart()

    # ── Persist order ──────────────────────────────────────────────────────────

    def _save_order(self, status: str = "open"):
        if not self.cart_items:
            QMessageBox.information(self, "Empty Order", "Please add items before saving.")
            return
        if not self.waiter_input.text().strip():
            QMessageBox.warning(self, "Required", "Please enter the waiter's name.")
            return

        subtotal = sum(i["price"] * i["qty"] for i in self.cart_items)
        tax = subtotal * TAX_RATE
        service = subtotal * SERVICE_CHARGE_RATE
        discount = self.discount_input.value()
        total = max(subtotal + tax + service - discount, 0)
        is_to = 1 if self.takeaway_check.isChecked() else 0

        conn = get_db()
        c = conn.cursor()

        if self.order_id:
            c.execute("""
                      UPDATE orders
                      SET waiter=?,
                          notes=?,
                          status=?,
                          updated_at=CURRENT_TIMESTAMP,
                          customer_count=?,
                          is_takeaway=?,
                          subtotal=?,
                          tax=?,
                          service_charge=?,
                          discount=?,
                          total=?
                      WHERE id = ?
                      """, (self.waiter_input.text().strip(), self.notes_input.toPlainText(),
                            status, self.customer_count.value(), is_to,
                            subtotal, tax, service, discount, total, self.order_id))
            c.execute("DELETE FROM order_items WHERE order_id=?", (self.order_id,))
        else:
            c.execute("""
                      INSERT INTO orders
                      (table_id, waiter, notes, status, customer_count, is_takeaway,
                       subtotal, tax, service_charge, discount, total)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                      """, (self.table_id, self.waiter_input.text().strip(),
                            self.notes_input.toPlainText(), status,
                            self.customer_count.value(), is_to,
                            subtotal, tax, service, discount, total))
            self.order_id = c.lastrowid
            if not is_to:
                c.execute("UPDATE tables SET status='occupied' WHERE id=?", (self.table_id,))

        item_status = "sent" if status in ("sent", "preparing", "ready") else "pending"
        for item in self.cart_items:
            c.execute("""
                      INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, notes, status)
                      VALUES (?, ?, ?, ?, ?, ?)
                      """, (self.order_id, item["item_id"], item["qty"],
                            item["price"], item["notes"], item_status))

        conn.commit()
        conn.close()
        self.order_updated.emit()
        msg = "Order saved as draft." if status == "open" else "Order sent to the kitchen! 🍳"
        QMessageBox.information(self, "Saved" if status == "open" else "Sent!", msg)

    def _generate_bill(self):
        """Generate bill for current order with proper transaction handling"""
        if not self.order_id and not self.cart_items:
            QMessageBox.warning(self, "No Order", "No items to bill.")
            return

        # Save order if not saved
        if not self.order_id:
            self._save_order("billed")
            QApplication.processEvents()
            return

        conn = None
        try:
            conn = get_db()
            conn.execute("PRAGMA busy_timeout = 5000")

            order = conn.execute("SELECT * FROM orders WHERE id = ?", (self.order_id,)).fetchone()
            if not order:
                QMessageBox.critical(self, "Error", "Order not found in database.")
                return

            items = conn.execute("""
                                 SELECT oi.*, mi.name
                                 FROM order_items oi
                                          JOIN menu_items mi ON oi.menu_item_id = mi.id
                                 WHERE oi.order_id = ?
                                 """, (self.order_id,)).fetchall()

            table = conn.execute("SELECT number FROM tables WHERE id = ?", (self.table_id,)).fetchone()

            if order['status'] in ['paid', 'billed']:
                existing_bill = conn.execute(
                    "SELECT * FROM bills WHERE order_id = ? ORDER BY id DESC LIMIT 1",
                    (self.order_id,)
                ).fetchone()
                if existing_bill:
                    QMessageBox.information(
                        self, "Already Billed",
                        f"This order has already been billed.\n"
                        f"Bill Number: {existing_bill['bill_number']}\n"
                        f"Total: ${order['total']:.2f}"
                    )
                    return

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve order: {str(e)}")
            return
        finally:
            if conn:
                conn.close()

        # Get current user ID from main window
        current_user_id = None
        main_window = self.window()
        if hasattr(main_window, 'current_user') and main_window.current_user:
            current_user_id = main_window.current_user.get('id')

        # Show bill dialog
        dialog = BillDialog(
            dict(order),
            [dict(i) for i in items],
            table["number"] if table else "Takeaway",
            self,
            current_user_id
        )

        if dialog.exec():
            self.order_updated.emit()
            self.cart_items.clear()
            self._refresh_cart()
            self.order_id = None
            self.order_title.setText("Select a table")
            self.table_info.setText("")
            self._set_enabled(False)

            QMessageBox.information(
                self, "Success",
                "Payment processed successfully!\n"
                "The order has been marked as paid and the table is now being cleaned."
            )
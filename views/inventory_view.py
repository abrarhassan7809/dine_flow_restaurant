from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QComboBox, QSpinBox,
                               QDoubleSpinBox, QLineEdit, QTextEdit, QDialog,
                               QFormLayout, QGroupBox, QProgressBar)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor
from widgets.buttons import AccentButton, GhostButton, DangerButton
from widgets.dialogs import BaseDialog
from widgets.styles import input_style, table_style
from database.connection import get_db
from utils.constants import *
from utils.helpers import format_currency
from datetime import datetime


class InventoryItemDialog(BaseDialog):
    """Dialog for adding/editing inventory items"""

    def __init__(self, parent=None, item_data=None):
        super().__init__("Edit Inventory Item" if item_data else "Add Inventory Item", parent)
        self.item_data = item_data
        self._build()

    def _build(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        # Link to menu item
        self.menu_item_combo = QComboBox()
        self.menu_item_combo.setStyleSheet(input_style())
        self._load_menu_items()
        if self.item_data:
            index = self.menu_item_combo.findData(self.item_data['menu_item_id'])
            if index >= 0:
                self.menu_item_combo.setCurrentIndex(index)

        # Quantity
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0, 99999)
        self.quantity_input.setDecimals(2)
        self.quantity_input.setValue(0)
        self.quantity_input.setStyleSheet(input_style())
        if self.item_data:
            self.quantity_input.setValue(self.item_data['quantity'])

        # Unit
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["pcs", "kg", "g", "L", "ml", "oz", "lb"])
        self.unit_combo.setStyleSheet(input_style())
        if self.item_data:
            index = self.unit_combo.findText(self.item_data['unit'])
            if index >= 0:
                self.unit_combo.setCurrentIndex(index)

        # Reorder level
        self.reorder_input = QDoubleSpinBox()
        self.reorder_input.setRange(0, 99999)
        self.reorder_input.setDecimals(2)
        self.reorder_input.setValue(10)
        self.reorder_input.setStyleSheet(input_style())
        if self.item_data:
            self.reorder_input.setValue(self.item_data['reorder_level'])

        # Cost per unit
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setRange(0, 9999)
        self.cost_input.setDecimals(2)
        self.cost_input.setPrefix("$")
        self.cost_input.setStyleSheet(input_style())
        if self.item_data:
            # Get cost from menu item or inventory
            self.cost_input.setValue(0)

        layout.addRow("Menu Item:", self.menu_item_combo)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Unit:", self.unit_combo)
        layout.addRow("Reorder Level:", self.reorder_input)
        layout.addRow("Cost/Unit:", self.cost_input)

        self.content_layout.addLayout(layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = GhostButton("Cancel")
        save_btn = AccentButton("Save Item")

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        self.content_layout.addLayout(btn_layout)

    def _load_menu_items(self):
        """Load menu items into combo box"""
        conn = get_db()
        items = conn.execute(
            "SELECT id, name FROM menu_items ORDER BY name"
        ).fetchall()
        conn.close()

        self.menu_item_combo.clear()
        self.menu_item_combo.addItem("Select Item", None)
        for item in items:
            self.menu_item_combo.addItem(item['name'], item['id'])

    def _save(self):
        """Save inventory item"""
        if self.menu_item_combo.currentData() is None:
            QMessageBox.warning(self, "Required", "Please select a menu item")
            return

        conn = get_db()

        if self.item_data:
            # Update existing item
            conn.execute("""
                         UPDATE inventory
                         SET menu_item_id  = ?,
                             quantity      = ?,
                             unit          = ?,
                             reorder_level = ?,
                             last_updated  = CURRENT_TIMESTAMP
                         WHERE id = ?
                         """, (
                             self.menu_item_combo.currentData(),
                             self.quantity_input.value(),
                             self.unit_combo.currentText(),
                             self.reorder_input.value(),
                             self.item_data['id']
                         ))
        else:
            # Check if item already exists
            existing = conn.execute(
                "SELECT id FROM inventory WHERE menu_item_id = ?",
                (self.menu_item_combo.currentData(),)
            ).fetchone()

            if existing:
                QMessageBox.warning(self, "Duplicate",
                                    "This menu item already has an inventory record")
                conn.close()
                return

            # Insert new item
            conn.execute("""
                         INSERT INTO inventory (menu_item_id, quantity, unit, reorder_level)
                         VALUES (?, ?, ?, ?)
                         """, (
                             self.menu_item_combo.currentData(),
                             self.quantity_input.value(),
                             self.unit_combo.currentText(),
                             self.reorder_input.value()
                         ))

        conn.commit()
        conn.close()
        self.accept()


class StockAdjustDialog(BaseDialog):
    """Dialog for adjusting stock levels"""

    def __init__(self, parent=None, item_data=None):
        super().__init__("Adjust Stock", parent)
        self.item_data = item_data
        self._build()

    def _build(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        # Item name (read-only)
        self.name_label = QLabel(self.item_data['item_name'] if self.item_data else "")
        self.name_label.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600;")

        # Current quantity
        self.current_label = QLabel(f"{self.item_data['quantity']} {self.item_data['unit']}")
        self.current_label.setStyleSheet(f"color: {TEXT2};")

        # Adjustment type
        self.adjust_type = QComboBox()
        self.adjust_type.addItems(["Add Stock", "Remove Stock", "Set to"])
        self.adjust_type.setStyleSheet(input_style())
        self.adjust_type.currentTextChanged.connect(self._on_type_changed)

        # Adjustment amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 99999)
        self.amount_input.setDecimals(2)
        self.amount_input.setValue(0)
        self.amount_input.setStyleSheet(input_style())

        # Reason
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("e.g., delivery, waste, count")
        self.reason_input.setStyleSheet(input_style())

        layout.addRow("Item:", self.name_label)
        layout.addRow("Current:", self.current_label)
        layout.addRow("Adjustment:", self.adjust_type)
        layout.addRow("Amount:", self.amount_input)
        layout.addRow("Reason:", self.reason_input)

        self.content_layout.addLayout(layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = GhostButton("Cancel")
        save_btn = AccentButton("Apply Adjustment")

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        self.content_layout.addLayout(btn_layout)

    def _on_type_changed(self, text):
        """Handle adjustment type change"""
        if text == "Set to":
            self.amount_input.setPrefix("")
        else:
            self.amount_input.setPrefix("+ " if text == "Add Stock" else "- ")

    def _save(self):
        """Apply stock adjustment"""
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Invalid", "Amount must be greater than 0")
            return

        conn = get_db()

        current = self.item_data['quantity']

        if self.adjust_type.currentText() == "Add Stock":
            new_quantity = current + self.amount_input.value()
        elif self.adjust_type.currentText() == "Remove Stock":
            if self.amount_input.value() > current:
                QMessageBox.warning(self, "Insufficient",
                                    f"Cannot remove {self.amount_input.value()} - only {current} available")
                conn.close()
                return
            new_quantity = current - self.amount_input.value()
        else:  # Set to
            new_quantity = self.amount_input.value()

        # Update inventory
        conn.execute("""
                     UPDATE inventory
                     SET quantity     = ?,
                         last_updated = CURRENT_TIMESTAMP
                     WHERE id = ?
                     """, (new_quantity, self.item_data['id']))

        # Log adjustment (could add to audit log)
        conn.commit()
        conn.close()

        self.accept()


class InventoryView(QWidget):
    """Inventory management view"""

    def __init__(self):
        super().__init__()
        self.inventory_table = None  # Initialize attribute
        self.warning_frame = None
        self.stats_label = None
        self.category_filter = None
        self.status_filter = None
        self.search_input = None
        self.low_stock_timer = None
        self.warning_label = None
        self._build()
        self._setup_low_stock_timer()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = self._create_header()
        layout.addLayout(header)

        # Filter bar
        filter_bar = self._create_filter_bar()
        layout.addLayout(filter_bar)

        # Low stock warning
        self.warning_frame = self._create_warning_frame()
        layout.addWidget(self.warning_frame)

        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(8)
        self.inventory_table.setHorizontalHeaderLabels([
            "Item", "Category", "Quantity", "Unit", "Reorder Level",
            "Status", "Last Updated", "Actions"
        ])

        # Set column widths
        self.inventory_table.setColumnWidth(0, 150)  # Item
        self.inventory_table.setColumnWidth(1, 120)  # Category
        self.inventory_table.setColumnWidth(2, 100)  # Quantity
        self.inventory_table.setColumnWidth(3, 100)  # Unit
        self.inventory_table.setColumnWidth(4, 130)  # Reorder Level
        self.inventory_table.setColumnWidth(5, 120)  # Status
        self.inventory_table.setColumnWidth(6, 150)  # Last Updated
        self.inventory_table.setColumnWidth(7, 100)  # Actions

        # Set stretch
        header = self.inventory_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)

        self.inventory_table.setStyleSheet(table_style())
        self.inventory_table.verticalHeader().setVisible(False)
        self.inventory_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.setMinimumHeight(400)

        layout.addWidget(self.inventory_table)

        self.refresh()

    def _create_header(self):
        header = QHBoxLayout()

        title = QLabel("📦 Inventory Management")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)

        header.addStretch()

        # Summary stats
        self.stats_label = QLabel("Items: 0 | Low Stock: 0 | Value: $0")
        self.stats_label.setStyleSheet(f"color: {TEXT2}; font-size: 14px; margin-right: 10px;")
        header.addWidget(self.stats_label)

        add_btn = AccentButton("➕ Add Item")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_item)
        header.addWidget(add_btn)

        refresh_btn = GhostButton("🔄 Refresh")
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        return header

    def _create_filter_bar(self):
        layout = QHBoxLayout()
        layout.setSpacing(12)

        layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories", None)
        self.category_filter.setStyleSheet(input_style())
        self.category_filter.setMinimumWidth(150)
        self.category_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.category_filter)

        layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Low Stock", "In Stock", "Out of Stock"])
        self.status_filter.setStyleSheet(input_style())
        self.status_filter.currentTextChanged.connect(self.refresh)
        layout.addWidget(self.status_filter)

        layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search items...")
        self.search_input.setStyleSheet(input_style())
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self.refresh)
        layout.addWidget(self.search_input)

        layout.addStretch()

        # Load categories
        self._load_categories()

        return layout

    def _create_warning_frame(self):
        """Create warning frame for low stock items"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {YELLOW}22;
                border: 1px solid {YELLOW};
                border-radius: 8px;
            }}
        """)
        frame.setVisible(False)  # Hidden by default

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)

        icon = QLabel("⚠️")
        icon.setStyleSheet(f"font-size: 20px;")
        layout.addWidget(icon)

        self.warning_label = QLabel("Low stock alert: 0 items need reordering")
        self.warning_label.setStyleSheet(f"color: {YELLOW}; font-weight: 600;")
        layout.addWidget(self.warning_label, 1)

        view_btn = GhostButton("View Items")
        view_btn.clicked.connect(self._show_low_stock)
        layout.addWidget(view_btn)

        return frame

    def _setup_low_stock_timer(self):
        """Setup timer to check for low stock"""
        self.low_stock_timer = QTimer()
        self.low_stock_timer.timeout.connect(self._check_low_stock)
        self.low_stock_timer.start(60000)  # Check every minute

    def _load_categories(self):
        """Load categories into filter"""
        conn = get_db()
        categories = conn.execute(
            "SELECT id, name FROM menu_categories ORDER BY name"
        ).fetchall()
        conn.close()

        self.category_filter.clear()
        self.category_filter.addItem("All Categories", None)
        for cat in categories:
            self.category_filter.addItem(cat['name'], cat['id'])

    def refresh(self):
        """Refresh inventory list"""
        # Check if inventory_table exists
        if not hasattr(self, 'inventory_table') or self.inventory_table is None:
            return

        category_id = self.category_filter.currentData() if self.category_filter else None
        status_filter = self.status_filter.currentText() if self.status_filter else "All"
        search_text = self.search_input.text().strip() if self.search_input else ""

        conn = get_db()

        query = """
                SELECT i.*,
                       mi.name as item_name,
                       mi.category_id,
                       mc.name as category_name,
                       mi.cost
                FROM inventory i
                         JOIN menu_items mi ON i.menu_item_id = mi.id
                         LEFT JOIN menu_categories mc ON mi.category_id = mc.id
                WHERE 1 = 1 \
                """
        params = []

        if category_id:
            query += " AND mi.category_id = ?"
            params.append(category_id)

        if search_text:
            query += " AND mi.name LIKE ?"
            params.append(f"%{search_text}%")

        # Apply status filter
        if status_filter == "Low Stock":
            query += " AND i.quantity <= i.reorder_level AND i.quantity > 0"
        elif status_filter == "Out of Stock":
            query += " AND i.quantity <= 0"
        elif status_filter == "In Stock":
            query += " AND i.quantity > i.reorder_level"

        query += " ORDER BY i.quantity <= i.reorder_level DESC, mi.name"

        items = conn.execute(query, params).fetchall()
        conn.close()

        self.inventory_table.setRowCount(len(items))

        low_stock_count = 0
        total_value = 0

        for row, item in enumerate(items):
            # Item name
            self.inventory_table.setItem(row, 0, QTableWidgetItem(item['item_name']))

            # Category
            cat_item = QTableWidgetItem(item['category_name'] if item['category_name'] else 'Uncategorized')
            cat_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_table.setItem(row, 1, cat_item)

            # Quantity
            qty = item['quantity']
            qty_item = QTableWidgetItem(f"{qty:.2f}")
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Color code based on stock level
            if qty <= 0:
                qty_item.setForeground(QColor(RED))
            elif qty <= item['reorder_level']:
                qty_item.setForeground(QColor(YELLOW))
                low_stock_count += 1
            else:
                qty_item.setForeground(QColor(GREEN))

            self.inventory_table.setItem(row, 2, qty_item)

            # Unit
            unit_item = QTableWidgetItem(item['unit'])
            unit_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_table.setItem(row, 3, unit_item)

            # Reorder level
            reorder_item = QTableWidgetItem(f"{item['reorder_level']:.2f}")
            reorder_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.inventory_table.setItem(row, 4, reorder_item)

            # Status
            if qty <= 0:
                status = "Out of Stock"
                status_color = RED
            elif qty <= item['reorder_level']:
                status = "Low Stock"
                status_color = YELLOW
            else:
                status = "In Stock"
                status_color = GREEN

            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(status_color))
            self.inventory_table.setItem(row, 5, status_item)

            # Last updated
            last_updated = item['last_updated'] if 'last_updated' in item.keys() else ''
            if last_updated:
                last_updated = last_updated[:16]  # YYYY-MM-DD HH:MM
            self.inventory_table.setItem(row, 6, QTableWidgetItem(last_updated))

            # Calculate total value
            total_value += qty * item['cost']

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)

            # Adjust stock button
            adjust_btn = QPushButton("📊")
            adjust_btn.setFixedSize(30, 30)
            adjust_btn.setToolTip("Adjust Stock")
            adjust_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {BLUE}22;
                    color: {BLUE};
                    border: 1px solid {BLUE}55;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background: {BLUE};
                    color: white;
                }}
            """)
            item_dict = dict(item)
            adjust_btn.clicked.connect(lambda _, i=item_dict: self._adjust_stock(i))
            actions_layout.addWidget(adjust_btn)

            # Edit button
            edit_btn = QPushButton("✎")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setToolTip("Edit item")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {GREEN}22;
                    color: {GREEN};
                    border: 1px solid {GREEN}55;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background: {GREEN};
                    color: white;
                }}
            """)
            edit_btn.clicked.connect(lambda _, i=item_dict: self._edit_item(i))
            actions_layout.addWidget(edit_btn)

            actions_layout.addStretch()
            self.inventory_table.setCellWidget(row, 7, actions_widget)

            # Set row height
            self.inventory_table.setRowHeight(row, 50)

        # Update stats
        if self.stats_label:
            self.stats_label.setText(
                f"Items: {len(items)} | Low Stock: {low_stock_count} | Value: ${total_value:.2f}"
            )

        # Update warning frame
        self._check_low_stock()

    def _check_low_stock(self):
        """Check for low stock items and show warning"""
        conn = get_db()
        low_stock = conn.execute("""
                                 SELECT COUNT(*) as count
                                 FROM inventory i
                                 WHERE i.quantity <= i.reorder_level AND i.quantity > 0
                                 """).fetchone()
        out_of_stock = conn.execute("""
                                    SELECT COUNT(*) as count
                                    FROM inventory i
                                    WHERE i.quantity <= 0
                                    """).fetchone()
        conn.close()

        total_alerts = low_stock['count'] + out_of_stock['count']

        if self.warning_frame and self.warning_label:
            if total_alerts > 0:
                self.warning_frame.setVisible(True)
                self.warning_label.setText(
                    f"⚠️ Stock Alert: {low_stock['count']} items low, {out_of_stock['count']} out of stock"
                )
            else:
                self.warning_frame.setVisible(False)

    def _show_low_stock(self):
        """Filter to show only low stock items"""
        if self.status_filter:
            self.status_filter.setCurrentText("Low Stock")

    def _add_item(self):
        """Add new inventory item"""
        dialog = InventoryItemDialog(self)
        if dialog.exec():
            self.refresh()

    def _edit_item(self, item_data):
        """Edit inventory item"""
        dialog = InventoryItemDialog(self, item_data)
        if dialog.exec():
            self.refresh()

    def _adjust_stock(self, item_data):
        """Adjust stock level"""
        dialog = StockAdjustDialog(self, item_data)
        if dialog.exec():
            self.refresh()
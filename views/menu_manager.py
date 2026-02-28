from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QComboBox, QMessageBox, QLineEdit,
                               QSpinBox, QDoubleSpinBox, QTextEdit, QDialog,
                               QFormLayout, QCheckBox, QGroupBox, QSizePolicy,
                               QTabWidget, QScrollArea)
from PySide6.QtCore import Qt, Signal
from widgets.buttons import AccentButton, GhostButton, DangerButton
from widgets.dialogs import BaseDialog
from widgets.styles import input_style, table_style
from database.connection import get_db
from utils.constants import *


class CategoryDialog(BaseDialog):
    """Dialog for adding/editing menu categories"""

    def __init__(self, parent=None, category_data=None):
        super().__init__("Edit Category" if category_data else "Add Category", parent)
        self.category_data = category_data
        self._build()

    def _build(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Category name")
        self.name_input.setStyleSheet(input_style())
        if self.category_data:
            self.name_input.setText(self.category_data['name'])

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Category description")
        self.desc_input.setStyleSheet(input_style())
        if self.category_data:
            # Use dictionary key access, not .get()
            self.desc_input.setText(self.category_data['description'] if 'description' in self.category_data else '')

        self.sort_order = QSpinBox()
        self.sort_order.setRange(1, 100)
        self.sort_order.setValue(1)
        self.sort_order.setStyleSheet(input_style())
        if self.category_data:
            self.sort_order.setValue(self.category_data['sort_order'] if 'sort_order' in self.category_data else 1)

        self.active_check = QCheckBox("Category is active")
        self.active_check.setChecked(True)
        if self.category_data:
            self.active_check.setChecked(self.category_data['is_active'] if 'is_active' in self.category_data else 1)

        layout.addRow("Name*:", self.name_input)
        layout.addRow("Description:", self.desc_input)
        layout.addRow("Sort Order:", self.sort_order)
        layout.addRow("", self.active_check)

        self.content_layout.addLayout(layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = GhostButton("Cancel")
        save_btn = AccentButton("Save Category")

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        self.content_layout.addLayout(btn_layout)

    def _save(self):
        """Save category"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Required", "Category name is required")
            return

        conn = get_db()

        if self.category_data:
            # Update existing category
            conn.execute("""
                         UPDATE menu_categories
                         SET name        = ?,
                             description = ?,
                             sort_order  = ?,
                             is_active   = ?
                         WHERE id = ?
                         """, (
                             self.name_input.text(),
                             self.desc_input.text(),
                             self.sort_order.value(),
                             1 if self.active_check.isChecked() else 0,
                             self.category_data['id']
                         ))
        else:
            # Insert new category
            conn.execute("""
                         INSERT INTO menu_categories (name, description, sort_order, is_active)
                         VALUES (?, ?, ?, ?)
                         """, (
                             self.name_input.text(),
                             self.desc_input.text(),
                             self.sort_order.value(),
                             1 if self.active_check.isChecked() else 0
                         ))

        conn.commit()
        conn.close()
        self.accept()


class MenuItemDialog(BaseDialog):
    """Dialog for adding/editing menu items"""

    def __init__(self, parent=None, item_data=None):
        super().__init__("Edit Menu Item" if item_data else "Add Menu Item", parent)
        self.item_data = item_data
        self._build()

    def _build(self):
        # Basic info group
        basic_group = QGroupBox("Basic Information")
        basic_group.setStyleSheet(f"""
            QGroupBox {{
                color: {TEXT2};
                border: 1px solid {BORDER};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(8)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Item name")
        self.name_input.setStyleSheet(input_style())
        if self.item_data:
            self.name_input.setText(self.item_data['name'])

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Item description")
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setStyleSheet(input_style())
        if self.item_data:
            self.desc_input.setPlainText(self.item_data['description'] if 'description' in self.item_data else '')

        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(input_style())
        self._load_categories()
        if self.item_data:
            index = self.category_combo.findData(self.item_data['category_id'])
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        basic_layout.addRow("Name*:", self.name_input)
        basic_layout.addRow("Description:", self.desc_input)
        basic_layout.addRow("Category*:", self.category_combo)

        self.content_layout.addWidget(basic_group)

        # Pricing group
        price_group = QGroupBox("Pricing & Inventory")
        price_group.setStyleSheet(basic_group.styleSheet())

        price_layout = QFormLayout(price_group)
        price_layout.setSpacing(8)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 9999)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        self.price_input.setStyleSheet(input_style())
        if self.item_data:
            self.price_input.setValue(self.item_data['price'])

        self.cost_input = QDoubleSpinBox()
        self.cost_input.setRange(0, 9999)
        self.cost_input.setDecimals(2)
        self.cost_input.setPrefix("$")
        self.cost_input.setStyleSheet(input_style())
        if self.item_data:
            self.cost_input.setValue(self.item_data['cost'] if 'cost' in self.item_data else 0)

        self.prep_time = QSpinBox()
        self.prep_time.setRange(1, 120)
        self.prep_time.setSuffix(" min")
        self.prep_time.setStyleSheet(input_style())
        if self.item_data:
            self.prep_time.setValue(self.item_data['prep_time'] if 'prep_time' in self.item_data else 10)

        self.available_check = QCheckBox("Item is available")
        self.available_check.setChecked(True)
        self.available_check.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {BORDER};
                border-radius: 4px;
                background: {SURFACE2};
            }}
            QCheckBox::indicator:checked {{
                background: {GREEN};
                border-color: {GREEN};
            }}
        """)
        if self.item_data:
            self.available_check.setChecked(self.item_data['is_available'] if 'is_available' in self.item_data else 1)

        price_layout.addRow("Price*:", self.price_input)
        price_layout.addRow("Cost:", self.cost_input)
        price_layout.addRow("Prep Time:", self.prep_time)
        price_layout.addRow("", self.available_check)

        self.content_layout.addWidget(price_group)

        # Allergens & nutrition group
        info_group = QGroupBox("Additional Information")
        info_group.setStyleSheet(basic_group.styleSheet())

        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)

        self.allergens_input = QLineEdit()
        self.allergens_input.setPlaceholderText("e.g., nuts, dairy, gluten")
        self.allergens_input.setStyleSheet(input_style())
        if self.item_data:
            self.allergens_input.setText(self.item_data['allergens'] if 'allergens' in self.item_data else '')

        self.nutrition_input = QLineEdit()
        self.nutrition_input.setPlaceholderText("e.g., 500 cal, 20g protein")
        self.nutrition_input.setStyleSheet(input_style())
        if self.item_data:
            self.nutrition_input.setText(
                self.item_data['nutritional_info'] if 'nutritional_info' in self.item_data else '')

        info_layout.addRow("Allergens:", self.allergens_input)
        info_layout.addRow("Nutrition:", self.nutrition_input)

        self.content_layout.addWidget(info_group)

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

    def _load_categories(self):
        """Load categories into combo box"""
        conn = get_db()
        categories = conn.execute(
            "SELECT id, name FROM menu_categories WHERE is_active = 1 ORDER BY sort_order"
        ).fetchall()
        conn.close()

        self.category_combo.clear()
        for cat in categories:
            self.category_combo.addItem(cat['name'], cat['id'])

    def _save(self):
        """Save menu item"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Required", "Item name is required")
            return

        if self.category_combo.currentData() is None:
            QMessageBox.warning(self, "Required", "Please select a category")
            return

        conn = get_db()

        if self.item_data:
            # Update existing item
            conn.execute("""
                         UPDATE menu_items
                         SET name             = ?,
                             description      = ?,
                             category_id      = ?,
                             price            = ?,
                             cost             = ?,
                             prep_time        = ?,
                             is_available     = ?,
                             allergens        = ?,
                             nutritional_info = ?,
                             updated_at       = CURRENT_TIMESTAMP
                         WHERE id = ?
                         """, (
                             self.name_input.text(),
                             self.desc_input.toPlainText(),
                             self.category_combo.currentData(),
                             self.price_input.value(),
                             self.cost_input.value(),
                             self.prep_time.value(),
                             1 if self.available_check.isChecked() else 0,
                             self.allergens_input.text(),
                             self.nutrition_input.text(),
                             self.item_data['id']
                         ))
        else:
            # Insert new item
            conn.execute("""
                         INSERT INTO menu_items (name, description, category_id, price, cost,
                                                 prep_time, is_available, allergens, nutritional_info)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                         """, (
                             self.name_input.text(),
                             self.desc_input.toPlainText(),
                             self.category_combo.currentData(),
                             self.price_input.value(),
                             self.cost_input.value(),
                             self.prep_time.value(),
                             1 if self.available_check.isChecked() else 0,
                             self.allergens_input.text(),
                             self.nutrition_input.text()
                         ))

        conn.commit()
        conn.close()

        self.accept()


class MenuManager(QWidget):
    """Menu management view with category management"""

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        # Use tab widget for Items and Categories
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background: {SURFACE};
            }}
            QTabBar::tab {{
                background: {SURFACE2};
                color: {TEXT2};
                border: 1px solid {BORDER};
                padding: 8px 16px;
                border-radius: 6px 6px 0 0;
                margin-right: 2px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {ACCENT};
                color: white;
                border-color: {ACCENT};
            }}
        """)

        # Items tab
        items_tab = self._create_items_tab()
        self.tab_widget.addTab(items_tab, "🍴 Menu Items")

        # Categories tab
        categories_tab = self._create_categories_tab()
        self.tab_widget.addTab(categories_tab, "📁 Categories")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.tab_widget)

    def _create_items_tab(self):
        """Create the menu items management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Menu Items")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)

        filter_bar.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories", None)
        self.category_filter.setStyleSheet(input_style())
        self.category_filter.setMinimumWidth(150)
        self.category_filter.currentIndexChanged.connect(self.refresh_items)
        filter_bar.addWidget(self.category_filter)

        filter_bar.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search items...")
        self.search_input.setStyleSheet(input_style())
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self.refresh_items)
        filter_bar.addWidget(self.search_input)

        filter_bar.addStretch()

        add_btn = AccentButton("➕ Add Item")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_item)
        filter_bar.addWidget(add_btn)

        layout.addLayout(filter_bar)

        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "Name", "Category", "Price", "Cost", "Prep Time", "Status", "Actions"
        ])

        # Set column resize modes
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Category
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Price
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Cost
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Prep Time
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # Actions

        # Set fixed width for actions column
        self.items_table.setColumnWidth(6, 140)

        self.items_table.setStyleSheet(table_style())
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.verticalHeader().setDefaultSectionSize(50)  # Set row height
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setMinimumHeight(400)

        layout.addWidget(self.items_table)

        # Load initial data
        self._load_category_filter()
        self.refresh_items()

        return widget

    def _create_categories_tab(self):
        """Create the categories management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Menu Categories")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)
        header.addStretch()

        add_btn = AccentButton("➕ Add Category")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_category)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Categories table
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(5)
        self.categories_table.setHorizontalHeaderLabels([
            "Name", "Description", "Sort Order", "Status", "Actions"
        ])

        # Set column resize modes
        header = self.categories_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Name
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Description stretches
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Sort Order
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Actions

        # Set fixed width for actions column
        self.categories_table.setColumnWidth(4, 160)

        self.categories_table.setStyleSheet(table_style())
        self.categories_table.verticalHeader().setVisible(False)
        self.categories_table.verticalHeader().setDefaultSectionSize(50)  # Set row height
        self.categories_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.categories_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.categories_table.setAlternatingRowColors(True)
        self.categories_table.setMinimumHeight(400)

        layout.addWidget(self.categories_table)

        self.refresh_categories()

        return widget

    def _load_category_filter(self):
        """Load categories into filter combo box"""
        conn = get_db()
        categories = conn.execute(
            "SELECT id, name FROM menu_categories ORDER BY sort_order"
        ).fetchall()
        conn.close()

        self.category_filter.clear()
        self.category_filter.addItem("All Categories", None)
        for cat in categories:
            self.category_filter.addItem(cat['name'], cat['id'])

    def refresh_items(self):
        """Refresh menu items list"""
        category_id = self.category_filter.currentData()
        search_text = self.search_input.text().strip()

        conn = get_db()

        query = """
                SELECT mi.*, mc.name as category_name
                FROM menu_items mi
                         JOIN menu_categories mc ON mi.category_id = mc.id
                WHERE 1 = 1
                """
        params = []

        if category_id:
            query += " AND mi.category_id = ?"
            params.append(category_id)

        if search_text:
            query += " AND (mi.name LIKE ? OR mi.description LIKE ?)"
            params.append(f"%{search_text}%")
            params.append(f"%{search_text}%")

        query += " ORDER BY mc.sort_order, mi.name"

        items = conn.execute(query, params).fetchall()
        conn.close()

        self.items_table.setRowCount(len(items))

        for row, item in enumerate(items):
            # Name
            name_item = QTableWidgetItem(item['name'])
            self.items_table.setItem(row, 0, name_item)

            # Category
            cat_item = QTableWidgetItem(item['category_name'])
            cat_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 1, cat_item)

            # Price
            price_item = QTableWidgetItem(f"${item['price']:.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 2, price_item)

            # Cost
            cost_item = QTableWidgetItem(f"${item['cost']:.2f}")
            cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 3, cost_item)

            # Prep time
            prep_item = QTableWidgetItem(f"{item['prep_time']} min")
            prep_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 4, prep_item)

            # Status
            status_text = "Available" if item['is_available'] else "Unavailable"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(GREEN if item['is_available'] else RED))
            self.items_table.setItem(row, 5, status_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)
            actions_layout.setAlignment(Qt.AlignLeft)

            # Edit button
            edit_btn = QPushButton("✎ Edit")
            edit_btn.setFixedSize(50, 28)
            edit_btn.setToolTip("Edit item")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {BLUE}22;
                    color: {BLUE};
                    border: 1px solid {BLUE}55;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 0 4px;
                }}
                QPushButton:hover {{
                    background: {BLUE};
                    color: white;
                }}
            """)
            edit_btn.clicked.connect(lambda _, i=dict(item): self._edit_item(i))
            actions_layout.addWidget(edit_btn)

            # Toggle availability button
            toggle_text = "Enable" if not item['is_available'] else "Disable"
            toggle_color = GREEN if item['is_available'] else RED
            toggle_btn = QPushButton(toggle_text)
            toggle_btn.setFixedSize(50, 28)
            toggle_btn.setToolTip("Disable" if item['is_available'] else "Enable")
            toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {toggle_color}22;
                    color: {toggle_color};
                    border: 1px solid {toggle_color}55;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 0 4px;
                }}
                QPushButton:hover {{
                    background: {toggle_color};
                    color: white;
                }}
            """)
            toggle_btn.clicked.connect(lambda _, iid=item['id'], avail=item['is_available']:
                                       self._toggle_item(iid, avail))
            actions_layout.addWidget(toggle_btn)

            actions_layout.addStretch()
            self.items_table.setCellWidget(row, 6, actions_widget)

    def refresh_categories(self):
        """Refresh categories list"""
        conn = get_db()
        categories = conn.execute(
            "SELECT * FROM menu_categories ORDER BY sort_order"
        ).fetchall()
        conn.close()

        self.categories_table.setRowCount(len(categories))

        for row, cat in enumerate(categories):
            # Name
            name_item = QTableWidgetItem(cat['name'])
            self.categories_table.setItem(row, 0, name_item)

            # Description - use dictionary key access, not .get()
            desc_value = cat['description'] if 'description' in cat.keys() and cat['description'] is not None else ''
            desc_item = QTableWidgetItem(desc_value)
            self.categories_table.setItem(row, 1, desc_item)

            # Sort Order
            sort_item = QTableWidgetItem(str(cat['sort_order']))
            sort_item.setTextAlignment(Qt.AlignCenter)
            self.categories_table.setItem(row, 2, sort_item)

            # Status
            status_text = "Active" if cat['is_active'] else "Inactive"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(GREEN if cat['is_active'] else RED))
            self.categories_table.setItem(row, 3, status_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)
            actions_layout.setAlignment(Qt.AlignLeft)

            # Edit button
            edit_btn = QPushButton("✎ Edit")
            edit_btn.setFixedSize(50, 28)
            edit_btn.setToolTip("Edit category")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {BLUE}22;
                    color: {BLUE};
                    border: 1px solid {BLUE}55;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 0 4px;
                }}
                QPushButton:hover {{
                    background: {BLUE};
                    color: white;
                }}
            """)
            edit_btn.clicked.connect(lambda _, c=dict(cat): self._edit_category(c))
            actions_layout.addWidget(edit_btn)

            # Toggle status button
            toggle_text = "Activate" if not cat['is_active'] else "Deactivate"
            toggle_color = GREEN if cat['is_active'] else RED
            toggle_btn = QPushButton(toggle_text)
            toggle_btn.setFixedSize(70, 28)
            toggle_btn.setToolTip("Deactivate" if cat['is_active'] else "Activate")
            toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {toggle_color}22;
                    color: {toggle_color};
                    border: 1px solid {toggle_color}55;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 0 4px;
                }}
                QPushButton:hover {{
                    background: {toggle_color};
                    color: white;
                }}
            """)
            toggle_btn.clicked.connect(lambda _, cid=cat['id'], active=cat['is_active']:
                                       self._toggle_category(cid, active))
            actions_layout.addWidget(toggle_btn)

            actions_layout.addStretch()
            self.categories_table.setCellWidget(row, 4, actions_widget)

    def _toggle_item(self, item_id, current_status):
        """Toggle item availability"""
        conn = get_db()
        conn.execute(
            "UPDATE menu_items SET is_available = ? WHERE id = ?",
            (0 if current_status else 1, item_id)
        )
        conn.commit()
        conn.close()
        self.refresh_items()

    def _toggle_category(self, category_id, current_status):
        """Toggle category active status"""
        conn = get_db()
        conn.execute(
            "UPDATE menu_categories SET is_active = ? WHERE id = ?",
            (0 if current_status else 1, category_id)
        )
        conn.commit()
        conn.close()
        self.refresh_categories()
        self._load_category_filter()

    def _add_item(self):
        """Add new menu item"""
        dialog = MenuItemDialog(self)
        if dialog.exec():
            self.refresh_items()
            self._load_category_filter()

    def _edit_item(self, item_data):
        """Edit existing menu item"""
        dialog = MenuItemDialog(self, item_data)
        if dialog.exec():
            self.refresh_items()

    def _add_category(self):
        """Add new category"""
        dialog = CategoryDialog(self)
        if dialog.exec():
            self.refresh_categories()
            self._load_category_filter()

    def _edit_category(self, category_data):
        """Edit existing category"""
        dialog = CategoryDialog(self, category_data)
        if dialog.exec():
            self.refresh_categories()
            self._load_category_filter()
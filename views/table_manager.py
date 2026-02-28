from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QSpinBox, QComboBox,
                               QDialog, QFormLayout, QGroupBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from widgets.buttons import AccentButton, GhostButton, DangerButton
from widgets.dialogs import BaseDialog
from widgets.styles import input_style, table_style
from database.connection import get_db
from utils.constants import *
from database.models import Table


class TableDialog(BaseDialog):
    """Dialog for adding/editing tables"""

    def __init__(self, parent=None, table_data=None):
        super().__init__("Edit Table" if table_data else "Add Table", parent)
        self.table_data = table_data
        self._build()

    def _build(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        self.number_input = QSpinBox()
        self.number_input.setRange(1, 100)
        self.number_input.setStyleSheet(input_style())
        if self.table_data:
            self.number_input.setValue(self.table_data['number'])

        self.capacity_input = QSpinBox()
        self.capacity_input.setRange(1, 20)
        self.capacity_input.setValue(4)
        self.capacity_input.setStyleSheet(input_style())
        if self.table_data:
            self.capacity_input.setValue(self.table_data['capacity'])

        self.status_combo = QComboBox()
        self.status_combo.addItems(["available", "occupied", "reserved", "cleaning", "out_of_service"])
        self.status_combo.setStyleSheet(input_style())
        if self.table_data:
            index = self.status_combo.findText(self.table_data['status'])
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["rectangle", "circle", "square"])
        self.shape_combo.setStyleSheet(input_style())
        if self.table_data:
            # Handle if shape key doesn't exist
            shape = self.table_data.get('shape', 'rectangle') if hasattr(self.table_data, 'get') else 'rectangle'
            index = self.shape_combo.findText(shape)
            if index >= 0:
                self.shape_combo.setCurrentIndex(index)

        # X and Y position inputs (optional)
        self.x_position = QSpinBox()
        self.x_position.setRange(0, 1000)
        self.x_position.setValue(20)
        self.x_position.setStyleSheet(input_style())
        if self.table_data and 'x_position' in self.table_data:
            self.x_position.setValue(self.table_data['x_position'])

        self.y_position = QSpinBox()
        self.y_position.setRange(0, 1000)
        self.y_position.setValue(20)
        self.y_position.setStyleSheet(input_style())
        if self.table_data and 'y_position' in self.table_data:
            self.y_position.setValue(self.table_data['y_position'])

        layout.addRow("Table Number*:", self.number_input)
        layout.addRow("Capacity*:", self.capacity_input)
        layout.addRow("Status:", self.status_combo)
        layout.addRow("Shape:", self.shape_combo)
        layout.addRow("X Position:", self.x_position)
        layout.addRow("Y Position:", self.y_position)

        self.content_layout.addLayout(layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = GhostButton("Cancel")
        save_btn = AccentButton("Save")

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        self.content_layout.addLayout(btn_layout)

    def _save(self):
        """Save table"""
        # Check if table number already exists (for new tables)
        conn = get_db()

        if not self.table_data:  # New table
            existing = conn.execute(
                "SELECT id FROM tables WHERE number = ?",
                (self.number_input.value(),)
            ).fetchone()
            if existing:
                QMessageBox.warning(self, "Duplicate Table",
                                    f"Table {self.number_input.value()} already exists!")
                conn.close()
                return

        if self.table_data:
            # Update existing table
            conn.execute("""
                         UPDATE tables
                         SET number     = ?,
                             capacity   = ?,
                             status     = ?,
                             shape      = ?,
                             x_position = ?,
                             y_position = ?,
                             updated_at = CURRENT_TIMESTAMP
                         WHERE id = ?
                         """, (
                             self.number_input.value(),
                             self.capacity_input.value(),
                             self.status_combo.currentText(),
                             self.shape_combo.currentText(),
                             self.x_position.value(),
                             self.y_position.value(),
                             self.table_data['id']
                         ))
        else:
            # Insert new table
            conn.execute("""
                         INSERT INTO tables (number, capacity, status, shape, x_position, y_position)
                         VALUES (?, ?, ?, ?, ?, ?)
                         """, (
                             self.number_input.value(),
                             self.capacity_input.value(),
                             self.status_combo.currentText(),
                             self.shape_combo.currentText(),
                             self.x_position.value(),
                             self.y_position.value()
                         ))

        conn.commit()
        conn.close()

        self.accept()


class TableManager(QWidget):
    """Table management view"""

    tables_updated = Signal()  # Signal to notify other views that tables have changed

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

        # Tables table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Table #", "Capacity", "Status", "Current Order", "Shape", "Position", "Actions"
        ])

        # Set column widths properly
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Table #
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Capacity
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Status
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Current Order (stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Shape
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Position
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)  # Actions (fixed width)

        # Set fixed width for actions column
        self.table.setColumnWidth(6, 230)

        self.table.setStyleSheet(table_style())
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set row height to accommodate buttons
        self.table.verticalHeader().setDefaultSectionSize(50)

        layout.addWidget(self.table)

        self.refresh()

    def _create_header(self):
        header = QHBoxLayout()

        title = QLabel("🪑 Table Management")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)

        header.addStretch()

        # Table count indicator
        self.table_count_label = QLabel("Total Tables: 0")
        self.table_count_label.setStyleSheet(f"color: {TEXT2}; font-size: 14px; margin-right: 10px;")
        header.addWidget(self.table_count_label)

        add_btn = AccentButton("➕ Add Table")
        add_btn.clicked.connect(self._add_table)
        header.addWidget(add_btn)

        refresh_btn = GhostButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        return header

    def refresh(self):
        """Refresh tables list"""
        conn = get_db()

        # Get all tables
        tables = conn.execute("SELECT * FROM tables ORDER BY number").fetchall()

        # Get active orders
        orders = conn.execute("""
                              SELECT o.table_id, o.id, o.status, o.total
                              FROM orders o
                              WHERE o.status NOT IN ('paid', 'cancelled')
                              ORDER BY o.id DESC
                              """).fetchall()

        # Create order map
        order_map = {}
        for order in orders:
            if order['table_id'] not in order_map:
                order_map[order['table_id']] = order

        self.table.setRowCount(len(tables))

        # Update table count
        self.table_count_label.setText(f"Total Tables: {len(tables)}")

        for row, table in enumerate(tables):
            # Table number
            self.table.setItem(row, 0, QTableWidgetItem(str(table['number'])))

            # Capacity
            self.table.setItem(row, 1, QTableWidgetItem(str(table['capacity'])))

            # Status
            status_item = QTableWidgetItem(table['status'].capitalize())
            status_item.setForeground(QColor(STATUS_COLORS.get(table['status'], TEXT2)))
            self.table.setItem(row, 2, status_item)

            # Current order
            order = order_map.get(table['id'])
            if order:
                order_text = f"#{order['id']} - {order['status']} - ${order['total']:.2f}"
            else:
                order_text = "-"
            self.table.setItem(row, 3, QTableWidgetItem(order_text))

            # Shape
            shape = table['shape'] if 'shape' in table.keys() else 'rectangle'
            self.table.setItem(row, 4, QTableWidgetItem(shape.capitalize()))

            # Position
            x_pos = table['x_position'] if 'x_position' in table.keys() else 0
            y_pos = table['y_position'] if 'y_position' in table.keys() else 0
            position_text = f"({x_pos}, {y_pos})"
            self.table.setItem(row, 5, QTableWidgetItem(position_text))

            # Actions - create a container widget with horizontal layout
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)

            # Make the layout stretch to fill available space
            actions_layout.setAlignment(Qt.AlignLeft)

            # Status quick buttons (only 3 most important ones to save space)
            status_buttons = [
                ("A", GREEN),
                ("R", BLUE),
                ("C", YELLOW)
            ]

            for status, color in status_buttons:
                btn = QPushButton(status.capitalize())
                btn.setFixedHeight(28)
                btn.setMinimumWidth(30)  # Set minimum width for each button
                btn.setMaximumWidth(50)  # Set maximum width to prevent stretching
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {color}22;
                        color: {color};
                        border: 1px solid {color}55;
                        border-radius: 4px;
                        padding: 2px 4px;
                        font-size: 11px;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        background: {color};
                        color: white;
                    }}
                """)
                btn.clicked.connect(lambda checked, tid=table['id'], s=status:
                                    self._update_status(tid, s))
                actions_layout.addWidget(btn)

            # Add a small separator
            separator = QFrame()
            separator.setFrameShape(QFrame.VLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setFixedWidth(1)
            separator.setStyleSheet(f"background: {BORDER};")
            actions_layout.addWidget(separator)

            # Edit button
            edit_btn = GhostButton("✎ Edit")
            edit_btn.setFixedHeight(28)
            edit_btn.setMinimumWidth(50)
            edit_btn.setMaximumWidth(60)
            edit_btn.setToolTip("Edit table")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #9BA3C0;
                    border: 1px solid #363B52;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #363B52;
                    color: white;
                }
            """)
            edit_btn.clicked.connect(lambda checked, t=dict(table): self._edit_table(t))
            actions_layout.addWidget(edit_btn)

            # Delete button
            delete_btn = QPushButton("🗑 Del")
            delete_btn.setFixedHeight(28)
            delete_btn.setMinimumWidth(45)
            delete_btn.setMaximumWidth(55)
            delete_btn.setToolTip("Delete table")

            # Check if table has active orders
            has_active_order = order is not None

            if has_active_order:
                delete_btn.setEnabled(False)
                delete_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {SURFACE2};
                        color: {TEXT2};
                        border: 1px solid {BORDER};
                        border-radius: 4px;
                        padding: 2px 8px;
                        font-size: 11px;
                        opacity: 0.5;
                    }}
                """)
            else:
                delete_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {RED}22;
                        color: {RED};
                        border: 1px solid {RED}55;
                        border-radius: 4px;
                        padding: 2px 8px;
                        font-size: 11px;
                    }}
                    QPushButton:hover {{
                        background: {RED};
                        color: white;
                    }}
                """)

            delete_btn.clicked.connect(lambda checked, tid=table['id'], tnum=table['number']:
                                       self._delete_table(tid, tnum))
            actions_layout.addWidget(delete_btn)

            actions_layout.addStretch()  # Push buttons to the left
            self.table.setCellWidget(row, 6, actions_widget)

        conn.close()

    def _update_status(self, table_id, status):
        """Update table status"""
        conn = get_db()
        conn.execute("UPDATE tables SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                     (status, table_id))
        conn.commit()
        conn.close()
        self.refresh()
        self.tables_updated.emit()  # Notify other views

    def _add_table(self):
        """Add new table"""
        dialog = TableDialog(self)
        if dialog.exec():
            self.refresh()
            self.tables_updated.emit()  # Notify other views

    def _edit_table(self, table_data):
        """Edit existing table"""
        dialog = TableDialog(self, table_data)
        if dialog.exec():
            self.refresh()
            self.tables_updated.emit()  # Notify other views

    def _delete_table(self, table_id, table_number):
        """Delete a table"""
        # Double-check for active orders
        conn = get_db()
        active_order = conn.execute("""
                                    SELECT id
                                    FROM orders
                                    WHERE table_id = ?
                                      AND status NOT IN ('paid', 'cancelled')
                                    """, (table_id,)).fetchone()

        if active_order:
            QMessageBox.warning(
                self, "Cannot Delete",
                f"Table {table_number} has an active order (#{active_order['id']}).\n"
                "Please complete or cancel the order before deleting the table."
            )
            conn.close()
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete Table {table_number}?\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Delete the table
                conn.execute("DELETE FROM tables WHERE id = ?", (table_id,))
                conn.commit()

                QMessageBox.information(
                    self, "Success",
                    f"Table {table_number} has been deleted successfully."
                )

                self.refresh()
                self.tables_updated.emit()  # Notify other views

            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to delete table: {str(e)}"
                )
            finally:
                conn.close()
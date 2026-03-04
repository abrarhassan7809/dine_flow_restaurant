from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QComboBox, QLineEdit,
                               QTextEdit, QDialog, QFormLayout, QGroupBox,
                               QTabWidget, QCheckBox, QSpinBox, QDateTimeEdit,
                               QScrollArea, QSizePolicy, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal, QDateTime, QDate
from PySide6.QtGui import QColor, QPixmap
from widgets.buttons import AccentButton, GhostButton, DangerButton
from widgets.dialogs import BaseDialog
from widgets.styles import input_style, table_style
from database.connection import get_db
from utils.constants import *
from utils.helpers import format_currency, format_datetime
import hashlib


class StaffDialog(BaseDialog):
    """Dialog for adding/editing staff members"""

    def __init__(self, parent=None, staff_data=None):
        super().__init__("Edit Staff" if staff_data else "Add Staff Member", parent)
        self.staff_data = staff_data
        self._build()

    def _build(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full name")
        self.name_input.setStyleSheet(input_style())
        if self.staff_data:
            self.name_input.setText(self.staff_data['name'])

        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "waiter", "chef", "manager", "cashier", "host", "bartender", "admin"
        ])
        self.role_combo.setStyleSheet(input_style())
        if self.staff_data:
            index = self.role_combo.findText(self.staff_data['role'])
            if index >= 0:
                self.role_combo.setCurrentIndex(index)

        # PIN code (4-6 digits)
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("4-6 digit PIN")
        self.pin_input.setMaxLength(6)
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setStyleSheet(input_style())
        if self.staff_data and 'pin_code' in self.staff_data:
            self.pin_input.setText(self.staff_data['pin_code'])

        # Confirm PIN (for new staff)
        self.pin_confirm = QLineEdit()
        self.pin_confirm.setPlaceholderText("Confirm PIN")
        self.pin_confirm.setMaxLength(6)
        self.pin_confirm.setEchoMode(QLineEdit.Password)
        self.pin_confirm.setStyleSheet(input_style())
        if not self.staff_data:
            self.pin_confirm.setVisible(True)
        else:
            self.pin_confirm.setVisible(False)

        # Email (optional)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address (optional)")
        self.email_input.setStyleSheet(input_style())
        if self.staff_data and 'email' in self.staff_data:
            self.email_input.setText(self.staff_data['email'])

        # Phone (optional)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number (optional)")
        self.phone_input.setStyleSheet(input_style())
        if self.staff_data and 'phone' in self.staff_data:
            self.phone_input.setText(self.staff_data['phone'])

        # Active status
        self.active_check = QCheckBox("Active staff member")
        self.active_check.setChecked(True)
        if self.staff_data:
            self.active_check.setChecked(self.staff_data['is_active'] if 'is_active' in self.staff_data else 1)

        layout.addRow("Name*:", self.name_input)
        layout.addRow("Role*:", self.role_combo)
        layout.addRow("PIN*:", self.pin_input)
        layout.addRow("Confirm PIN:", self.pin_confirm)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Phone:", self.phone_input)
        layout.addRow("", self.active_check)

        self.content_layout.addLayout(layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = GhostButton("Cancel")
        save_btn = AccentButton("Save Staff")

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        self.content_layout.addLayout(btn_layout)

    def _save(self):
        """Save staff member"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Required", "Name is required")
            return

        pin = self.pin_input.text().strip()
        if not pin:
            QMessageBox.warning(self, "Required", "PIN is required")
            return

        if not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
            QMessageBox.warning(self, "Invalid PIN", "PIN must be 4-6 digits")
            return

        if not self.staff_data:  # New staff
            if pin != self.pin_confirm.text().strip():
                QMessageBox.warning(self, "PIN Mismatch", "PINs do not match")
                return

        conn = get_db()

        # Check if PIN already exists (for new staff)
        if not self.staff_data:
            existing = conn.execute(
                "SELECT id FROM staff WHERE pin_code = ?",
                (pin,)
            ).fetchone()
            if existing:
                QMessageBox.warning(self, "Duplicate PIN", "This PIN is already in use")
                conn.close()
                return

        # Check if email and phone columns exist
        c = conn.execute("PRAGMA table_info(staff)")
        columns = [col[1] for col in c.fetchall()]
        has_email = 'email' in columns
        has_phone = 'phone' in columns

        if self.staff_data:
            # Update existing staff - build query dynamically based on existing columns
            if has_email and has_phone:
                conn.execute("""
                             UPDATE staff
                             SET name      = ?,
                                 role      = ?,
                                 pin_code  = ?,
                                 email     = ?,
                                 phone     = ?,
                                 is_active = ?
                             WHERE id = ?
                             """, (
                                 self.name_input.text(),
                                 self.role_combo.currentText(),
                                 pin,
                                 self.email_input.text(),
                                 self.phone_input.text(),
                                 1 if self.active_check.isChecked() else 0,
                                 self.staff_data['id']
                             ))
            elif has_email:
                conn.execute("""
                             UPDATE staff
                             SET name      = ?,
                                 role      = ?,
                                 pin_code  = ?,
                                 email     = ?,
                                 is_active = ?
                             WHERE id = ?
                             """, (
                                 self.name_input.text(),
                                 self.role_combo.currentText(),
                                 pin,
                                 self.email_input.text(),
                                 1 if self.active_check.isChecked() else 0,
                                 self.staff_data['id']
                             ))
            elif has_phone:
                conn.execute("""
                             UPDATE staff
                             SET name      = ?,
                                 role      = ?,
                                 pin_code  = ?,
                                 phone     = ?,
                                 is_active = ?
                             WHERE id = ?
                             """, (
                                 self.name_input.text(),
                                 self.role_combo.currentText(),
                                 pin,
                                 self.phone_input.text(),
                                 1 if self.active_check.isChecked() else 0,
                                 self.staff_data['id']
                             ))
            else:
                conn.execute("""
                             UPDATE staff
                             SET name      = ?,
                                 role      = ?,
                                 pin_code  = ?,
                                 is_active = ?
                             WHERE id = ?
                             """, (
                                 self.name_input.text(),
                                 self.role_combo.currentText(),
                                 pin,
                                 1 if self.active_check.isChecked() else 0,
                                 self.staff_data['id']
                             ))
        else:
            # Insert new staff - build query dynamically based on existing columns
            if has_email and has_phone:
                conn.execute("""
                             INSERT INTO staff (name, role, pin_code, email, phone, is_active)
                             VALUES (?, ?, ?, ?, ?, ?)
                             """, (
                                 self.name_input.text(),
                                 self.role_combo.currentText(),
                                 pin,
                                 self.email_input.text(),
                                 self.phone_input.text(),
                                 1 if self.active_check.isChecked() else 0
                             ))
            elif has_email:
                conn.execute("""
                             INSERT INTO staff (name, role, pin_code, email, is_active)
                             VALUES (?, ?, ?, ?, ?)
                             """, (
                                 self.name_input.text(),
                                 self.role_combo.currentText(),
                                 pin,
                                 self.email_input.text(),
                                 1 if self.active_check.isChecked() else 0
                             ))
            elif has_phone:
                conn.execute("""
                             INSERT INTO staff (name, role, pin_code, phone, is_active)
                             VALUES (?, ?, ?, ?, ?)
                             """, (
                                 self.name_input.text(),
                                 self.role_combo.currentText(),
                                 pin,
                                 self.phone_input.text(),
                                 1 if self.active_check.isChecked() else 0
                             ))
            else:
                conn.execute("""
                             INSERT INTO staff (name, role, pin_code, is_active)
                             VALUES (?, ?, ?, ?)
                             """, (
                                 self.name_input.text(),
                                 self.role_combo.currentText(),
                                 pin,
                                 1 if self.active_check.isChecked() else 0
                             ))

        conn.commit()
        conn.close()
        self.accept()


class ShiftDialog(BaseDialog):
    """Dialog for starting/ending shifts"""

    def __init__(self, parent=None, staff_id=None, staff_name=None, shift_data=None):
        super().__init__("Shift Management", parent)
        self.staff_id = staff_id
        self.staff_name = staff_name
        self.shift_data = shift_data
        self._build()

    def _build(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        # Staff name
        name_label = QLabel(self.staff_name if self.staff_name else "Unknown")
        name_label.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600;")
        layout.addRow("Staff:", name_label)

        if not self.shift_data:
            # Starting shift
            self.start_time = QDateTimeEdit()
            self.start_time.setDateTime(QDateTime.currentDateTime())
            self.start_time.setCalendarPopup(True)
            self.start_time.setStyleSheet(input_style())

            self.cash_float = QDoubleSpinBox()
            self.cash_float.setRange(0, 10000)
            self.cash_float.setDecimals(2)
            self.cash_float.setPrefix("$")
            self.cash_float.setValue(100)
            self.cash_float.setStyleSheet(input_style())

            layout.addRow("Start Time:", self.start_time)
            layout.addRow("Cash Float:", self.cash_float)

            btn_text = "Start Shift"
        else:
            # Ending shift
            self.end_time = QDateTimeEdit()
            self.end_time.setDateTime(QDateTime.currentDateTime())
            self.end_time.setCalendarPopup(True)
            self.end_time.setStyleSheet(input_style())

            self.cash_sales = QDoubleSpinBox()
            self.cash_sales.setRange(0, 100000)
            self.cash_sales.setDecimals(2)
            self.cash_sales.setPrefix("$")
            self.cash_sales.setValue(0)
            self.cash_sales.setStyleSheet(input_style())

            self.card_sales = QDoubleSpinBox()
            self.card_sales.setRange(0, 100000)
            self.card_sales.setDecimals(2)
            self.card_sales.setPrefix("$")
            self.card_sales.setValue(0)
            self.card_sales.setStyleSheet(input_style())

            self.total_sales = QDoubleSpinBox()
            self.total_sales.setRange(0, 100000)
            self.total_sales.setDecimals(2)
            self.total_sales.setPrefix("$")
            self.total_sales.setValue(0)
            self.total_sales.setStyleSheet(input_style())
            self.total_sales.setReadOnly(True)

            layout.addRow("End Time:", self.end_time)
            layout.addRow("Cash Sales:", self.cash_sales)
            layout.addRow("Card Sales:", self.card_sales)
            layout.addRow("Total Sales:", self.total_sales)

            # Connect signals to update total
            self.cash_sales.valueChanged.connect(self._update_total)
            self.card_sales.valueChanged.connect(self._update_total)

            btn_text = "End Shift"

        self.content_layout.addLayout(layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = GhostButton("Cancel")
        action_btn = AccentButton(btn_text)

        cancel_btn.clicked.connect(self.reject)
        action_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(action_btn)

        self.content_layout.addLayout(btn_layout)

    def _update_total(self):
        """Update total sales"""
        total = self.cash_sales.value() + self.card_sales.value()
        self.total_sales.setValue(total)

    def _save(self):
        """Save shift data"""
        conn = get_db()

        if not self.shift_data:
            # Start shift
            conn.execute("""
                         INSERT INTO shifts (staff_id, start_time, cash_float)
                         VALUES (?, ?, ?)
                         """, (
                             self.staff_id,
                             self.start_time.dateTime().toString(Qt.ISODate),
                             self.cash_float.value()
                         ))
        else:
            # End shift
            conn.execute("""
                         UPDATE shifts
                         SET end_time    = ?,
                             cash_sales  = ?,
                             card_sales  = ?,
                             total_sales = ?
                         WHERE id = ?
                         """, (
                             self.end_time.dateTime().toString(Qt.ISODate),
                             self.cash_sales.value(),
                             self.card_sales.value(),
                             self.total_sales.value(),
                             self.shift_data['id']
                         ))

        conn.commit()
        conn.close()
        self.accept()


class StaffView(QWidget):
    """Staff management view"""

    def __init__(self):
        super().__init__()
        self.current_staff_id = 1  # Default to first staff member for demo
        self.staff_table = None
        self.shifts_table = None
        self.role_filter = None
        self.status_filter = None
        self.shift_indicator = None
        self.clock_btn = None
        self.shift_from = None
        self.shift_to = None
        self._build()

    def _build(self):
        """Build the staff management UI"""
        # Use tab widget for Staff and Shifts
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

        # Staff tab
        staff_tab = self._create_staff_tab()
        self.tab_widget.addTab(staff_tab, "👥 Staff Members")

        # Shifts tab
        shifts_tab = self._create_shifts_tab()
        self.tab_widget.addTab(shifts_tab, "⏰ Shifts")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.tab_widget)

    def _create_staff_tab(self):
        """Create the staff management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header with clock in/out
        header = QHBoxLayout()

        title = QLabel("Staff Members")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)

        header.addStretch()

        # Current shift indicator
        self.shift_indicator = QLabel("⏹️ Not Clocked In")
        self.shift_indicator.setStyleSheet(f"color: {TEXT2}; font-size: 12px; margin-right: 10px;")
        header.addWidget(self.shift_indicator)

        self.clock_btn = AccentButton("⏰ Clock In")
        self.clock_btn.setFixedHeight(36)
        self.clock_btn.clicked.connect(self._toggle_shift)
        header.addWidget(self.clock_btn)

        add_btn = AccentButton("➕ Add Staff")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_staff)
        header.addWidget(add_btn)

        # Change PIN button
        change_pin_btn = GhostButton("🔑 Change PIN")
        change_pin_btn.setFixedHeight(36)
        change_pin_btn.clicked.connect(self._change_pin)
        header.addWidget(change_pin_btn)

        refresh_btn = GhostButton("🔄 Refresh")
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)

        filter_bar.addWidget(QLabel("Role:"))
        self.role_filter = QComboBox()
        self.role_filter.addItems(["All", "waiter", "chef", "manager", "cashier", "host", "bartender", "admin"])
        self.role_filter.setStyleSheet(input_style())
        self.role_filter.setMinimumWidth(120)
        self.role_filter.currentTextChanged.connect(self.refresh)
        filter_bar.addWidget(self.role_filter)

        filter_bar.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Active", "Inactive"])
        self.status_filter.setStyleSheet(input_style())
        self.status_filter.setMinimumWidth(100)
        self.status_filter.currentTextChanged.connect(self.refresh)
        filter_bar.addWidget(self.status_filter)

        filter_bar.addStretch()

        layout.addLayout(filter_bar)

        # Staff table
        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(7)
        self.staff_table.setHorizontalHeaderLabels([
            "Name", "Role", "PIN", "Email", "Phone", "Status", "Actions"
        ])

        # Set column widths
        self.staff_table.setColumnWidth(0, 150)  # Name
        self.staff_table.setColumnWidth(1, 100)  # Role
        self.staff_table.setColumnWidth(2, 60)  # PIN
        self.staff_table.setColumnWidth(3, 150)  # Email
        self.staff_table.setColumnWidth(4, 150)  # Phone
        self.staff_table.setColumnWidth(5, 80)  # Status
        self.staff_table.setColumnWidth(6, 100)  # Actions

        # Set stretch
        header = self.staff_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Email column stretches

        self.staff_table.setStyleSheet(table_style())
        self.staff_table.verticalHeader().setVisible(False)
        self.staff_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.staff_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.staff_table.setAlternatingRowColors(True)
        self.staff_table.setMinimumHeight(400)

        layout.addWidget(self.staff_table)

        return widget

    def _change_pin(self):
        """Open change PIN dialog for current user"""
        from views.change_pin_dialog import ChangePinDialog

        # Get current user ID from main window
        main_window = self.window()
        if hasattr(main_window, 'current_user') and main_window.current_user:
            user_name = main_window.current_user.get('name', 'User')
            dialog = ChangePinDialog(main_window.current_user['id'], user_name, self)
            if dialog.exec():
                # Optional: Show success message or refresh
                QMessageBox.information(self, "Success", "Your PIN has been changed successfully!")
        else:
            QMessageBox.warning(self, "Error", "No user logged in")

    def _create_shifts_tab(self):
        """Create the shifts history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header with date filters
        header = QHBoxLayout()

        title = QLabel("Shift History")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)

        header.addStretch()

        # Date filters
        header.addWidget(QLabel("From:"))
        self.shift_from = QDateTimeEdit()
        self.shift_from.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.shift_from.setCalendarPopup(True)
        self.shift_from.setStyleSheet(input_style())
        self.shift_from.setDate(QDate.currentDate().addDays(-7))
        header.addWidget(self.shift_from)

        header.addWidget(QLabel("To:"))
        self.shift_to = QDateTimeEdit()
        self.shift_to.setDateTime(QDateTime.currentDateTime())
        self.shift_to.setCalendarPopup(True)
        self.shift_to.setStyleSheet(input_style())
        self.shift_to.setDate(QDate.currentDate())
        header.addWidget(self.shift_to)

        filter_btn = GhostButton("Apply Filter")
        filter_btn.clicked.connect(self._refresh_shifts)
        header.addWidget(filter_btn)

        refresh_btn = GhostButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_shifts)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Shifts table
        self.shifts_table = QTableWidget()
        self.shifts_table.setColumnCount(8)
        self.shifts_table.setHorizontalHeaderLabels([
            "Staff", "Role", "Start Time", "End Time", "Cash Float",
            "Cash Sales", "Card Sales", "Total"
        ])

        # Set column widths
        self.shifts_table.setColumnWidth(0, 200)  # Staff
        self.shifts_table.setColumnWidth(1, 100)  # Role
        self.shifts_table.setColumnWidth(2, 150)  # Start Time
        self.shifts_table.setColumnWidth(3, 150)  # End Time
        self.shifts_table.setColumnWidth(4, 120)  # Cash Float
        self.shifts_table.setColumnWidth(5, 100)  # Cash Sales
        self.shifts_table.setColumnWidth(6, 100)  # Card Sales
        self.shifts_table.setColumnWidth(7, 150)  # Total

        # Set stretch
        header = self.shifts_table.horizontalHeader()
        header.setStretchLastSection(False)

        self.shifts_table.setStyleSheet(table_style())
        self.shifts_table.verticalHeader().setVisible(False)
        self.shifts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.shifts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.shifts_table.setAlternatingRowColors(True)
        self.shifts_table.setMinimumHeight(400)

        layout.addWidget(self.shifts_table)

        return widget

    def refresh(self):
        """Refresh staff list"""
        if not self.staff_table:
            return

        role_filter = self.role_filter.currentText() if self.role_filter else "All"
        if role_filter == "All":
            role_filter = None
        status_filter = self.status_filter.currentText() if self.status_filter else "All"

        conn = get_db()

        # Check which columns exist
        c = conn.execute("PRAGMA table_info(staff)")
        columns = [col[1] for col in c.fetchall()]
        has_email = 'email' in columns
        has_phone = 'phone' in columns

        query = "SELECT * FROM staff WHERE 1=1"
        params = []

        if role_filter:
            query += " AND role = ?"
            params.append(role_filter)

        if status_filter == "Active":
            query += " AND is_active = 1"
        elif status_filter == "Inactive":
            query += " AND is_active = 0"

        query += " ORDER BY name"

        staff = conn.execute(query, params).fetchall()
        conn.close()

        self.staff_table.setRowCount(len(staff))

        for row, s in enumerate(staff):
            s_dict = dict(s)

            # Name
            self.staff_table.setItem(row, 0, QTableWidgetItem(s_dict['name']))

            # Role
            role_item = QTableWidgetItem(s_dict['role'].capitalize())
            role_item.setTextAlignment(Qt.AlignCenter)
            self.staff_table.setItem(row, 1, role_item)

            # PIN
            pin_text = "••••" if s_dict.get('pin_code') else ""
            pin_item = QTableWidgetItem(pin_text)
            pin_item.setTextAlignment(Qt.AlignCenter)
            self.staff_table.setItem(row, 2, pin_item)

            # Email (if column exists)
            if has_email:
                email = s_dict.get('email', '')
                self.staff_table.setItem(row, 3, QTableWidgetItem(email if email else ""))
            else:
                self.staff_table.setItem(row, 3, QTableWidgetItem("N/A"))

            # Phone (if column exists)
            if has_phone:
                phone = s_dict.get('phone', '')
                self.staff_table.setItem(row, 4, QTableWidgetItem(phone if phone else ""))
            else:
                self.staff_table.setItem(row, 4, QTableWidgetItem("N/A"))

            # Status
            status_text = "Active" if s_dict.get('is_active', 1) else "Inactive"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(GREEN if s_dict.get('is_active', 1) else RED))
            self.staff_table.setItem(row, 5, status_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)

            # Edit button
            edit_btn = QPushButton("✎")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setToolTip("Edit staff")
            edit_btn.setStyleSheet(f"""
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
            edit_btn.clicked.connect(lambda checked, st=s_dict: self._edit_staff(st))
            actions_layout.addWidget(edit_btn)

            # Toggle active button
            is_active = s_dict.get('is_active', 1)
            toggle_text = "✓" if is_active else "✗"
            toggle_color = GREEN if is_active else RED
            toggle_btn = QPushButton(toggle_text)
            toggle_btn.setFixedSize(30, 30)
            toggle_btn.setToolTip("Deactivate" if is_active else "Activate")
            toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {toggle_color}22;
                    color: {toggle_color};
                    border: 1px solid {toggle_color}55;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background: {toggle_color};
                    color: white;
                }}
            """)
            toggle_btn.clicked.connect(lambda checked, sid=s_dict['id'], active=is_active:
                                       self._toggle_active(sid, active))
            actions_layout.addWidget(toggle_btn)

            actions_layout.addStretch()
            self.staff_table.setCellWidget(row, 6, actions_widget)

            # Set row height
            self.staff_table.setRowHeight(row, 50)

        # Check current shift
        self._check_current_shift()

    def _refresh_shifts(self):
        """Refresh shifts table"""
        if not self.shifts_table or not self.shift_from or not self.shift_to:
            return

        from_date = self.shift_from.dateTime().toString(Qt.ISODate)
        to_date = self.shift_to.dateTime().toString(Qt.ISODate)

        conn = get_db()

        shifts = conn.execute("""
                              SELECT s.*, st.name as staff_name, st.role
                              FROM shifts s
                                       JOIN staff st ON s.staff_id = st.id
                              WHERE s.start_time BETWEEN ? AND ?
                              ORDER BY s.start_time DESC
                              """, (from_date, to_date)).fetchall()
        conn.close()

        self.shifts_table.setRowCount(len(shifts))

        total_cash = 0
        total_card = 0
        total_all = 0

        for row, shift in enumerate(shifts):
            shift_dict = dict(shift)

            # Staff
            self.shifts_table.setItem(row, 0, QTableWidgetItem(shift_dict['staff_name']))

            # Role
            role_item = QTableWidgetItem(shift_dict['role'].capitalize())
            role_item.setTextAlignment(Qt.AlignCenter)
            self.shifts_table.setItem(row, 1, role_item)

            # Start Time
            start_str = format_datetime(shift_dict['start_time'], "%Y-%m-%d %H:%M")
            self.shifts_table.setItem(row, 2, QTableWidgetItem(start_str))

            # End Time
            end_str = format_datetime(shift_dict['end_time'], "%Y-%m-%d %H:%M") if shift_dict.get(
                'end_time') else "Active"
            end_item = QTableWidgetItem(end_str)
            if not shift_dict.get('end_time'):
                end_item.setForeground(QColor(GREEN))
            self.shifts_table.setItem(row, 3, end_item)

            # Cash Float
            float_item = QTableWidgetItem(format_currency(shift_dict['cash_float']))
            float_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.shifts_table.setItem(row, 4, float_item)

            # Cash Sales
            cash = shift_dict.get('cash_sales', 0) or 0
            cash_item = QTableWidgetItem(format_currency(cash))
            cash_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.shifts_table.setItem(row, 5, cash_item)
            total_cash += cash

            # Card Sales
            card = shift_dict.get('card_sales', 0) or 0
            card_item = QTableWidgetItem(format_currency(card))
            card_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.shifts_table.setItem(row, 6, card_item)
            total_card += card

            # Total
            total = shift_dict.get('total_sales', 0) or 0
            total_item = QTableWidgetItem(format_currency(total))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            total_item.setForeground(QColor(ACCENT))
            self.shifts_table.setItem(row, 7, total_item)
            total_all += total

            self.shifts_table.setRowHeight(row, 50)

        # Add summary row if there are shifts
        if len(shifts) > 0:
            row = self.shifts_table.rowCount()
            self.shifts_table.insertRow(row)

            # Summary label
            summary_item = QTableWidgetItem("TOTALS:")
            summary_item.setForeground(QColor(ACCENT))
            summary_item.setFont(self.shifts_table.font())
            self.shifts_table.setItem(row, 4, summary_item)

            # Totals
            cash_total_item = QTableWidgetItem(format_currency(total_cash))
            cash_total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            cash_total_item.setForeground(QColor(ACCENT))
            cash_total_item.setFont(self.shifts_table.font())
            self.shifts_table.setItem(row, 5, cash_total_item)

            card_total_item = QTableWidgetItem(format_currency(total_card))
            card_total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            card_total_item.setForeground(QColor(ACCENT))
            card_total_item.setFont(self.shifts_table.font())
            self.shifts_table.setItem(row, 6, card_total_item)

            all_total_item = QTableWidgetItem(format_currency(total_all))
            all_total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            all_total_item.setForeground(QColor(ACCENT))
            all_total_item.setFont(self.shifts_table.font())
            self.shifts_table.setItem(row, 7, all_total_item)

            self.shifts_table.setRowHeight(row, 50)

    def _check_current_shift(self):
        """Check if current staff has an active shift"""
        if not self.shift_indicator or not self.clock_btn:
            return

        conn = get_db()
        active_shift = conn.execute("""
                                    SELECT *
                                    FROM shifts
                                    WHERE staff_id = ?
                                      AND end_time IS NULL
                                    ORDER BY start_time DESC LIMIT 1
                                    """, (self.current_staff_id,)).fetchone()

        if active_shift:
            staff = conn.execute(
                "SELECT name FROM staff WHERE id = ?",
                (self.current_staff_id,)
            ).fetchone()

            self.shift_indicator.setText(f"✅ Clocked In: {staff['name'] if staff else 'Unknown'}")
            self.shift_indicator.setStyleSheet(f"color: {GREEN}; font-size: 12px;")
            self.clock_btn.setText("⏹️ Clock Out")
            # Change button color to red for clock out
            self.clock_btn.setStyleSheet(self.clock_btn.styleSheet().replace(ACCENT, RED))
        else:
            self.shift_indicator.setText("⏹️ Not Clocked In")
            self.shift_indicator.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
            self.clock_btn.setText("⏰ Clock In")
            # Restore original color
            self.clock_btn.setStyleSheet(self.clock_btn.styleSheet().replace(RED, ACCENT))

        conn.close()

    def _toggle_shift(self):
        """Clock in or out"""
        if not self.clock_btn:
            return

        conn = get_db()

        if self.clock_btn.text() == "⏰ Clock In":
            # Clock in
            staff = conn.execute(
                "SELECT name FROM staff WHERE id = ?",
                (self.current_staff_id,)
            ).fetchone()

            if not staff:
                QMessageBox.warning(self, "Error", "Staff member not found")
                conn.close()
                return

            dialog = ShiftDialog(self, self.current_staff_id, staff['name'])
            if dialog.exec():
                self._check_current_shift()
                self._refresh_shifts()
        else:
            # Clock out
            active_shift = conn.execute("""
                                        SELECT *
                                        FROM shifts
                                        WHERE staff_id = ?
                                          AND end_time IS NULL
                                        ORDER BY start_time DESC LIMIT 1
                                        """, (self.current_staff_id,)).fetchone()

            if active_shift:
                staff = conn.execute(
                    "SELECT name FROM staff WHERE id = ?",
                    (self.current_staff_id,)
                ).fetchone()

                dialog = ShiftDialog(self, self.current_staff_id, staff['name'], active_shift)
                if dialog.exec():
                    self._check_current_shift()
                    self._refresh_shifts()

        conn.close()

    def _toggle_active(self, staff_id, current_status):
        """Toggle staff active status"""
        conn = get_db()
        conn.execute(
            "UPDATE staff SET is_active = ? WHERE id = ?",
            (0 if current_status else 1, staff_id)
        )
        conn.commit()
        conn.close()
        self.refresh()

    def _add_staff(self):
        """Add new staff member"""
        dialog = StaffDialog(self)
        if dialog.exec():
            self.refresh()

    def _edit_staff(self, staff_data):
        """Edit existing staff member"""
        dialog = StaffDialog(self, staff_data)
        if dialog.exec():
            self.refresh()
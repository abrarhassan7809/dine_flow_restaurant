from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QComboBox, QDateEdit,
                               QTimeEdit, QSpinBox, QLineEdit, QTextEdit,
                               QDialog, QFormLayout, QGroupBox, QTabWidget,
                               QCalendarWidget, QSplitter)
from PySide6.QtCore import Qt, Signal, QDate, QTime, QDateTime
from PySide6.QtGui import QColor
from widgets.buttons import AccentButton, GhostButton, DangerButton
from widgets.dialogs import BaseDialog
from widgets.styles import input_style, table_style
from database.connection import get_db
from utils.constants import *
from utils.helpers import format_datetime
from database.models import Reservation, Table
from datetime import datetime, timedelta


class ReservationDialog(BaseDialog):
    """Dialog for adding/editing reservations"""

    def __init__(self, parent=None, reservation_data=None):
        super().__init__("Edit Reservation" if reservation_data else "New Reservation", parent)
        self.reservation_data = reservation_data
        self._build()

    def _build(self):
        # Customer info group
        customer_group = QGroupBox("Customer Information")
        customer_group.setStyleSheet(f"""
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

        customer_layout = QFormLayout(customer_group)
        customer_layout.setSpacing(8)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer name")
        self.name_input.setStyleSheet(input_style())
        if self.reservation_data:
            self.name_input.setText(self.reservation_data['customer_name'])

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        self.phone_input.setStyleSheet(input_style())
        if self.reservation_data and 'customer_phone' in self.reservation_data:
            self.phone_input.setText(self.reservation_data['customer_phone'])

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        self.email_input.setStyleSheet(input_style())
        if self.reservation_data and 'customer_email' in self.reservation_data:
            self.email_input.setText(self.reservation_data['customer_email'])

        customer_layout.addRow("Name*:", self.name_input)
        customer_layout.addRow("Phone:", self.phone_input)
        customer_layout.addRow("Email:", self.email_input)

        self.content_layout.addWidget(customer_group)

        # Reservation details group
        details_group = QGroupBox("Reservation Details")
        details_group.setStyleSheet(customer_group.styleSheet())

        details_layout = QFormLayout(details_group)
        details_layout.setSpacing(8)

        # Date and time
        date_time_layout = QHBoxLayout()

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet(input_style())
        date_time_layout.addWidget(self.date_input)

        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime.currentTime().addSecs(3600))  # +1 hour
        self.time_input.setStyleSheet(input_style())
        date_time_layout.addWidget(self.time_input)

        # Party size
        self.party_size = QSpinBox()
        self.party_size.setRange(1, 20)
        self.party_size.setValue(2)
        self.party_size.setStyleSheet(input_style())

        # Duration
        self.duration = QSpinBox()
        self.duration.setRange(30, 240)
        self.duration.setValue(120)
        self.duration.setSuffix(" min")
        self.duration.setStyleSheet(input_style())

        # Table selection
        self.table_combo = QComboBox()
        self.table_combo.setStyleSheet(input_style())
        self.table_combo.setMinimumWidth(150)
        self._load_available_tables()

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["confirmed", "pending", "cancelled", "completed", "no-show"])
        self.status_combo.setStyleSheet(input_style())
        if self.reservation_data:
            index = self.status_combo.findText(self.reservation_data['status'])
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

        # Special requests
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Special requests, allergies, occasion, etc.")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setStyleSheet(input_style())
        if self.reservation_data and 'special_requests' in self.reservation_data:
            self.notes_input.setPlainText(self.reservation_data['special_requests'])

        details_layout.addRow("Date/Time:", date_time_layout)
        details_layout.addRow("Party Size*:", self.party_size)
        details_layout.addRow("Duration:", self.duration)
        details_layout.addRow("Table:", self.table_combo)
        details_layout.addRow("Status:", self.status_combo)
        details_layout.addRow("Notes:", self.notes_input)

        self.content_layout.addWidget(details_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = GhostButton("Cancel")
        save_btn = AccentButton("Save Reservation")

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        self.content_layout.addLayout(btn_layout)

        # Load existing data if editing
        if self.reservation_data:
            self._load_reservation_data()

    def _load_available_tables(self):
        """Load available tables for the selected date/time"""
        self.table_combo.clear()
        self.table_combo.addItem("Auto-assign", None)

        conn = get_db()
        tables = conn.execute(
            "SELECT id, number, capacity FROM tables ORDER BY number"
        ).fetchall()
        conn.close()

        for table in tables:
            self.table_combo.addItem(
                f"Table {table['number']} (Capacity: {table['capacity']})",
                table['id']
            )

    def _load_reservation_data(self):
        """Load existing reservation data"""
        self.name_input.setText(self.reservation_data['customer_name'])

        if 'customer_phone' in self.reservation_data:
            self.phone_input.setText(self.reservation_data['customer_phone'])

        if 'customer_email' in self.reservation_data:
            self.email_input.setText(self.reservation_data['customer_email'])

        res_time = QDateTime.fromString(self.reservation_data['reservation_time'], Qt.ISODate)
        self.date_input.setDate(res_time.date())
        self.time_input.setTime(res_time.time())

        self.party_size.setValue(self.reservation_data['party_size'])

        if 'duration' in self.reservation_data:
            self.duration.setValue(self.reservation_data['duration'])

        if self.reservation_data.get('table_id'):
            index = self.table_combo.findData(self.reservation_data['table_id'])
            if index >= 0:
                self.table_combo.setCurrentIndex(index)

        if 'special_requests' in self.reservation_data:
            self.notes_input.setPlainText(self.reservation_data['special_requests'])

    def _save(self):
        """Save reservation"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Required", "Customer name is required")
            return

        # Create datetime from date and time
        res_datetime = QDateTime(
            self.date_input.date(),
            self.time_input.time()
        ).toString(Qt.ISODate)

        conn = get_db()

        if self.reservation_data:
            # Update existing reservation
            conn.execute("""
                         UPDATE reservations
                         SET customer_name    = ?,
                             customer_phone   = ?,
                             customer_email   = ?,
                             party_size       = ?,
                             reservation_time = ?,
                             duration         = ?,
                             table_id         = ?,
                             status           = ?,
                             special_requests = ?
                         WHERE id = ?
                         """, (
                             self.name_input.text(),
                             self.phone_input.text(),
                             self.email_input.text(),
                             self.party_size.value(),
                             res_datetime,
                             self.duration.value(),
                             self.table_combo.currentData(),
                             self.status_combo.currentText(),
                             self.notes_input.toPlainText(),
                             self.reservation_data['id']
                         ))
        else:
            # Insert new reservation
            conn.execute("""
                         INSERT INTO reservations (customer_name, customer_phone, customer_email,
                                                   party_size, reservation_time, duration,
                                                   table_id, status, special_requests)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                         """, (
                             self.name_input.text(),
                             self.phone_input.text(),
                             self.email_input.text(),
                             self.party_size.value(),
                             res_datetime,
                             self.duration.value(),
                             self.table_combo.currentData(),
                             self.status_combo.currentText(),
                             self.notes_input.toPlainText()
                         ))

        conn.commit()
        conn.close()
        self.accept()


class ReservationsView(QWidget):
    """Reservations management view"""

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

        # Filter bar
        filter_bar = self._create_filter_bar()
        layout.addLayout(filter_bar)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {BORDER};
                width: 2px;
            }}
        """)

        # Calendar view (left panel)
        calendar_panel = self._create_calendar_panel()
        splitter.addWidget(calendar_panel)

        # Reservations table (right panel)
        table_panel = self._create_table_panel()
        splitter.addWidget(table_panel)

        # Set initial sizes (40% calendar, 60% table)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter, 1)

        self.refresh()

    def _create_header(self):
        header = QHBoxLayout()

        title = QLabel("📅 Reservations")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        header.addWidget(title)

        header.addStretch()

        # Reservation count
        self.count_label = QLabel("Total: 0")
        self.count_label.setStyleSheet(f"color: {TEXT2}; font-size: 14px; margin-right: 10px;")
        header.addWidget(self.count_label)

        add_btn = AccentButton("➕ New Reservation")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_reservation)
        header.addWidget(add_btn)

        refresh_btn = GhostButton("🔄 Refresh")
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        return header

    def _create_filter_bar(self):
        layout = QHBoxLayout()
        layout.setSpacing(12)

        layout.addWidget(QLabel("Date:"))
        self.filter_date = QDateEdit()
        self.filter_date.setDate(QDate.currentDate())
        self.filter_date.setCalendarPopup(True)
        self.filter_date.setStyleSheet(input_style())
        self.filter_date.dateChanged.connect(self.refresh)
        layout.addWidget(self.filter_date)

        layout.addWidget(QLabel("Status:"))
        self.filter_status = QComboBox()
        self.filter_status.addItems(["All", "Confirmed", "Pending", "Completed", "Cancelled", "No-show"])
        self.filter_status.setStyleSheet(input_style())
        self.filter_status.currentTextChanged.connect(self.refresh)
        layout.addWidget(self.filter_status)

        layout.addStretch()

        return layout

    def _create_calendar_panel(self):
        """Create calendar panel for visual reservation view"""
        panel = QWidget()
        panel.setStyleSheet(f"background: {SURFACE}; border-radius: 8px;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)

        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet(f"""
            QCalendarWidget {{
                background: {SURFACE2};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: {TEXT};
                background: {SURFACE2};
                selection-background-color: {ACCENT};
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background: {SURFACE3};
            }}
        """)
        self.calendar.clicked.connect(self._on_date_selected)
        layout.addWidget(self.calendar)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(8)

        for status, color in [
            ("Confirmed", GREEN),
            ("Pending", YELLOW),
            ("Completed", BLUE),
            ("Cancelled", RED),
            ("No-show", TEXT2)
        ]:
            legend_item = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            legend_item.addWidget(dot)
            legend_item.addWidget(QLabel(status))
            legend_item.addStretch()
            legend_layout.addLayout(legend_item)

        layout.addLayout(legend_layout)

        return panel

    def _create_table_panel(self):
        """Create table panel for reservations list"""
        panel = QWidget()
        panel.setStyleSheet(f"background: {SURFACE}; border-radius: 8px;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)

        # Reservations table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Time", "Customer", "Phone", "Party", "Table", "Duration", "Status", "Notes", "Actions"
        ])

        # Set column widths
        self.table.setColumnWidth(0, 100)  # Time
        self.table.setColumnWidth(1, 150)  # Customer
        self.table.setColumnWidth(2, 120)  # Phone
        self.table.setColumnWidth(3, 60)  # Party
        self.table.setColumnWidth(4, 80)  # Table
        self.table.setColumnWidth(5, 80)  # Duration
        self.table.setColumnWidth(6, 100)  # Status
        self.table.setColumnWidth(7, 150)  # Notes
        self.table.setColumnWidth(8, 120)  # Actions

        # Set stretch
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # Notes column stretches

        self.table.setStyleSheet(table_style())
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(400)

        layout.addWidget(self.table)

        return panel

    def refresh(self):
        """Refresh reservations list"""
        selected_date = self.filter_date.date().toString("yyyy-MM-dd")
        status_filter = self.filter_status.currentText().lower()
        if status_filter == "all":
            status_filter = None

        conn = get_db()

        query = """
                SELECT r.*, t.number as table_number
                FROM reservations r
                         LEFT JOIN tables t ON r.table_id = t.id
                WHERE DATE (r.reservation_time) = DATE (?) \
                """
        params = [selected_date]

        if status_filter and status_filter != "all":
            query += " AND r.status = ?"
            params.append(status_filter)

        query += " ORDER BY r.reservation_time"

        reservations = conn.execute(query, params).fetchall()
        conn.close()

        self.table.setRowCount(len(reservations))
        self.count_label.setText(f"Total: {len(reservations)}")

        # Highlight dates with reservations on calendar
        self._highlight_dates()

        for row, res in enumerate(reservations):
            # Convert sqlite3.Row to dictionary for easier access
            res_dict = dict(res)

            res_time = QDateTime.fromString(res_dict['reservation_time'], Qt.ISODate)
            time_str = res_time.toString("hh:mm AP")

            # Time
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, time_item)

            # Customer
            self.table.setItem(row, 1, QTableWidgetItem(res_dict['customer_name']))

            # Phone - use dictionary access with key check
            phone = res_dict['customer_phone'] if 'customer_phone' in res_dict and res_dict['customer_phone'] else '-'
            self.table.setItem(row, 2, QTableWidgetItem(phone))

            # Party
            party_item = QTableWidgetItem(str(res_dict['party_size']))
            party_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, party_item)

            # Table
            table_text = f"Table {res_dict['table_number']}" if res_dict.get('table_number') else "Auto"
            table_item = QTableWidgetItem(table_text)
            table_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, table_item)

            # Duration
            duration_item = QTableWidgetItem(f"{res_dict['duration']} min")
            duration_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, duration_item)

            # Status
            status_color = {
                'confirmed': GREEN,
                'pending': YELLOW,
                'completed': BLUE,
                'cancelled': RED,
                'no-show': TEXT2
            }.get(res_dict['status'], TEXT2)

            status_item = QTableWidgetItem(res_dict['status'].capitalize())
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(status_color))
            self.table.setItem(row, 6, status_item)

            # Notes
            notes = res_dict['special_requests'] if 'special_requests' in res_dict and res_dict[
                'special_requests'] else '-'
            self.table.setItem(row, 7, QTableWidgetItem(notes))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)

            # Edit button
            edit_btn = QPushButton("✎")
            edit_btn.setFixedSize(24, 24)
            edit_btn.setToolTip("Edit reservation")
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
            edit_btn.clicked.connect(lambda _, r=res_dict: self._edit_reservation(r))
            actions_layout.addWidget(edit_btn)

            # Status quick buttons
            for status, color, icon in [
                ("✓", GREEN, "confirmed"),
                ("⌛", YELLOW, "pending"),
                ("✗", RED, "cancelled")
            ]:
                if res_dict['status'] != status.lower():
                    btn = QPushButton(icon)
                    btn.setFixedSize(24, 24)
                    btn.setToolTip(f"Mark as {status}")
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {color}22;
                            color: {color};
                            border: 1px solid {color}55;
                            border-radius: 4px;
                            font-size: 12px;
                            font-weight: 700;
                            padding: 0;
                        }}
                        QPushButton:hover {{
                            background: {color};
                            color: white;
                        }}
                    """)
                    btn.clicked.connect(lambda _, rid=res_dict['id'], s=status.lower():
                                        self._update_status(rid, s))
                    actions_layout.addWidget(btn)

            actions_layout.addStretch()
            self.table.setCellWidget(row, 8, actions_widget)

            # Set row height
            self.table.setRowHeight(row, 32)

    def _highlight_dates(self):
        """Highlight dates that have reservations on the calendar"""
        # This would require custom calendar painting
        # For now, we'll just show a message
        pass

    def _on_date_selected(self, date):
        """Handle date selection from calendar"""
        self.filter_date.setDate(date)
        self.refresh()

    def _update_status(self, reservation_id, new_status):
        """Update reservation status"""
        conn = get_db()
        conn.execute(
            "UPDATE reservations SET status = ? WHERE id = ?",
            (new_status, reservation_id)
        )
        conn.commit()
        conn.close()
        self.refresh()

    def _add_reservation(self):
        """Add new reservation"""
        dialog = ReservationDialog(self)
        if dialog.exec():
            self.refresh()

    def _edit_reservation(self, reservation_data):
        """Edit existing reservation"""
        dialog = ReservationDialog(self, reservation_data)
        if dialog.exec():
            self.refresh()
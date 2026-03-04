from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFormLayout, QLineEdit, QComboBox,
                               QSpinBox, QDoubleSpinBox, QTextEdit, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMessageBox,
                               QDateEdit, QTimeEdit, QGroupBox, QCheckBox, QFrame, QApplication)
from PySide6.QtCore import Qt, QDate, QTime, QDateTime
from PySide6.QtGui import QFont, QColor
from widgets.buttons import AccentButton, GhostButton, DangerButton
from widgets.cards import Badge
from widgets.styles import input_style, table_style
from utils.constants import *
from utils.helpers import format_currency, format_datetime
from database.models import Bill, Order


class BaseDialog(QDialog):
    """Base dialog with common styling"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setStyleSheet(f"""
            QDialog {{
                background: {SURFACE};
                color: {TEXT};
            }}
        """)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build_base()

    def _build_base(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel(self.windowTitle())
        title_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEXT};")
        title_bar.addWidget(title_label)

        title_bar.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT2};
                border: none;
                border-radius: 15px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {RED}22;
                color: {RED};
            }}
        """)
        close_btn.clicked.connect(self.reject)
        title_bar.addWidget(close_btn)

        layout.addLayout(title_bar)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        layout.addWidget(sep)

        # Content area
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(16)
        layout.addLayout(self.content_layout)


class BillDialog(BaseDialog):
    """Dialog for generating and viewing bills"""

    def __init__(self, order, items, table_number, parent=None, user_id=None):
        super().__init__("Bill / Receipt", parent)
        self.order = order
        self.items = items
        self.table_number = table_number
        self.user_id = user_id
        self._build()

    def _build(self):
        # Header
        header = QVBoxLayout()

        title = QLabel("🧾 BILL")
        title.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {ACCENT};")
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(title)

        restaurant = QLabel("The Grand Restaurant")
        restaurant.setStyleSheet(f"font-size: 14px; color: {TEXT2};")
        restaurant.setAlignment(Qt.AlignCenter)
        header.addWidget(restaurant)

        self.content_layout.addLayout(header)

        # Info
        info_layout = QHBoxLayout()

        table_info = QLabel(f"Table: {self.table_number}")
        table_info.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        info_layout.addWidget(table_info)

        info_layout.addStretch()

        order_info = QLabel(f"Order: #{self.order['id']}")
        order_info.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        info_layout.addWidget(order_info)

        info_layout.addStretch()

        dt = QLabel(format_datetime(self.order['created_at'], "%d/%m/%Y %H:%M"))
        dt.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        info_layout.addWidget(dt)

        self.content_layout.addLayout(info_layout)

        if self.order['waiter']:
            waiter = QLabel(f"Waiter: {self.order['waiter']}")
            waiter.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
            self.content_layout.addWidget(waiter)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        self.content_layout.addWidget(sep)

        # Items table
        tbl = QTableWidget(len(self.items), 4)
        tbl.setHorizontalHeaderLabels(["Item", "Qty", "Unit", "Total"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tbl.setStyleSheet(table_style())
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setMaximumHeight(250)

        for r, item in enumerate(self.items):
            tbl.setItem(r, 0, QTableWidgetItem(item['name']))
            tbl.setItem(r, 1, QTableWidgetItem(str(item['quantity'])))
            tbl.setItem(r, 2, QTableWidgetItem(format_currency(item['unit_price'])))
            tbl.setItem(r, 3, QTableWidgetItem(format_currency(item['unit_price'] * item['quantity'])))

        self.content_layout.addWidget(tbl)

        # Totals
        totals_group = QGroupBox("Summary")
        totals_group.setStyleSheet(f"""
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

        totals_layout = QFormLayout(totals_group)
        totals_layout.setLabelAlignment(Qt.AlignRight)
        totals_layout.setSpacing(8)

        subtotal = QLabel(format_currency(self.order['subtotal']))
        tax = QLabel(format_currency(self.order['tax']))
        discount = QLabel(f"-{format_currency(self.order['discount'])}")
        service = QLabel(format_currency(self.order['service_charge']))
        total = QLabel(format_currency(self.order['total']))

        total.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {ACCENT};")

        totals_layout.addRow("Subtotal:", subtotal)
        totals_layout.addRow("Tax (10%):", tax)
        totals_layout.addRow("Service Charge (5%):", service)
        if self.order['discount'] > 0:
            totals_layout.addRow("Discount:", discount)
        totals_layout.addRow("TOTAL:", total)

        self.content_layout.addWidget(totals_group)

        # Payment section
        payment_group = QGroupBox("Payment")
        payment_group.setStyleSheet(totals_group.styleSheet())

        payment_layout = QFormLayout(payment_group)
        payment_layout.setSpacing(10)

        # Define payment methods if not imported from constants
        PAYMENT_METHODS = [
            "Cash",
            "Credit Card",
            "Debit Card",
            "Mobile Pay",
            "Gift Card",
            "Voucher"
        ]

        self.pay_method = QComboBox()
        self.pay_method.addItems(PAYMENT_METHODS)
        self.pay_method.setStyleSheet(input_style())

        self.amount_paid = QDoubleSpinBox()
        self.amount_paid.setRange(0, 99999)
        self.amount_paid.setDecimals(2)
        self.amount_paid.setPrefix("$")
        self.amount_paid.setValue(self.order['total'])
        self.amount_paid.setStyleSheet(input_style())
        self.amount_paid.valueChanged.connect(self._update_change)

        self.tip_amount = QDoubleSpinBox()
        self.tip_amount.setRange(0, 99999)
        self.tip_amount.setDecimals(2)
        self.tip_amount.setPrefix("$")
        self.tip_amount.setStyleSheet(input_style())
        self.tip_amount.valueChanged.connect(self._update_change)

        self.change_label = QLabel("$0.00")
        self.change_label.setStyleSheet(f"color: {GREEN}; font-weight: 700; font-size: 14px;")

        payment_layout.addRow("Method:", self.pay_method)
        payment_layout.addRow("Amount Paid:", self.amount_paid)
        payment_layout.addRow("Tip:", self.tip_amount)
        payment_layout.addRow("Change:", self.change_label)

        self.content_layout.addWidget(payment_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = GhostButton("Cancel")
        print_btn = GhostButton("🖨️ Print")
        pay_btn = AccentButton("✓ Confirm Payment")

        cancel_btn.clicked.connect(self.reject)
        print_btn.clicked.connect(self._print_bill)
        pay_btn.clicked.connect(self._confirm_payment)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(pay_btn)

        self.content_layout.addLayout(btn_layout)

    def _update_change(self):
        total_with_tip = self.order['total'] + self.tip_amount.value()
        change = max(self.amount_paid.value() - total_with_tip, 0)
        print(total_with_tip, change)
        self.change_label.setText(format_currency(change))

    def _confirm_payment(self):
        """Process payment confirmation"""
        total_with_tip = self.order['total'] + self.tip_amount.value()
        amount_paid = self.amount_paid.value()

        total_with_tip = round(total_with_tip, 2)
        amount_paid = round(amount_paid, 2)

        if amount_paid < total_with_tip - 0.01:
            shortfall = total_with_tip - amount_paid
            QMessageBox.warning(
                self,
                "Insufficient Payment",
                f"Amount paid (${amount_paid:.2f}) is less than total including tip (${total_with_tip:.2f}).\n"
                f"Shortfall: ${shortfall:.2f}\n\n"
                f"Please enter the full amount or adjust the tip."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Payment",
            f"Total: {format_currency(self.order['total'])}\n"
            f"Tip: {format_currency(self.tip_amount.value())}\n"
            f"Amount Paid: {format_currency(amount_paid)}\n"
            f"Change: {format_currency(max(amount_paid - total_with_tip, 0))}\n\n"
            f"Confirm payment?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        pay_btn = self.sender()
        if pay_btn:
            pay_btn.setEnabled(False)
            QApplication.processEvents()

        try:
            # Pass user_id to Bill.generate - note the order of parameters
            # The method signature is: generate(order_id, payment_method="cash", amount_paid=0, tip=0, created_by=None)
            if self.user_id:
                bill = Bill.generate(
                    self.order['id'],  # order_id
                    self.pay_method.currentText(),  # payment_method
                    amount_paid,  # amount_paid
                    self.tip_amount.value(),  # tip
                    self.user_id  # created_by
                )
            else:
                bill = Bill.generate(
                    self.order['id'],  # order_id
                    self.pay_method.currentText(),  # payment_method
                    amount_paid,  # amount_paid
                    self.tip_amount.value()  # tip
                )

            QMessageBox.information(
                self,
                "Payment Confirmed",
                f"✅ Payment successful!\n\n"
                f"Bill Number: {bill.bill_number}\n"
                f"Total: {format_currency(self.order['total'])}\n"
                f"Tip: {format_currency(self.tip_amount.value())}\n"
                f"Amount Paid: {format_currency(amount_paid)}\n"
                f"Change: {format_currency(bill.change_given)}\n\n"
                f"Thank you for your payment!"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to process payment: {str(e)}\n\n"
                f"Please try again or contact support."
            )
        finally:
            if pay_btn:
                pay_btn.setEnabled(True)

    def _print_bill(self):
        # TODO: Implement actual printing
        QMessageBox.information(self, "Print", "Bill sent to printer")


class ReservationDialog(BaseDialog):
    """Dialog for creating/editing reservations"""

    def __init__(self, parent=None, reservation=None):
        super().__init__("Reservation" if not reservation else "Edit Reservation", parent)
        self.reservation = reservation
        self._build()

    def _build(self):
        # Customer info
        customer_group = QGroupBox("Customer Information")
        customer_group.setStyleSheet("""
            QGroupBox {
                color: #9BA3C0;
                border: 1px solid #363B52;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        customer_layout = QFormLayout(customer_group)
        customer_layout.setSpacing(8)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer name")
        self.name_input.setStyleSheet(input_style())

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        self.phone_input.setStyleSheet(input_style())

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        self.email_input.setStyleSheet(input_style())

        customer_layout.addRow("Name*:", self.name_input)
        customer_layout.addRow("Phone:", self.phone_input)
        customer_layout.addRow("Email:", self.email_input)

        self.content_layout.addWidget(customer_group)

        # Reservation details
        details_group = QGroupBox("Reservation Details")
        details_group.setStyleSheet(customer_group.styleSheet())

        details_layout = QFormLayout(details_group)
        details_layout.setSpacing(8)

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet(input_style())

        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime.currentTime().addSecs(3600))  # +1 hour
        self.time_input.setStyleSheet(input_style())

        self.party_size = QSpinBox()
        self.party_size.setRange(1, 20)
        self.party_size.setValue(2)
        self.party_size.setStyleSheet(input_style())

        self.duration = QSpinBox()
        self.duration.setRange(30, 240)
        self.duration.setValue(120)
        self.duration.setSuffix(" min")
        self.duration.setStyleSheet(input_style())

        self.table_combo = QComboBox()
        self.table_combo.setStyleSheet(input_style())
        self._load_tables()

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Special requests, allergies, etc.")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setStyleSheet(input_style())

        details_layout.addRow("Date*:", self.date_input)
        details_layout.addRow("Time*:", self.time_input)
        details_layout.addRow("Party Size*:", self.party_size)
        details_layout.addRow("Duration:", self.duration)
        details_layout.addRow("Preferred Table:", self.table_combo)
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
        if self.reservation:
            self._load_reservation_data()

    def _load_tables(self):
        from database.connection import get_db
        conn = get_db()
        tables = conn.execute("SELECT id, number FROM tables ORDER BY number").fetchall()
        conn.close()

        self.table_combo.addItem("Any available", None)
        for table in tables:
            self.table_combo.addItem(f"Table {table['number']}", table['id'])

    def _load_reservation_data(self):
        self.name_input.setText(self.reservation['customer_name'])
        self.phone_input.setText(self.reservation.get('customer_phone', ''))
        self.email_input.setText(self.reservation.get('customer_email', ''))

        res_time = QDateTime.fromString(self.reservation['reservation_time'], Qt.ISODate)
        self.date_input.setDate(res_time.date())
        self.time_input.setTime(res_time.time())

        self.party_size.setValue(self.reservation['party_size'])
        self.duration.setValue(self.reservation.get('duration', 120))

        if self.reservation.get('table_id'):
            index = self.table_combo.findData(self.reservation['table_id'])
            if index >= 0:
                self.table_combo.setCurrentIndex(index)

        self.notes_input.setPlainText(self.reservation.get('special_requests', ''))

    def _save(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Required", "Customer name is required")
            return

        # TODO: Save to database
        self.accept()
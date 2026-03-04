from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QFrame, QMessageBox,
                               QApplication)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QPalette, QLinearGradient, QColor
from database.connection import get_db
from utils.constants import *
from widgets.buttons import AccentButton, GhostButton
from widgets.styles import input_style
import hashlib


class LoginView(QWidget):
    """Login screen for the restaurant management system"""

    login_successful = Signal(dict)  # Emits user data on successful login

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {DARK};")
        self._build()

    def _build(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Center container
        container = QFrame()
        container.setFixedSize(400, 500)
        container.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(20)

        # Logo and title
        logo_label = QLabel("🍽")
        logo_label.setStyleSheet(f"font-size: 64px; color: {ACCENT};")
        logo_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(logo_label)

        title_label = QLabel("RestaurantOS")
        title_label.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)

        subtitle_label = QLabel("Restaurant Management System")
        subtitle_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(subtitle_label)

        # Spacer
        container_layout.addSpacing(20)

        # PIN input
        pin_label = QLabel("Enter your PIN")
        pin_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px; font-weight: 600;")
        container_layout.addWidget(pin_label)

        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("4-6 digit PIN")
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setMaxLength(6)
        self.pin_input.setFixedHeight(44)
        self.pin_input.setStyleSheet(input_style())
        self.pin_input.returnPressed.connect(self._attempt_login)
        container_layout.addWidget(self.pin_input)

        # Login button
        self.login_btn = AccentButton("🔑 Login")
        self.login_btn.setFixedHeight(44)
        self.login_btn.clicked.connect(self._attempt_login)
        container_layout.addWidget(self.login_btn)

        # Error message label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {RED}; font-size: 11px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        container_layout.addWidget(self.error_label)

        # Info text
        info_label = QLabel("Default Admin PIN: 1234")
        info_label.setStyleSheet(f"color: {TEXT2}; font-size: 10px;")
        info_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(info_label)

        container_layout.addStretch()

        layout.addWidget(container)

        # Animation for error message
        self.error_animation = QPropertyAnimation(self.error_label, b"pos")
        self.error_animation.setDuration(100)
        self.error_animation.setEasingCurve(QEasingCurve.OutCubic)

    def _attempt_login(self):
        """Attempt to login with entered PIN"""
        pin = self.pin_input.text().strip()

        if not pin:
            self._show_error("Please enter your PIN")
            return

        if not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
            self._show_error("PIN must be 4-6 digits")
            return

        conn = get_db()

        # Check if user exists with this PIN
        user = conn.execute("""
                            SELECT id, name, role, pin_code, email, phone, is_active
                            FROM staff
                            WHERE pin_code = ?
                              AND is_active = 1
                            """, (pin,)).fetchone()

        conn.close()

        if user:
            # Successful login
            user_dict = dict(user)
            self.login_successful.emit(user_dict)
        else:
            self._show_error("Invalid PIN. Please try again.")

    def _show_error(self, message):
        """Show error message with animation"""
        self.error_label.setText(message)
        self.error_label.setVisible(True)

        # Simple shake animation
        original_pos = self.error_label.pos()
        self.error_animation.setStartValue(original_pos)
        self.error_animation.setKeyValueAt(0.2, original_pos + QtCore.QPoint(10, 0))
        self.error_animation.setKeyValueAt(0.4, original_pos - QtCore.QPoint(10, 0))
        self.error_animation.setKeyValueAt(0.6, original_pos + QtCore.QPoint(5, 0))
        self.error_animation.setKeyValueAt(0.8, original_pos - QtCore.QPoint(5, 0))
        self.error_animation.setEndValue(original_pos)
        self.error_animation.start()

        # Clear PIN input
        self.pin_input.clear()
        self.pin_input.setFocus()

    def clear(self):
        """Clear the login form"""
        self.pin_input.clear()
        self.error_label.setVisible(False)
        self.pin_input.setFocus()
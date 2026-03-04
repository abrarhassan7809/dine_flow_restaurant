from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from widgets.buttons import AccentButton, GhostButton
from widgets.styles import input_style
from database.connection import get_db
from utils.constants import *


class ChangePinDialog(QDialog):
    """Dialog for changing user PIN"""

    def __init__(self, user_id, user_name=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.user_name = user_name
        self.setWindowTitle("Change PIN")
        self.setMinimumSize(400, 350)  # Increased size
        self.setStyleSheet(f"""
            QDialog {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._build()

    def _build(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title bar with close button
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)

        title = QLabel("🔐 Change PIN")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {TEXT};")
        title_bar.addWidget(title)

        title_bar.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT2};
                border: none;
                border-radius: 15px;
                font-size: 16px;
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

        # User info (if available)
        if self.user_name:
            user_info = QHBoxLayout()
            user_info.addWidget(QLabel("User:"))
            user_label = QLabel(self.user_name)
            user_label.setStyleSheet(f"color: {ACCENT}; font-weight: 600;")
            user_info.addWidget(user_label)
            user_info.addStretch()
            layout.addLayout(user_info)

            layout.addSpacing(8)

        # Current PIN
        current_label = QLabel("Current PIN")
        current_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;")
        layout.addWidget(current_label)

        self.current_pin = QLineEdit()
        self.current_pin.setPlaceholderText("Enter your current PIN")
        self.current_pin.setEchoMode(QLineEdit.Password)
        self.current_pin.setMaxLength(6)
        self.current_pin.setFixedHeight(42)
        self.current_pin.setStyleSheet(input_style())
        layout.addWidget(self.current_pin)

        layout.addSpacing(8)

        # New PIN
        new_label = QLabel("New PIN (4-6 digits)")
        new_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;")
        layout.addWidget(new_label)

        self.new_pin = QLineEdit()
        self.new_pin.setPlaceholderText("Enter new PIN")
        self.new_pin.setEchoMode(QLineEdit.Password)
        self.new_pin.setMaxLength(6)
        self.new_pin.setFixedHeight(42)
        self.new_pin.setStyleSheet(input_style())
        layout.addWidget(self.new_pin)

        layout.addSpacing(8)

        # Confirm PIN
        confirm_label = QLabel("Confirm New PIN")
        confirm_label.setStyleSheet(f"color: {TEXT2}; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;")
        layout.addWidget(confirm_label)

        self.confirm_pin = QLineEdit()
        self.confirm_pin.setPlaceholderText("Re-enter new PIN")
        self.confirm_pin.setEchoMode(QLineEdit.Password)
        self.confirm_pin.setMaxLength(6)
        self.confirm_pin.setFixedHeight(42)
        self.confirm_pin.setStyleSheet(input_style())
        layout.addWidget(self.confirm_pin)

        layout.addStretch()

        # Separator
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {BORDER};")
        layout.addWidget(sep2)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = GhostButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)

        save_btn = AccentButton("✓ Save New PIN")
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # Set focus to current PIN field
        self.current_pin.setFocus()

    def _save(self):
        """Save new PIN"""
        current = self.current_pin.text().strip()
        new = self.new_pin.text().strip()
        confirm = self.confirm_pin.text().strip()

        # Validate inputs
        if not current:
            QMessageBox.warning(self, "Error", "Please enter your current PIN")
            self.current_pin.setFocus()
            return

        if not new:
            QMessageBox.warning(self, "Error", "Please enter a new PIN")
            self.new_pin.setFocus()
            return

        if not confirm:
            QMessageBox.warning(self, "Error", "Please confirm your new PIN")
            self.confirm_pin.setFocus()
            return

        if not new.isdigit() or len(new) < 4 or len(new) > 6:
            QMessageBox.warning(self, "Error", "New PIN must be 4-6 digits")
            self.new_pin.clear()
            self.new_pin.setFocus()
            return

        if new != confirm:
            QMessageBox.warning(self, "Error", "New PINs do not match")
            self.confirm_pin.clear()
            self.confirm_pin.setFocus()
            return

        # Verify current PIN
        conn = get_db()
        user = conn.execute(
            "SELECT id, name FROM staff WHERE id = ? AND pin_code = ?",
            (self.user_id, current)
        ).fetchone()

        if not user:
            conn.close()
            QMessageBox.warning(self, "Error", "Current PIN is incorrect")
            self.current_pin.clear()
            self.current_pin.setFocus()
            return

        # Update PIN
        conn.execute(
            "UPDATE staff SET pin_code = ? WHERE id = ?",
            (new, self.user_id)
        )
        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Success",
            f"✅ PIN changed successfully!\n\nYour new PIN has been saved."
        )
        self.accept()
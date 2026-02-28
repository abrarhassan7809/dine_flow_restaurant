from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient
from widgets.styles import button_style
from utils.constants import *


class BaseButton(QPushButton):
    """Base button with common functionality"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._opacity = 1.0

    def set_opacity(self, opacity):
        self._opacity = opacity
        self.update()

    def get_opacity(self):
        return self._opacity

    opacity = Property(float, get_opacity, set_opacity)


class AccentButton(BaseButton):
    """Accent gradient button for primary actions"""

    def __init__(self, text, icon_text="", parent=None):
        super().__init__(f"{icon_text} {text}".strip(), parent)
        self.setStyleSheet(button_style(
            bg=f"qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2})",
            fg=WHITE,
            hover=f"qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT2}, stop:1 {ACCENT})",
            border="transparent",
            padding="10px 20px"
        ))
        self.setFixedHeight(40)


class DangerButton(BaseButton):
    """Red button for destructive actions"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(button_style(
            bg=f"{RED}22",
            fg=RED,
            hover=f"{RED}44",
            border=f"{RED}55"
        ))


class GhostButton(BaseButton):
    """Subtle button for secondary actions"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(button_style())


class SuccessButton(BaseButton):
    """Green button for positive actions"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(button_style(
            bg=f"{GREEN}22",
            fg=GREEN,
            hover=f"{GREEN}44",
            border=f"{GREEN}55"
        ))


class IconButton(QPushButton):
    """Circular button with icon"""

    def __init__(self, icon_text, tooltip="", parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {SURFACE2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 18px;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {ACCENT};
                color: white;
                border-color: {ACCENT};
            }}
            QPushButton:pressed {{
                background: {ACCENT2};
            }}
        """)


class AnimatedButton(BaseButton):
    """Button with hover animation"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(ANIMATION_FAST)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        self.animation.setStartValue(self.opacity)
        self.animation.setEndValue(0.8)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.setStartValue(self.opacity)
        self.animation.setEndValue(1.0)
        self.animation.start()
        super().leaveEvent(event)


class ToggleButton(BaseButton):
    """Button that can be toggled on/off"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked):
        if checked:
            self.setStyleSheet(button_style(
                bg=ACCENT,
                fg=WHITE,
                border="transparent"
            ))
        else:
            self.setStyleSheet(button_style())
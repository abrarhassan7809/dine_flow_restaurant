from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QStackedWidget, QFrame, QPushButton, QLabel,
                               QStatusBar, QApplication, QScrollArea, QSizePolicy,
                               QMessageBox)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QResizeEvent
from views.floor_view import FloorView
from views.inventory_view import InventoryView
from views.order_view import OrderView
from views.kitchen_view import KitchenView
from views.reports_view import ReportsView
from views.menu_manager import MenuManager
from views.reservations_view import ReservationsView
from views.staff_view import StaffView
from views.table_manager import TableManager
from views.login_view import LoginView
from views.change_pin_dialog import ChangePinDialog
from views.audit_view import AuditView  # You'll need to create this
from utils.constants import *
from utils.auth import has_permission, Permission
from utils.audit import audit_logger


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🍽 Restaurant Management System")
        self.current_user = None
        self.login_history_id = None

        screen = QApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(900, 620)
        w = min(int(screen.width() * 0.85), 1400)
        h = min(int(screen.height() * 0.88), 950)
        x = screen.x() + (screen.width() - w) // 2
        y = screen.y() + (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

        # Start with login screen
        self._show_login()

    def _show_login(self):
        """Show the login screen"""
        self.login_view = LoginView()
        self.login_view.login_successful.connect(self._on_login_success)
        self.setCentralWidget(self.login_view)

    def _on_login_success(self, user_data):
        """Handle successful login"""
        self.current_user = user_data
        audit_logger.set_user(user_data)
        self._build_main_interface()

        # Check if this is first login (default PIN)
        if user_data['pin_code'] == '1234' and user_data['role'] == 'admin':
            QTimer.singleShot(1000, self._prompt_change_pin)

    def _prompt_change_pin(self):
        """Prompt user to change default PIN"""
        reply = QMessageBox.question(
            self,
            "Security Alert",
            "You are using the default PIN (1234). For security reasons, you should change it immediately.\n\nWould you like to change your PIN now?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            from views.change_pin_dialog import ChangePinDialog
            dialog = ChangePinDialog(
                self.current_user['id'],  # user_id
                self.current_user['name'],  # user_name (optional)
                self  # parent
            )
            if dialog.exec():
                # Update the PIN in current user data
                QMessageBox.information(
                    self,
                    "Success",
                    "Your PIN has been changed successfully!\n\nPlease use your new PIN for future logins."
                )

    def _build_main_interface(self):
        """Build the main application interface"""
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = self._create_sidebar()
        root.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.content_stack, 1)

        self._init_views()
        self._create_status_bar()
        self._connect_signals()

        # Navigate to first available view based on permissions
        self._navigate_to_first_available()
        self._update_user_info()

    def _create_sidebar(self):
        """Create the sidebar with user info and navigation based on permissions"""
        sidebar = QFrame()
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border-right: 1px solid {BORDER};
            }}
        """)

        outer = QVBoxLayout(sidebar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Logo / header
        header = QFrame()
        header.setFixedHeight(72)
        header.setStyleSheet(f"border-bottom: 1px solid {BORDER};")
        h_lay = QVBoxLayout(header)
        h_lay.setContentsMargins(16, 12, 16, 12)
        h_lay.setSpacing(2)

        self.logo = QLabel("🍽 RestaurantOS")
        self.logo.setStyleSheet(f"color: {ACCENT}; font-size: 16px; font-weight: 800;")
        h_lay.addWidget(self.logo)

        self.subtitle = QLabel("Management System")
        self.subtitle.setStyleSheet(f"color: {TEXT2}; font-size: 11px;")
        h_lay.addWidget(self.subtitle)
        outer.addWidget(header)

        # Scrollable nav
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        nav_container = QWidget()
        nav_container.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 8, 0, 8)
        nav_layout.setSpacing(2)

        self.nav_buttons = []
        self.nav_indices = []  # Store which indices are actually available

        self._nav_items = [
            ("🏠", "Floor Plan", 0, Permission.VIEW_FLOOR),
            ("📝", "New Order", 1, Permission.VIEW_ORDERS),
            ("🍳", "Kitchen", 2, Permission.VIEW_KITCHEN),
            ("📊", "Reports", 3, Permission.VIEW_REPORTS),
            ("🍴", "Menu", 4, Permission.VIEW_MENU),
            ("🪑", "Tables", 5, Permission.VIEW_TABLES),
            ("📅", "Reservations", 6, Permission.VIEW_RESERVATIONS),
            ("📦", "Inventory", 7, Permission.VIEW_INVENTORY),
            ("👥", "Staff", 8, Permission.VIEW_STAFF),
        ]

        # Add Audit Log for admin only
        if self.current_user and self.current_user['role'] == 'admin':
            self._nav_items.append(("📋", "Audit Log", 9, Permission.VIEW_AUDIT))

        for icon, label, idx, permission in self._nav_items:
            # Check if user has permission to view this section
            if has_permission(self.current_user['role'], permission):
                btn = QPushButton(f"  {icon}  {label}")
                btn.setCheckable(True)
                btn.setFixedHeight(44)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {TEXT2};
                        border: none;
                        text-align: left;
                        padding: 0 16px;
                        font-size: 13px;
                        font-weight: 500;
                        border-left: 3px solid transparent;
                    }}
                    QPushButton:hover   {{ background: {SURFACE2}; color: {TEXT}; }}
                    QPushButton:checked {{
                        background: {ACCENT}15;
                        color: {ACCENT};
                        font-weight: 600;
                        border-left-color: {ACCENT};
                    }}
                """)
                btn.clicked.connect(lambda _checked, i=idx: self._navigate(i))
                nav_layout.addWidget(btn)
                self.nav_buttons.append(btn)
                self.nav_indices.append(idx)

        nav_layout.addStretch()
        nav_scroll.setWidget(nav_container)
        outer.addWidget(nav_scroll, 1)

        # User section with logout button
        user_frame = QFrame()
        user_frame.setFixedHeight(120)
        user_frame.setStyleSheet(f"border-top: 1px solid {BORDER};")
        u_lay = QVBoxLayout(user_frame)
        u_lay.setContentsMargins(16, 10, 16, 10)
        u_lay.setSpacing(2)

        self.user_name = QLabel("")
        self.user_name.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 13px;")
        u_lay.addWidget(self.user_name)

        self.user_role = QLabel("")
        self.user_role.setStyleSheet(f"color: {TEXT2}; font-size: 11px;")
        u_lay.addWidget(self.user_role)

        # Change PIN button
        change_pin_btn = QPushButton("🔑 Change PIN")
        change_pin_btn.setFixedHeight(30)
        change_pin_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {BLUE};
                border: 1px solid {BLUE}55;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                margin-top: 5px;
            }}
            QPushButton:hover {{
                background: {BLUE};
                color: white;
            }}
        """)
        change_pin_btn.clicked.connect(self._change_pin)
        u_lay.addWidget(change_pin_btn)

        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setFixedHeight(30)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {RED};
                border: 1px solid {RED}55;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                margin-top: 5px;
            }}
            QPushButton:hover {{
                background: {RED};
                color: white;
            }}
        """)
        logout_btn.clicked.connect(self._logout)
        u_lay.addWidget(logout_btn)

        outer.addWidget(user_frame)

        return sidebar

    def _change_pin(self):
        """Open change PIN dialog"""
        from views.change_pin_dialog import ChangePinDialog
        dialog = ChangePinDialog(
            self.current_user['id'],
            self.current_user['name'],
            self
        )
        if dialog.exec():
            # Log PIN change
            audit_logger.log(
                'UPDATE',
                'staff',
                self.current_user['id'],
                None,
                'PIN changed'
            )
            QMessageBox.information(
                self,
                "Success",
                "Your PIN has been changed successfully!"
            )

    def _update_user_info(self):
        """Update user information in sidebar"""
        if self.current_user:
            self.user_name.setText(self.current_user['name'])
            role = self.current_user['role'].capitalize()
            self.user_role.setText(role)

    def _logout(self):
        """Log out current user"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Log logout
            if self.current_user:
                audit_logger.log_logout(self.current_user['id'])

            self.current_user = None
            audit_logger.set_user(None)
            self._show_login()

    def _navigate_to_first_available(self):
        """Navigate to the first available view based on permissions"""
        if self.nav_indices:
            self._navigate(self.nav_indices[0])

    def _init_views(self):
        """Initialize all views"""
        self.views = {}

        # Only initialize views that the user has permission to access
        if has_permission(self.current_user['role'], Permission.VIEW_FLOOR):
            self.views[0] = FloorView()

        if has_permission(self.current_user['role'], Permission.VIEW_ORDERS):
            self.views[1] = OrderView()

        if has_permission(self.current_user['role'], Permission.VIEW_KITCHEN):
            self.views[2] = KitchenView()

        if has_permission(self.current_user['role'], Permission.VIEW_REPORTS):
            self.views[3] = ReportsView()

        if has_permission(self.current_user['role'], Permission.VIEW_MENU):
            self.views[4] = MenuManager()

        if has_permission(self.current_user['role'], Permission.VIEW_TABLES):
            self.views[5] = TableManager()

        if has_permission(self.current_user['role'], Permission.VIEW_RESERVATIONS):
            self.views[6] = ReservationsView()

        if has_permission(self.current_user['role'], Permission.VIEW_INVENTORY):
            self.views[7] = InventoryView()

        if has_permission(self.current_user['role'], Permission.VIEW_STAFF):
            self.views[8] = StaffView()

        # Audit view for admin
        if self.current_user['role'] == 'admin':
            from views.audit_view import AuditView
            self.views[9] = AuditView()

        # Add all views to stack
        for view in self.views.values():
            self.content_stack.addWidget(view)

    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(30)
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {SURFACE};
                color: {TEXT2};
                border-top: 1px solid {BORDER};
                padding: 0 8px;
                font-size: 12px;
            }}
            QStatusBar::item {{ border: none; }}
        """)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {TEXT2}; padding: 0 8px;")
        self.status_bar.addWidget(self.status_label, 1)

        self.status_bar.addPermanentWidget(self._vsep())

        # Show current user
        user_indicator = QLabel(f"👤 {self.current_user['name']} ({self.current_user['role'].capitalize()})")
        user_indicator.setStyleSheet(f"color: {ACCENT}; padding: 0 8px;")
        self.status_bar.addPermanentWidget(user_indicator)

        self.status_bar.addPermanentWidget(self._vsep())

        self.connection_label = QLabel("● Connected")
        self.connection_label.setStyleSheet(f"color: {GREEN}; padding: 0 8px;")
        self.status_bar.addPermanentWidget(self.connection_label)

        self.status_bar.addPermanentWidget(self._vsep())

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(f"color: {TEXT2}; padding: 0 8px;")
        self.status_bar.addPermanentWidget(self.clock_label)

        # Setup clock
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _vsep(self) -> QFrame:
        """Create vertical separator"""
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background: {BORDER};")
        return sep

    def _update_clock(self):
        """Update clock display"""
        self.clock_label.setText(
            QDateTime.currentDateTime().toString("ddd, MMM d yyyy  •  h:mm:ss AP")
        )

    def _navigate(self, index: int):
        """Navigate to different views"""
        if index in self.views:
            for i, btn in enumerate(self.nav_buttons):
                btn.setChecked(i == self.nav_indices.index(index))
            self.content_stack.setCurrentWidget(self.views[index])

            view = self.views[index]
            if hasattr(view, "refresh"):
                view.refresh()

            # Find the nav item text
            for icon, label, idx, _ in self._nav_items:
                if idx == index:
                    self.status_label.setText(f"Viewing: {icon} {label}")
                    break

    def _connect_signals(self):
        """Connect signals between views"""
        # Floor → order (if both views exist)
        if 0 in self.views and hasattr(self.views[0], "table_selected") and 1 in self.views:
            self.views[0].table_selected.connect(self._open_order)

        # Order updates → refresh floor, kitchen, tables
        if 1 in self.views and hasattr(self.views[1], "order_updated"):
            if 0 in self.views:
                self.views[1].order_updated.connect(self.views[0].refresh)
            if 2 in self.views:
                self.views[1].order_updated.connect(self.views[2].refresh)
            if 5 in self.views:
                self.views[1].order_updated.connect(self.views[5].refresh)

        # Table manager changes → refresh floor
        if 5 in self.views and hasattr(self.views[5], "tables_updated") and 0 in self.views:
            self.views[5].tables_updated.connect(self.views[0].refresh)

    def _open_order(self, table_id: int):
        """Open order view for specific table"""
        if 1 in self.views:
            self._navigate(1)
            self.views[1].load_table(table_id)

    def resizeEvent(self, event: QResizeEvent):
        """Handle resize events"""
        super().resizeEvent(event)
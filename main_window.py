from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QStackedWidget, QFrame, QPushButton, QLabel,
                               QStatusBar, QApplication, QScrollArea, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QResizeEvent
from views.floor_view import FloorView
from views.order_view import OrderView
from views.kitchen_view import KitchenView
from views.reports_view import ReportsView
from views.menu_manager import MenuManager
from views.table_manager import TableManager
from utils.constants import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🍽 Restaurant Management System")

        screen = QApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(900, 620)
        w = min(int(screen.width() * 0.85), 1400)
        h = min(int(screen.height() * 0.88), 950)
        x = screen.x() + (screen.width()  - w) // 2
        y = screen.y() + (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

        self._build()
        self._setup_auto_refresh()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # BUG C FIX: plain fixed-width sidebar, no QSplitter fighting min/max
        self.sidebar = self._create_sidebar()
        root.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.content_stack, 1)

        # BUG E FIX: _init_views BEFORE _connect_signals so self.views exists
        self._init_views()
        self._create_status_bar()
        self._connect_signals()

        self.nav_buttons[0].setChecked(True)

    # ── Sidebar ────────────────────────────────────────────────────────────────

    def _create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(SIDEBAR_WIDTH)   # BUG C FIX: single width constraint
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

        # Scrollable nav so items are never clipped on short screens
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

        # BUG D FIX: keep full labels in a separate list; never mangle btn text
        self._nav_items = [
            ("🏠", "Floor Plan"),
            ("📝", "New Order"),
            ("🍳", "Kitchen"),
            ("📊", "Reports"),
            ("🍴", "Menu"),
            ("🪑", "Tables"),
            ("📅", "Reservations"),
            ("📦", "Inventory"),
            ("👥", "Staff"),
        ]

        for idx, (icon, label) in enumerate(self._nav_items):
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

        nav_layout.addStretch()
        nav_scroll.setWidget(nav_container)
        outer.addWidget(nav_scroll, 1)

        # User section
        user_frame = QFrame()
        user_frame.setFixedHeight(68)
        user_frame.setStyleSheet(f"border-top: 1px solid {BORDER};")
        u_lay = QVBoxLayout(user_frame)
        u_lay.setContentsMargins(16, 10, 16, 10)
        u_lay.setSpacing(2)

        self.user_name = QLabel("John Doe")
        self.user_name.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 13px;")
        u_lay.addWidget(self.user_name)

        self.user_role = QLabel("Manager")
        self.user_role.setStyleSheet(f"color: {TEXT2}; font-size: 11px;")
        u_lay.addWidget(self.user_role)
        outer.addWidget(user_frame)

        return sidebar

    # ── Views ──────────────────────────────────────────────────────────────────

    def _init_views(self):
        self.views = {
            0: FloorView(),
            1: OrderView(),
            2: KitchenView(),
            3: ReportsView(),
            4: MenuManager(),
            5: TableManager(),
            6: self._placeholder("📅  Reservations"),
            7: self._placeholder("📦  Inventory"),
            8: self._placeholder("👥  Staff"),
        }
        for view in self.views.values():
            self.content_stack.addWidget(view)

    def _placeholder(self, title: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {DARK};")
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {TEXT}; font-size: 22px; font-weight: 700;")
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)
        sub = QLabel("Coming Soon")
        sub.setStyleSheet(f"color: {TEXT2}; font-size: 14px; margin-top: 6px;")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)
        return w

    # ── Status bar ─────────────────────────────────────────────────────────────

    def _create_status_bar(self):
        # BUG B FIX: static 30 px — no dynamic recalculation on every resize
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

        self.connection_label = QLabel("● Connected")
        self.connection_label.setStyleSheet(f"color: {GREEN}; padding: 0 8px;")
        self.status_bar.addPermanentWidget(self.connection_label)

        self.status_bar.addPermanentWidget(self._vsep())

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(f"color: {TEXT2}; padding: 0 8px;")
        self.status_bar.addPermanentWidget(self.clock_label)

    def _vsep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background: {BORDER};")
        return sep

    # ── Auto-refresh clock ─────────────────────────────────────────────────────

    def _setup_auto_refresh(self):
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        self.clock_label.setText(
            QDateTime.currentDateTime().toString("ddd, MMM d yyyy  •  h:mm:ss AP")
        )

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _navigate(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.content_stack.setCurrentIndex(index)

        view = self.views.get(index)
        if hasattr(view, "refresh"):
            view.refresh()

        icon, label = self._nav_items[index]
        self.status_label.setText(f"Viewing: {icon} {label}")

    def _connect_signals(self):
        # Floor → order
        if hasattr(self.views[0], "table_selected"):
            self.views[0].table_selected.connect(self._open_order)

        # Order updates → refresh floor, kitchen, tables
        if hasattr(self.views[1], "order_updated"):
            self.views[1].order_updated.connect(self.views[0].refresh)
            self.views[1].order_updated.connect(self.views[2].refresh)
            self.views[1].order_updated.connect(self.views[5].refresh)

        # Table manager changes → refresh floor
        if hasattr(self.views[5], "tables_updated"):
            self.views[5].tables_updated.connect(self.views[0].refresh)

    def _open_order(self, table_id: int):
        self._navigate(1)
        self.views[1].load_table(table_id)

    # BUG A FIX: eventFilter + handle_resize removed entirely.
    # The sidebar is fixed-width so there is nothing to do on resize.
    # resizeEvent is kept as a clean no-op override for future use.
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
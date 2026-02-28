"""
views/reports_view.py — fully corrected

BUG 6  FIX: PURPLE constant used in _update_charts() but never defined anywhere.
             Added PURPLE to constants and the chart colour list.
BUG 8  FIX: get_sales_summary() imported but missing from helpers.py → ImportError.
             Function now implemented in utils/helpers.py.
BUG 9  FIX: MetricCard missing from widgets.cards — defined inline here to be
             self-contained; no external dependency needed.
BUG 10 FIX: refresh() never called on startup → blank view.
             Added explicit self.refresh() call at end of __init__.
BUG 11 FIX: Orders query used INNER JOIN on tables, silently excluding takeaway
             orders (table_id = NULL). Changed to LEFT JOIN.
BUG 12 FIX: _update_charts guarded with safe .get() fallbacks so missing summary
             keys don't crash the chart renderer.
BUG 13 FIX: Chart axes and figure backgrounds set to dark theme colours.
             PURPLE added to constants (now imported from there).
"""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QTabWidget, QDateEdit, QComboBox,
                               QMessageBox, QSizePolicy)
from PySide6.QtCore import Qt, QDate

from widgets.buttons import AccentButton, GhostButton
from widgets.styles import input_style
from utils.constants import *
from utils.helpers import format_currency, get_sales_summary
from database.connection import get_db

try:
    import matplotlib
    matplotlib.use("Qt5Agg")
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    _HAS_MATPLOTLIB = True
except ImportError:
    _HAS_MATPLOTLIB = False


# ── Inline MetricCard (BUG 9 FIX) ─────────────────────────────────────────────

class MetricCard(QFrame):
    """Small KPI card showing a title, big value and subtitle."""

    def __init__(self, title: str, value: str, subtitle: str = "",
                 color: str = None, parent=None):
        super().__init__(parent)
        color = color or ACCENT
        self.setMinimumWidth(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE2};
                border: 1px solid {BORDER};
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            f"color: {TEXT2}; font-size: 11px; font-weight: 700;"
            f" letter-spacing: 0.5px; background: transparent;"
        )
        lay.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: 800; background: transparent;"
        )
        lay.addWidget(lbl_value)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setStyleSheet(f"color: {TEXT2}; font-size: 11px; background: transparent;")
            lay.addWidget(lbl_sub)


# ── ReportsView ────────────────────────────────────────────────────────────────

class ReportsView(QWidget):
    """Analytics and reporting dashboard."""

    def __init__(self):
        super().__init__()
        self._build()
        # BUG 10 FIX: load data on construction so view is never blank
        self.refresh()

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        layout.addLayout(self._create_header())
        layout.addLayout(self._create_date_selector())

        # Metric cards row
        self.metrics_layout = QHBoxLayout()
        self.metrics_layout.setSpacing(16)
        layout.addLayout(self.metrics_layout)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabBar::tab {{
                background: {SURFACE2};
                color: {TEXT2};
                border: 1px solid {BORDER};
                padding: 8px 16px;
                border-radius: 6px 6px 0 0;
                margin-right: 2px;
                font-weight: 600;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background: {ACCENT};
                color: white;
                border-color: {ACCENT};
            }}
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                background: {SURFACE};
                border-radius: 0 8px 8px 8px;
                padding: 12px;
            }}
        """)

        self.sales_table  = self._make_table()
        self.items_table  = self._make_table()
        self.orders_table = self._make_table()

        tabs.addTab(self._wrap(self.sales_table),  "💰 Sales Summary")
        tabs.addTab(self._wrap(self.items_table),  "🏆 Top Items")
        tabs.addTab(self._wrap(self.orders_table), "📋 All Orders")

        if _HAS_MATPLOTLIB:
            self.chart_widget = self._create_charts()
            tabs.addTab(self._wrap(self.chart_widget), "📊 Charts")

        layout.addWidget(tabs, 1)

        # Export buttons
        exp_row = QHBoxLayout()
        exp_row.addStretch()
        for label, slot in [
            ("📥 Export CSV", self._export_csv),
            ("📥 Export PDF", self._export_pdf),
            ("🖨️ Print",       self._print_report),
        ]:
            btn = GhostButton(label)
            btn.clicked.connect(slot)
            exp_row.addWidget(btn)
        layout.addLayout(exp_row)

    def _make_table(self) -> QTableWidget:
        tbl = QTableWidget()
        tbl.setStyleSheet(f"""
            QTableWidget {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                gridline-color: {SURFACE2};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {TEXT};
                border-bottom: 1px solid {SURFACE2};
            }}
            QHeaderView::section {{
                background: {SURFACE2};
                color: {TEXT2};
                border: none;
                padding: 8px;
                font-weight: 700;
                font-size: 11px;
            }}
        """)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        return tbl

    def _wrap(self, widget: QWidget) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(widget)
        return container

    def _create_header(self):
        hdr = QHBoxLayout()
        title = QLabel("📊 Reports & Analytics")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT};")
        hdr.addWidget(title)
        hdr.addStretch()
        refresh_btn = GhostButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        hdr.addWidget(refresh_btn)
        return hdr

    def _create_date_selector(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        date_style = f"""
            QDateEdit {{
                background: {SURFACE2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
        """

        row.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setStyleSheet(date_style)
        row.addWidget(self.date_from)

        row.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setStyleSheet(date_style)
        row.addWidget(self.date_to)

        apply_btn = AccentButton("Apply")
        apply_btn.clicked.connect(self.refresh)
        row.addWidget(apply_btn)
        row.addStretch()

        # Quick-filter combo — block signals while populating to avoid premature refresh
        self.quick_filter = QComboBox()
        self.quick_filter.setStyleSheet(date_style)
        self.quick_filter.blockSignals(True)
        self.quick_filter.addItems([
            "Today", "Yesterday", "Last 7 Days",
            "Last 30 Days", "This Month", "Last Month",
        ])
        self.quick_filter.blockSignals(False)
        self.quick_filter.currentTextChanged.connect(self._apply_quick_filter)
        row.addWidget(self.quick_filter)

        return row

    def _create_charts(self) -> QWidget:
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        self.figure = Figure(figsize=(10, 6), facecolor=SURFACE)
        self.canvas = FigureCanvas(self.figure)
        lay.addWidget(self.canvas)
        return widget

    # ── Data refresh ───────────────────────────────────────────────────────────

    def refresh(self):
        from_date = self.date_from.date().toString("yyyy-MM-dd")
        to_date   = self.date_to.date().toString("yyyy-MM-dd")

        # Clear metric cards
        while self.metrics_layout.count():
            item = self.metrics_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        summary = get_sales_summary(from_date, to_date)
        stats   = summary["stats"]

        # Add metric cards
        for title, value, subtitle, color in [
            ("Total Revenue",   format_currency(stats["total_revenue"]),
             f"{stats['order_count']} orders",  GREEN),
            ("Avg Order Value",  format_currency(stats["avg_order_value"]),
             "per transaction",                 BLUE),
            ("Tax Collected",    format_currency(stats["total_tax"]),
             "10% of subtotal",                 YELLOW),
            ("Discounts Given",  format_currency(stats["total_discounts"]),
             "total discounts",                 ACCENT),
        ]:
            # BUG 9 FIX: MetricCard defined inline above — no external import needed
            self.metrics_layout.addWidget(MetricCard(title, value, subtitle, color=color))

        self._update_sales_table(from_date, to_date)
        self._update_items_table(summary["top_items"])
        self._update_orders_table(from_date, to_date)

        if _HAS_MATPLOTLIB:
            self._update_charts(summary)

    # ── Sales summary tab ──────────────────────────────────────────────────────

    def _update_sales_table(self, from_date: str, to_date: str):
        conn = get_db()
        try:
            rows = conn.execute("""
                SELECT
                    DATE(created_at)   AS sale_date,
                    COUNT(*)           AS order_count,
                    SUM(total)         AS revenue,
                    SUM(tax)           AS tax,
                    SUM(discount)      AS discounts,
                    AVG(total)         AS avg_order
                FROM orders
                WHERE status = 'paid'
                  AND DATE(created_at) BETWEEN DATE(?) AND DATE(?)
                GROUP BY DATE(created_at)
                ORDER BY sale_date DESC
            """, (from_date, to_date)).fetchall()
        finally:
            conn.close()

        self.sales_table.setRowCount(len(rows))
        self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels(
            ["Date", "Orders", "Revenue", "Tax", "Discounts", "Avg Order"]
        )
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for r, sale in enumerate(rows):
            self.sales_table.setItem(r, 0, QTableWidgetItem(sale["sale_date"] or ""))
            self.sales_table.setItem(r, 1, QTableWidgetItem(str(sale["order_count"])))
            self.sales_table.setItem(r, 2, QTableWidgetItem(format_currency(sale["revenue"])))
            self.sales_table.setItem(r, 3, QTableWidgetItem(format_currency(sale["tax"])))
            self.sales_table.setItem(r, 4, QTableWidgetItem(format_currency(sale["discounts"])))
            self.sales_table.setItem(r, 5, QTableWidgetItem(format_currency(sale["avg_order"])))

    # ── Top items tab ──────────────────────────────────────────────────────────

    def _update_items_table(self, top_items: list):
        self.items_table.setRowCount(len(top_items))
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(["Item", "Qty Sold", "Revenue"])
        hdr = self.items_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        for r, item in enumerate(top_items):
            self.items_table.setItem(r, 0, QTableWidgetItem(item["name"]))
            self.items_table.setItem(r, 1, QTableWidgetItem(str(item["quantity_sold"])))
            self.items_table.setItem(r, 2, QTableWidgetItem(format_currency(item["revenue"])))

    # ── All orders tab ─────────────────────────────────────────────────────────

    def _update_orders_table(self, from_date: str, to_date: str):
        conn = get_db()
        try:
            # BUG 11 FIX: LEFT JOIN so takeaway orders (table_id=NULL) are included
            rows = conn.execute("""
                SELECT
                    o.id,
                    COALESCE(t.number, 0)   AS table_number,
                    o.waiter,
                    o.status,
                    o.created_at,
                    o.total,
                    o.is_takeaway,
                    COUNT(oi.id)            AS item_count
                FROM orders o
                LEFT JOIN tables t     ON o.table_id   = t.id
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE DATE(o.created_at) BETWEEN DATE(?) AND DATE(?)
                GROUP BY o.id
                ORDER BY o.id DESC
                LIMIT 200
            """, (from_date, to_date)).fetchall()
        finally:
            conn.close()

        self.orders_table.setRowCount(len(rows))
        self.orders_table.setColumnCount(7)
        self.orders_table.setHorizontalHeaderLabels(
            ["Order #", "Table", "Waiter", "Status", "Items", "Date/Time", "Total"]
        )
        hdr = self.orders_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        for r, order in enumerate(rows):
            self.orders_table.setItem(r, 0, QTableWidgetItem(f"#{order['id']}"))

            # BUG 11 FIX: show "Takeaway" for orders with no table
            if order["is_takeaway"] or not order["table_number"]:
                table_text = "Takeaway"
            else:
                table_text = f"Table {order['table_number']}"
            self.orders_table.setItem(r, 1, QTableWidgetItem(table_text))
            self.orders_table.setItem(r, 2, QTableWidgetItem(order["waiter"] or "—"))

            status_item = QTableWidgetItem(order["status"].upper())
            status_item.setForeground(QColor(ORDER_STATUS_COLORS.get(order["status"], TEXT2)))
            self.orders_table.setItem(r, 3, status_item)
            self.orders_table.setItem(r, 4, QTableWidgetItem(str(order["item_count"])))
            self.orders_table.setItem(r, 5, QTableWidgetItem(
                (order["created_at"] or "")[:16]
            ))
            self.orders_table.setItem(r, 6, QTableWidgetItem(format_currency(order["total"])))

    # ── Charts tab ─────────────────────────────────────────────────────────────

    def _update_charts(self, summary: dict):
        """
        BUG 6  FIX: PURPLE added to constants (imported via *).
        BUG 12 FIX: safe .get() with fallbacks — missing keys don't crash renderer.
        BUG 13 FIX: axes and figure set to dark-theme background colours.
        """
        self.figure.clear()

        gs  = self.figure.add_gridspec(2, 2, hspace=0.4, wspace=0.35)
        ax1 = self.figure.add_subplot(gs[0, 0])
        ax2 = self.figure.add_subplot(gs[0, 1])
        ax3 = self.figure.add_subplot(gs[1, :])

        for ax in (ax1, ax2, ax3):
            ax.set_facecolor(SURFACE2)        # BUG 13 FIX: dark background
            for spine in ax.spines.values():
                spine.set_color(BORDER)
            ax.tick_params(colors=TEXT2, labelsize=9)

        # Payment methods pie
        payments = summary.get("payments", [])   # BUG 12 FIX
        if payments:
            methods = [p["payment_method"] for p in payments]
            amounts = [p["total"]          for p in payments]
            # BUG 6 FIX: PURPLE is now defined in constants
            pie_colors = [BLUE, GREEN, YELLOW, ACCENT, PURPLE][:len(methods)]
            ax1.pie(amounts, labels=methods, colors=pie_colors,
                    autopct="%1.1f%%", textprops={"color": TEXT2, "fontsize": 9})
            ax1.set_title("Payment Methods", color=TEXT, fontsize=11, pad=8)
        else:
            ax1.text(0.5, 0.5, "No payment data",
                     ha="center", va="center", color=TEXT2, transform=ax1.transAxes)
            ax1.set_title("Payment Methods", color=TEXT, fontsize=11)

        # Top items bar chart
        top_items = summary.get("top_items", [])   # BUG 12 FIX
        if top_items:
            names = [
                (i["name"][:14] + "…" if len(i["name"]) > 14 else i["name"])
                for i in top_items[:6]
            ]
            qtys = [i["quantity_sold"] for i in top_items[:6]]
            bars = ax2.barh(names, qtys, color=ACCENT)
            ax2.bar_label(bars, padding=4, color=TEXT2, fontsize=8)
            ax2.set_title("Top Selling Items", color=TEXT, fontsize=11)
            ax2.set_xlabel("Qty Sold", color=TEXT2, fontsize=9)
        else:
            ax2.text(0.5, 0.5, "No sales data",
                     ha="center", va="center", color=TEXT2, transform=ax2.transAxes)
            ax2.set_title("Top Selling Items", color=TEXT, fontsize=11)

        # Hourly revenue line
        hourly = summary.get("hourly", [])   # BUG 12 FIX
        if hourly:
            hours   = [f"{int(h['hour']):02d}:00" for h in hourly]
            revenue = [h["revenue"] for h in hourly]
            ax3.plot(hours, revenue, marker="o", color=GREEN, linewidth=2, markersize=5)
            ax3.fill_between(range(len(hours)), revenue, alpha=0.15, color=GREEN)
            ax3.set_xticks(range(len(hours)))
            ax3.set_xticklabels(hours, rotation=45, ha="right")
            ax3.set_title("Hourly Sales", color=TEXT, fontsize=11)
            ax3.set_xlabel("Hour", color=TEXT2, fontsize=9)
            ax3.set_ylabel("Revenue ($)", color=TEXT2, fontsize=9)
            ax3.grid(True, alpha=0.2, color=BORDER, linestyle="--")
        else:
            ax3.text(0.5, 0.5, "No hourly data for this period",
                     ha="center", va="center", color=TEXT2, transform=ax3.transAxes)
            ax3.set_title("Hourly Sales", color=TEXT, fontsize=11)

        self.figure.patch.set_facecolor(SURFACE)
        self.canvas.draw()

    # ── Quick filter ───────────────────────────────────────────────────────────

    def _apply_quick_filter(self, text: str):
        today = QDate.currentDate()
        if text == "Today":
            self.date_from.setDate(today)
            self.date_to.setDate(today)
        elif text == "Yesterday":
            self.date_from.setDate(today.addDays(-1))
            self.date_to.setDate(today.addDays(-1))
        elif text == "Last 7 Days":
            self.date_from.setDate(today.addDays(-6))
            self.date_to.setDate(today)
        elif text == "Last 30 Days":
            self.date_from.setDate(today.addDays(-29))
            self.date_to.setDate(today)
        elif text == "This Month":
            self.date_from.setDate(QDate(today.year(), today.month(), 1))
            self.date_to.setDate(today)
        elif text == "Last Month":
            lm = today.addMonths(-1)
            self.date_from.setDate(QDate(lm.year(), lm.month(), 1))
            self.date_to.setDate(QDate(lm.year(), lm.month(), lm.daysInMonth()))
        self.refresh()

    # ── Export stubs ───────────────────────────────────────────────────────────

    def _export_csv(self):
        QMessageBox.information(self, "Export", "CSV export coming soon!")

    def _export_pdf(self):
        QMessageBox.information(self, "Export", "PDF export coming soon!")

    def _print_report(self):
        QMessageBox.information(self, "Print", "Print feature coming soon!")
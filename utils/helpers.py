import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtCore import QSize


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"


def format_datetime(dt_str: str, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime string"""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime(format)
    except:
        return dt_str


def format_time_ago(dt_str: str) -> str:
    """Format time ago string"""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds // 3600 > 0:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds // 60 > 0:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"
    except:
        return dt_str


def truncate_text(text: str, max_width: int, font: QFont) -> str:
    """Truncate text to fit max width"""
    metrics = QFontMetrics(font)
    if metrics.horizontalAdvance(text) <= max_width:
        return text

    while metrics.horizontalAdvance(text + "...") > max_width and len(text) > 3:
        text = text[:-1]

    return text + "..."


def generate_bill_number() -> str:
    """Generate unique bill number"""
    date_str = datetime.now().strftime("%Y%m%d")
    time_str = datetime.now().strftime("%H%M%S")
    hash_obj = hashlib.md5(f"{date_str}{time_str}".encode())
    return f"B{date_str}{hash_obj.hexdigest()[:6].upper()}"


def parse_modifiers(modifiers_json: Optional[str]) -> List[Dict]:
    """Parse modifiers JSON"""
    if not modifiers_json:
        return []
    try:
        return json.loads(modifiers_json)
    except:
        return []


def calculate_prep_time(items: List[Dict]) -> int:
    """Calculate total preparation time for items"""
    if not items:
        return 0

    # Group by prep time and calculate parallel preparation
    prep_times = {}
    for item in items:
        time = item.get('prep_time', 10)
        prep_times[time] = prep_times.get(time, 0) + item.get('quantity', 1)

    # Maximum time is the longest prep time
    # But if multiple items with same time, they're prepared in parallel
    return max(prep_times.keys()) if prep_times else 0


def get_sales_summary(start_date: str, end_date: str) -> Dict:
    """Get sales summary for date range"""
    from database.connection import get_db

    conn = get_db()

    # Overall stats
    stats = conn.execute("""
        SELECT 
            COUNT(DISTINCT o.id) as order_count,
            COALESCE(SUM(o.total), 0) as total_revenue,
            COALESCE(AVG(o.total), 0) as avg_order_value,
            COALESCE(SUM(CASE WHEN o.is_takeaway = 1 THEN o.total ELSE 0 END), 0) as takeaway_revenue,
            COALESCE(SUM(o.tax), 0) as total_tax,
            COALESCE(SUM(o.discount), 0) as total_discounts,
            COALESCE(SUM(o.service_charge), 0) as total_service_charge
        FROM orders o
        WHERE o.status = 'paid' 
            AND DATE(o.created_at) BETWEEN DATE(?) AND DATE(?)
    """, (start_date, end_date)).fetchone()

    # Payment methods breakdown
    payments = conn.execute("""
        SELECT 
            payment_method,
            COUNT(*) as count,
            SUM(amount_paid) as total,
            AVG(amount_paid) as average
        FROM bills b
        JOIN orders o ON b.order_id = o.id
        WHERE o.status = 'paid'
            AND DATE(o.created_at) BETWEEN DATE(?) AND DATE(?)
        GROUP BY payment_method
    """, (start_date, end_date)).fetchall()

    # Top items
    top_items = conn.execute("""
        SELECT 
            mi.name,
            SUM(oi.quantity) as quantity_sold,
            SUM(oi.quantity * oi.unit_price) as revenue
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = 'paid'
            AND DATE(o.created_at) BETWEEN DATE(?) AND DATE(?)
        GROUP BY mi.id
        ORDER BY quantity_sold DESC
        LIMIT 10
    """, (start_date, end_date)).fetchall()

    # Hourly breakdown
    hourly = conn.execute("""
        SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as orders,
            SUM(total) as revenue
        FROM orders
        WHERE status = 'paid'
            AND DATE(created_at) BETWEEN DATE(?) AND DATE(?)
        GROUP BY hour
        ORDER BY hour
    """, (start_date, end_date)).fetchall()

    conn.close()

    return {
        'stats': dict(stats),
        'payments': [dict(p) for p in payments],
        'top_items': [dict(i) for i in top_items],
        'hourly': [dict(h) for h in hourly]
    }


def get_current_shift(staff_id: int) -> Optional[Dict]:
    """Get current active shift for staff"""
    from database.connection import get_db

    conn = get_db()
    shift = conn.execute("""
        SELECT * FROM shifts 
        WHERE staff_id = ? AND end_time IS NULL
        ORDER BY start_time DESC LIMIT 1
    """, (staff_id,)).fetchone()
    conn.close()

    return dict(shift) if shift else None


def log_audit(user: str, action: str, table: str, record_id: int,
              old_value: Any = None, new_value: Any = None):
    """Log action to audit trail"""
    from database.connection import get_db

    conn = get_db()
    conn.execute("""
        INSERT INTO audit_log (user, action, table_name, record_id, old_value, new_value)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user, action, table, record_id, str(old_value), str(new_value)))
    conn.commit()
    conn.close()
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = str(BASE_DIR / "restaurant.db")

# ── Finance ────────────────────────────────────────────────────────────────────
TAX_RATE            = 0.10
SERVICE_CHARGE_RATE = 0.05

# ── UI Layout ──────────────────────────────────────────────────────────────────
# BUG N / Q FIX: TABLE_SPACING and KITCHEN_REFRESH_INTERVAL were missing entirely
TABLE_SPACING            = 16     # px gap between table cards in floor grid
KITCHEN_REFRESH_INTERVAL = 15000  # ms — auto-refresh kitchen display every 15 s
SIDEBAR_WIDTH            = 220    # px — fixed sidebar width
TABLE_WIDTH = 160
TABLE_HEIGHT = 140

# ── Responsive breakpoints ─────────────────────────────────────────────────────
BREAKPOINT_SMALL  = 900
BREAKPOINT_MEDIUM = 1200
BREAKPOINT_LARGE = 1440

# ── Colours ────────────────────────────────────────────────────────────────────
DARK     = "#0F1117"
SURFACE  = "#1A1D27"
SURFACE2 = "#222536"
SURFACE3 = "#2A2E40"
BORDER   = "#363B52"
ACCENT   = "#FF6B35"
ACCENT2  = "#FFB347"
GREEN    = "#2ECC71"
BLUE     = "#3498DB"
RED      = "#E74C3C"
YELLOW   = "#F39C12"
TEXT     = "#E8EAF0"
TEXT2    = "#9BA3C0"
WHITE    = "#FFFFFF"

# BUG M FIX: STATUS_COLORS was used in table_manager / floor_view but never defined
# in constants — it was imported via `from utils.constants import *` so it must live here.
STATUS_COLORS = {
    "available":      GREEN,
    "occupied":       ACCENT,
    "reserved":       BLUE,
    "cleaning":       YELLOW,
    "out_of_service": RED,
}

ORDER_STATUS_COLORS = {
    "open":      TEXT2,
    "sent":      BLUE,
    "preparing": YELLOW,
    "ready":     GREEN,
    "served":    ACCENT2,
    "billed":    ACCENT,
    "paid":      GREEN,
    "cancelled": RED,
}

# BUG 6 FIX: PURPLE was used in reports_view charts but never defined
PURPLE = "#9B59B6"
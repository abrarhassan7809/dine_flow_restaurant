# 🍽 Restaurant Management System

A full-featured desktop application built with **Python + PySide6 (Qt6)**.

---

## 🚀 Quick Start

```bash
pip install PySide6
python main.py
```

---

## ✨ Features

### 🏠 Floor Plan
- Visual grid of all 12 tables with real-time status
- Color-coded: **Green** = Available, **Orange** = Occupied, **Blue** = Reserved, **Yellow** = Cleaning
- Click any table to open its order directly

### 📝 Order Management
- Full menu browser with category tabs (Starters, Mains, Desserts, Beverages, Specials)
- Add items with one click, adjust quantities
- Waiter name, order notes, and discount support
- Auto-calculated subtotal, 10% tax, and total
- **Save Draft** or **Send to Kitchen** actions

### 🍳 Kitchen Display System (KDS)
- Live 3-column Kanban board: New → Preparing → Ready
- Auto-refreshes every 10 seconds
- One-click status progression per order
- Special notes highlighted in yellow

### 🧾 Billing & Payment
- Auto-generated bill with itemized receipt
- Payment methods: Cash / Card / Mobile
- Change calculation for cash payments
- Marks table as "Cleaning" after payment

### 📊 Reports & Analytics
- Date-range filtering
- Revenue, orders, average order value, items sold summary cards
- Daily sales breakdown table
- Top-selling items ranking
- Full order history log

### 🍴 Menu Manager
- Add / edit menu items
- Toggle availability (e.g. 86 an item)
- Filter by category

### 🪑 Table Manager
- Override table status (Available / Reserved / Cleaning)
- View current order per table

---

## 🗄 Database

SQLite database (`restaurant.db`) is created automatically on first run with:
- 12 pre-seeded tables (Tables 1–12)
- 21 sample menu items across 5 categories
- Full schema for orders, bills, and sales history

---

## 🗂 File Structure

```
restaurant_management/
├── main.py          # Entire application (single file)
├── restaurant.db    # Auto-created SQLite database
└── README.md
```

---

## 🎨 Tech Stack

| Layer | Technology |
|-------|-----------|
| GUI Framework | PySide6 (Qt 6) |
| Database | SQLite3 (stdlib) |
| Language | Python 3.9+ |
| Styling | Qt Stylesheets (dark theme) |
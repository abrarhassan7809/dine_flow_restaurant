import json
import sqlite3
from pathlib import Path
from datetime import datetime
from utils.constants import DB_PATH


def get_db():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with tables only - no default data"""
    conn = get_db()
    c = conn.cursor()

    # Create tables if they don't exist
    c.executescript("""
                    -- Tables
                    CREATE TABLE IF NOT EXISTS tables (
                                                          id INTEGER PRIMARY KEY,
                                                          number INTEGER UNIQUE NOT NULL,
                                                          capacity INTEGER DEFAULT 4,
                                                          status TEXT DEFAULT 'available',
                                                          x_position INTEGER DEFAULT 0,
                                                          y_position INTEGER DEFAULT 0,
                                                          shape TEXT DEFAULT 'rectangle',
                                                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Menu categories
                    CREATE TABLE IF NOT EXISTS menu_categories (
                                                                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                   name TEXT NOT NULL,
                                                                   description TEXT,
                                                                   sort_order INTEGER DEFAULT 0,
                                                                   is_active INTEGER DEFAULT 1,
                                                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Menu items
                    CREATE TABLE IF NOT EXISTS menu_items (
                                                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                              category_id INTEGER REFERENCES menu_categories(id),
                        name TEXT NOT NULL,
                        description TEXT,
                        price REAL NOT NULL,
                        cost REAL DEFAULT 0,
                        is_available INTEGER DEFAULT 1,
                        prep_time INTEGER DEFAULT 10,
                        image_path TEXT,
                        allergens TEXT,
                        nutritional_info TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );

                    -- Orders
                    CREATE TABLE IF NOT EXISTS orders (
                                                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                          table_id INTEGER REFERENCES tables(id),
                        customer_name TEXT,
                        customer_phone TEXT,
                        customer_email TEXT,
                        customer_count INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'open',
                        waiter TEXT DEFAULT '',
                        notes TEXT DEFAULT '',
                        subtotal REAL DEFAULT 0,
                        tax REAL DEFAULT 0,
                        discount_type TEXT DEFAULT 'fixed',
                        discount_value REAL DEFAULT 0,
                        discount REAL DEFAULT 0,
                        service_charge REAL DEFAULT 0,
                        total REAL DEFAULT 0,
                        is_takeaway INTEGER DEFAULT 0,
                        delivery_address TEXT,
                        estimated_prep_time INTEGER DEFAULT 0,
                        actual_prep_time INTEGER DEFAULT 0,
                        created_by INTEGER REFERENCES staff(id),
                        updated_by INTEGER REFERENCES staff(id)
                        );

                    -- Order items
                    CREATE TABLE IF NOT EXISTS order_items (
                                                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                               order_id INTEGER REFERENCES orders(id),
                        menu_item_id INTEGER REFERENCES menu_items(id),
                        quantity INTEGER DEFAULT 1,
                        unit_price REAL NOT NULL,
                        notes TEXT DEFAULT '',
                        status TEXT DEFAULT 'pending',
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        modifier_groups TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );

                    -- Modifier groups (for customizable items)
                    CREATE TABLE IF NOT EXISTS modifier_groups (
                                                                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                   name TEXT NOT NULL,
                                                                   min_selections INTEGER DEFAULT 0,
                                                                   max_selections INTEGER DEFAULT 1,
                                                                   is_required INTEGER DEFAULT 0
                    );

                    -- Modifiers
                    CREATE TABLE IF NOT EXISTS modifiers (
                                                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                             group_id INTEGER REFERENCES modifier_groups(id),
                        name TEXT NOT NULL,
                        price_adjustment REAL DEFAULT 0,
                        is_default INTEGER DEFAULT 0
                        );

                    -- Item modifiers (link menu items to modifier groups)
                    CREATE TABLE IF NOT EXISTS item_modifiers (
                                                                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                  menu_item_id INTEGER REFERENCES menu_items(id),
                        modifier_group_id INTEGER REFERENCES modifier_groups(id)
                        );

                    -- Bills
                    CREATE TABLE IF NOT EXISTS bills (
                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         order_id INTEGER REFERENCES orders(id),
                        bill_number TEXT UNIQUE,
                        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        payment_method TEXT DEFAULT 'cash',
                        amount_paid REAL DEFAULT 0,
                        change_given REAL DEFAULT 0,
                        tip_amount REAL DEFAULT 0,
                        is_paid INTEGER DEFAULT 0,
                        payment_reference TEXT,
                        printed INTEGER DEFAULT 0,
                        created_by INTEGER REFERENCES staff(id)
                        );

                    -- Inventory
                    CREATE TABLE IF NOT EXISTS inventory (
                                                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                             menu_item_id INTEGER REFERENCES menu_items(id),
                        quantity REAL DEFAULT 0,
                        unit TEXT DEFAULT 'pcs',
                        reorder_level REAL DEFAULT 10,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by INTEGER REFERENCES staff(id)
                        );

                    -- Staff
                    CREATE TABLE IF NOT EXISTS staff (
                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         name TEXT NOT NULL,
                                                         role TEXT DEFAULT 'waiter',
                                                         pin_code TEXT,
                                                         email TEXT,
                                                         phone TEXT,
                                                         is_active INTEGER DEFAULT 1,
                                                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                         created_by INTEGER REFERENCES staff(id)
                        );

                    -- Shift management
                    CREATE TABLE IF NOT EXISTS shifts (
                                                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                          staff_id INTEGER REFERENCES staff(id),
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        cash_float REAL DEFAULT 0,
                        cash_sales REAL DEFAULT 0,
                        card_sales REAL DEFAULT 0,
                        total_sales REAL DEFAULT 0
                        );

                    -- Reservations
                    CREATE TABLE IF NOT EXISTS reservations (
                                                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                table_id INTEGER REFERENCES tables(id),
                        customer_name TEXT NOT NULL,
                        customer_phone TEXT,
                        customer_email TEXT,
                        party_size INTEGER DEFAULT 2,
                        reservation_time TIMESTAMP NOT NULL,
                        duration INTEGER DEFAULT 120,
                        status TEXT DEFAULT 'confirmed',
                        special_requests TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by INTEGER REFERENCES staff(id),
                        updated_by INTEGER REFERENCES staff(id)
                        );

                    -- Enhanced Audit log for tracking all user actions
                    CREATE TABLE IF NOT EXISTS audit_log (
                                                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                             user_id INTEGER REFERENCES staff(id),
                        user_name TEXT,
                        user_role TEXT,
                        action TEXT NOT NULL,  -- INSERT, UPDATE, DELETE, LOGIN, LOGOUT
                        table_name TEXT NOT NULL,
                        record_id INTEGER,
                        old_value TEXT,
                        new_value TEXT,
                        ip_address TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );

                    -- Login history
                    CREATE TABLE IF NOT EXISTS login_history (
                                                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                 user_id INTEGER REFERENCES staff(id),
                        user_name TEXT,
                        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        logout_time TIMESTAMP,
                        ip_address TEXT
                        );

                    -- Indexes for performance
                    CREATE INDEX IF NOT EXISTS idx_orders_table ON orders(table_id, status);
                    CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(created_at);
                    CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
                    CREATE INDEX IF NOT EXISTS idx_reservations_time ON reservations(reservation_time);
                    CREATE INDEX IF NOT EXISTS idx_reservations_table ON reservations(table_id);
                    CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, timestamp);
                    CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name, action);
                    """)

    # Check if we need to add position columns to existing tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tables'")
    if c.fetchone():
        c.execute("PRAGMA table_info(tables)")
        columns = [column[1] for column in c.fetchall()]

        if 'x_position' not in columns:
            try:
                c.execute("ALTER TABLE tables ADD COLUMN x_position INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
        if 'y_position' not in columns:
            try:
                c.execute("ALTER TABLE tables ADD COLUMN y_position INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
        if 'shape' not in columns:
            try:
                c.execute("ALTER TABLE tables ADD COLUMN shape TEXT DEFAULT 'rectangle'")
            except sqlite3.OperationalError:
                pass

    # Check staff table columns
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='staff'")
    if c.fetchone():
        c.execute("PRAGMA table_info(staff)")
        columns = [column[1] for column in c.fetchall()]

        if 'email' not in columns:
            try:
                c.execute("ALTER TABLE staff ADD COLUMN email TEXT")
            except sqlite3.OperationalError:
                pass

        if 'phone' not in columns:
            try:
                c.execute("ALTER TABLE staff ADD COLUMN phone TEXT")
            except sqlite3.OperationalError:
                pass

        if 'created_by' not in columns:
            try:
                c.execute("ALTER TABLE staff ADD COLUMN created_by INTEGER REFERENCES staff(id)")
            except sqlite3.OperationalError:
                pass

    # Create default admin if none exists
    c.execute("SELECT COUNT(*) FROM staff WHERE role = 'admin'")
    if c.fetchone()[0] == 0:
        # Create default admin user
        default_admin = {
            'name': 'Administrator',
            'role': 'admin',
            'pin_code': '1234',
            'email': 'admin@restaurant.com',
            'phone': '555-0001',
            'is_active': 1
        }

        c.execute("""
                  INSERT INTO staff (name, role, pin_code, email, phone, is_active)
                  VALUES (?, ?, ?, ?, ?, ?)
                  """, (
                      default_admin['name'],
                      default_admin['role'],
                      default_admin['pin_code'],
                      default_admin['email'],
                      default_admin['phone'],
                      default_admin['is_active']
                  ))

        admin_id = c.lastrowid

        # Log admin creation
        c.execute("""
                  INSERT INTO audit_log (user_id, user_name, user_role, action, table_name, record_id, new_value)
                  VALUES (?, ?, ?, ?, ?, ?, ?)
                  """, (
                      admin_id,
                      default_admin['name'],
                      'admin',
                      'CREATE',
                      'staff',
                      admin_id,
                      json.dumps(default_admin)
                  ))

        print("✅ Default admin user created with PIN: 1234")

    conn.commit()
    conn.close()
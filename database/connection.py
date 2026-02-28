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
    """Initialize database with tables and seed data"""
    conn = get_db()
    c = conn.cursor()

    # First, create tables if they don't exist (this will create the schema properly)
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
                        actual_prep_time INTEGER DEFAULT 0
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
                        printed INTEGER DEFAULT 0
                        );

                    -- Inventory
                    CREATE TABLE IF NOT EXISTS inventory (
                                                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                             menu_item_id INTEGER REFERENCES menu_items(id),
                        quantity REAL DEFAULT 0,
                        unit TEXT DEFAULT 'pcs',
                        reorder_level REAL DEFAULT 10,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );

                    -- Staff
                    CREATE TABLE IF NOT EXISTS staff (
                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         name TEXT NOT NULL,
                                                         role TEXT DEFAULT 'waiter',
                                                         pin_code TEXT,
                                                         is_active INTEGER DEFAULT 1,
                                                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );

                    -- Audit log
                    CREATE TABLE IF NOT EXISTS audit_log (
                                                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                             user TEXT,
                                                             action TEXT,
                                                             table_name TEXT,
                                                             record_id INTEGER,
                                                             old_value TEXT,
                                                             new_value TEXT,
                                                             timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Indexes for performance
                    CREATE INDEX IF NOT EXISTS idx_orders_table ON orders(table_id, status);
                    CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(created_at);
                    CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
                    CREATE INDEX IF NOT EXISTS idx_reservations_time ON reservations(reservation_time);
                    CREATE INDEX IF NOT EXISTS idx_reservations_table ON reservations(table_id);
                    """)

    # Check if we need to add position columns to existing tables
    # First, check if tables table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tables'")
    if c.fetchone():
        # Get existing columns
        c.execute("PRAGMA table_info(tables)")
        columns = [column[1] for column in c.fetchall()]

        # Add missing columns one by one (only those with constant defaults)
        if 'x_position' not in columns:
            try:
                c.execute("ALTER TABLE tables ADD COLUMN x_position INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column might already exist
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

        # Note: We cannot add created_at and updated_at with CURRENT_TIMESTAMP default
        # So we'll rely on the CREATE TABLE statement to handle these for new tables
        # For existing tables, these columns won't be added

    # Update existing tables with positions if needed
    try:
        # Check if tables have x_position values
        c.execute("SELECT COUNT(*) FROM tables WHERE x_position = 0 AND y_position = 0")
        count = c.fetchone()[0]

        if count > 0:
            # Update table positions
            for i in range(1, 21):
                row = (i - 1) // 4
                col = (i - 1) % 4
                x_pos = col * 180 + 20
                y_pos = row * 160 + 20
                capacity = 4 if i <= 16 else 6
                shape = 'rectangle' if i <= 16 else 'circle'
                c.execute("""
                          UPDATE tables
                          SET x_position = ?,
                              y_position = ?,
                              capacity   = ?,
                              shape      = ?
                          WHERE number = ?
                          """, (x_pos, y_pos, capacity, shape, i))
    except sqlite3.OperationalError:
        # Tables might not have the columns yet, skip for now
        pass

    # Seed tables 1-20 if they don't exist
    for i in range(1, 4):
        c.execute("SELECT COUNT(*) FROM tables WHERE number = ?", (i,))
        if c.fetchone()[0] == 0:
            row = (i - 1) // 4
            col = (i - 1) % 4
            x_pos = col * 180 + 20
            y_pos = row * 160 + 20
            capacity = 4 if i <= 16 else 6
            shape = 'rectangle' if i <= 16 else 'circle'
            c.execute("""
                      INSERT INTO tables
                          (number, capacity, x_position, y_position, shape)
                      VALUES (?, ?, ?, ?, ?)
                      """, (i, capacity, x_pos, y_pos, shape))

    # Seed categories if they don't exist
    categories = [
        ("Starters", "Appetizers and small plates", 1),
        ("Main Course", "Signature main dishes", 2),
        ("Desserts", "Sweet treats", 3),
        ("Beverages", "Drinks and refreshments", 4),
        ("Specials", "Chef's specials", 5),
        ("Breakfast", "Morning favorites", 6),
        ("Kids Menu", "Meals for children", 7)
    ]

    for name, desc, order in categories:
        c.execute("SELECT COUNT(*) FROM menu_categories WHERE name = ?", (name,))
        if c.fetchone()[0] == 0:
            c.execute("""
                      INSERT INTO menu_categories (name, description, sort_order)
                      VALUES (?, ?, ?)
                      """, (name, desc, order))

    # Seed menu items with costs if none exist
    menu_items = [
        # Starters
        (1, "Bruschetta", "Toasted bread with tomatoes, basil, and balsamic glaze", 8.50, 3.20, 8),
        (1, "Soup of the Day", "Chef's daily soup creation", 7.00, 2.50, 10),
        (1, "Calamari Fritti", "Crispy fried squid rings with marinara sauce", 12.50, 5.00, 12),
        (1, "Caesar Salad", "Romaine lettuce, croutons, parmesan, house dressing", 10.00, 3.80, 8),
        (1, "Garlic Bread", "Toasted baguette with garlic butter and herbs", 5.50, 1.80, 6),
        (1, "Stuffed Mushrooms", "Mushrooms stuffed with cream cheese and herbs", 9.50, 3.50, 12),

        # Main Course
        (2, "Grilled Salmon", "Atlantic salmon with lemon butter sauce and vegetables", 24.00, 9.50, 20),
        (2, "Chicken Alfredo", "Fettuccine pasta with grilled chicken in cream sauce", 19.50, 6.80, 18),
        (2, "Beef Tenderloin", "8oz tenderloin steak with truffle mash and red wine jus", 38.00, 16.00, 25),
        (2, "Margherita Pizza", "San Marzano tomato sauce, fresh mozzarella, basil", 15.00, 4.50, 15),
        (2, "Mushroom Risotto", "Creamy arborio rice with mixed mushrooms and parmesan", 18.00, 6.00, 22),
        (2, "Fish & Chips", "Beer-battered cod with hand-cut fries and tartar sauce", 18.50, 6.50, 18),
        (2, "Vegetable Curry", "Seasonal vegetables in coconut curry with rice", 16.00, 5.20, 20),
        (2, "BBQ Ribs", "Slow-cooked pork ribs with BBQ sauce and coleslaw", 26.00, 9.80, 30),

        # Desserts
        (3, "Tiramisu", "Classic Italian dessert with coffee and mascarpone", 9.00, 3.00, 5),
        (3, "Crème Brûlée", "Vanilla custard with caramelized sugar crust", 8.50, 2.80, 5),
        (3, "Chocolate Lava Cake", "Warm chocolate cake with molten center, vanilla ice cream", 10.50, 3.50, 12),
        (3, "Cheesecake", "New York style cheesecake with berry compote", 8.00, 2.60, 5),
        (3, "Ice Cream Selection", "Three scoops of premium ice cream", 7.00, 1.80, 3),

        # Beverages
        (4, "Still Water", "500ml bottled still water", 3.00, 0.50, 2),
        (4, "Sparkling Water", "500ml bottled sparkling water", 3.00, 0.50, 2),
        (4, "Soft Drink", "Coca-Cola, Diet Coke, Sprite, Fanta", 4.00, 0.80, 2),
        (4, "Fresh Orange Juice", "Freshly squeezed orange juice", 5.50, 1.80, 5),
        (4, "Coffee", "Espresso, Americano, Latte, Cappuccino", 4.50, 0.80, 5),
        (4, "Tea", "Selection of premium teas", 4.00, 0.60, 4),
        (4, "House Wine", "Glass of house red or white wine", 7.00, 3.00, 2),
        (4, "Craft Beer", "Local craft beer selection", 6.50, 2.50, 2),
        (4, "Cocktail of the Day", "Signature cocktail creation", 10.00, 3.50, 5),

        # Specials
        (5, "Chef's Tasting Menu", "5-course tasting experience with wine pairing", 75.00, 25.00, 45),
        (5, "Sunday Roast", "Traditional roast with all the trimmings", 26.00, 9.00, 30),
        (5, "Lobster Thermidor", "Half lobster in creamy cheese sauce", 45.00, 18.00, 35),

        # Breakfast
        (6, "Full English Breakfast", "Eggs, bacon, sausage, beans, toast, mushrooms, tomatoes", 15.00, 5.50, 15),
        (6, "Pancakes", "Fluffy pancakes with maple syrup and berries", 11.00, 3.50, 10),
        (6, "Avocado Toast", "Sourdough toast with avocado, poached eggs", 12.50, 4.20, 10),
        (6, "Breakfast Burrito", "Eggs, bacon, cheese, potatoes in tortilla", 13.00, 4.80, 12),

        # Kids Menu
        (7, "Kids Pizza", "Small pizza with cheese and tomato", 8.50, 2.50, 10),
        (7, "Chicken Nuggets", "With fries and vegetables", 8.00, 2.80, 10),
        (7, "Mac & Cheese", "Creamy macaroni and cheese", 7.50, 2.20, 8),
        (7, "Kids Ice Cream", "One scoop with sprinkles", 4.00, 0.80, 2)
    ]

    c.execute("SELECT COUNT(*) FROM menu_items")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO menu_items (category_id, name, description, price, cost, prep_time) VALUES (?,?,?,?,?,?)",
            menu_items
        )

    # Seed staff if none exist
    staff_data = [
        ("John Smith", "manager", "1234"),
        ("Sarah Johnson", "waiter", "2345"),
        ("Mike Williams", "waiter", "3456"),
        ("Emma Brown", "waiter", "4567"),
        ("David Lee", "chef", "5678"),
        ("Lisa Anderson", "cashier", "6789")
    ]

    c.execute("SELECT COUNT(*) FROM staff")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO staff (name, role, pin_code) VALUES (?,?,?)",
            staff_data
        )

    conn.commit()
    conn.close()
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from database.connection import get_db


@dataclass
class Table:
    id: int
    number: int
    capacity: int
    status: str
    x_position: int
    y_position: int
    shape: str
    created_at: str
    updated_at: str

    @classmethod
    def get_by_id(cls, table_id: int) -> Optional['Table']:
        conn = get_db()
        row = conn.execute("SELECT * FROM tables WHERE id = ?", (table_id,)).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None

    @classmethod
    def get_all(cls) -> List['Table']:
        conn = get_db()
        rows = conn.execute("SELECT * FROM tables ORDER BY number").fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    def update_status(self, status: str) -> bool:
        conn = get_db()
        conn.execute(
            "UPDATE tables SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, self.id)
        )
        conn.commit()
        conn.close()
        return True


@dataclass
class MenuItem:
    id: int
    category_id: int
    name: str
    description: str
    price: float
    cost: float
    is_available: bool
    prep_time: int
    image_path: Optional[str]
    allergens: Optional[str]
    nutritional_info: Optional[str]
    created_at: str = None
    updated_at: str = None

    @classmethod
    def get_by_id(cls, item_id: int) -> Optional['MenuItem']:
        conn = get_db()
        row = conn.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,)).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None

    @classmethod
    def get_by_category(cls, category_id: int) -> List['MenuItem']:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM menu_items WHERE category_id = ? AND is_available = 1 ORDER BY name",
            (category_id,)
        ).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]


@dataclass
class Order:
    id: int
    table_id: int
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    customer_count: int
    created_at: str
    updated_at: str
    status: str
    waiter: str
    notes: str
    subtotal: float
    tax: float
    discount_type: str
    discount_value: float
    discount: float
    service_charge: float
    total: float
    is_takeaway: bool
    delivery_address: Optional[str]
    estimated_prep_time: int
    actual_prep_time: int

    @classmethod
    def create(cls, table_id: int, waiter: str = "", customer_count: int = 1) -> 'Order':
        conn = get_db()
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""
                  INSERT INTO orders (table_id, waiter, customer_count, created_at, updated_at)
                  VALUES (?, ?, ?, ?, ?)
                  """, (table_id, waiter, customer_count, now, now))

        order_id = c.lastrowid
        conn.commit()
        conn.close()

        return cls.get_by_id(order_id)

    @classmethod
    def get_by_id(cls, order_id: int) -> Optional['Order']:
        conn = get_db()
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None

    @classmethod
    def get_active_for_table(cls, table_id: int) -> Optional['Order']:
        conn = get_db()
        row = conn.execute("""
                           SELECT *
                           FROM orders
                           WHERE table_id = ?
                             AND status NOT IN ('paid', 'cancelled')
                           ORDER BY id DESC LIMIT 1
                           """, (table_id,)).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None

    def get_items(self) -> List[Dict]:
        conn = get_db()
        rows = conn.execute("""
                            SELECT oi.*, mi.name, mi.description, mi.prep_time
                            FROM order_items oi
                                     JOIN menu_items mi ON oi.menu_item_id = mi.id
                            WHERE oi.order_id = ?
                            ORDER BY oi.id
                            """, (self.id,)).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def calculate_totals(self) -> Dict[str, float]:
        items = self.get_items()
        subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
        tax = subtotal * 0.10  # 10% tax

        if self.discount_type == 'percentage':
            discount = subtotal * (self.discount_value / 100)
        else:
            discount = self.discount_value

        service_charge = subtotal * 0.05  # 5% service charge
        total = subtotal + tax + service_charge - discount

        return {
            'subtotal': round(subtotal, 2),
            'tax': round(tax, 2),
            'discount': round(discount, 2),
            'service_charge': round(service_charge, 2),
            'total': round(total, 2)
        }

    def update_status(self, status: str) -> bool:
        conn = get_db()
        conn.execute("""
                     UPDATE orders
                     SET status     = ?,
                         updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?
                     """, (status, self.id))
        conn.commit()
        conn.close()
        return True


@dataclass
class OrderItem:
    id: int
    order_id: int
    menu_item_id: int
    quantity: int
    unit_price: float
    notes: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    modifier_groups: Optional[str]
    created_at: str

    @classmethod
    def get_by_order(cls, order_id: int) -> List['OrderItem']:
        conn = get_db()
        rows = conn.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (order_id,)).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    def to_dict(self) -> Dict:
        data = {k: v for k, v in self.__dict__.items()}
        if self.modifier_groups:
            data['modifier_groups'] = json.loads(self.modifier_groups)
        return data


@dataclass
class Bill:
    id: int
    order_id: int
    bill_number: str
    generated_at: str
    payment_method: str
    amount_paid: float
    change_given: float
    tip_amount: float
    is_paid: bool
    payment_reference: Optional[str]
    printed: bool

    @classmethod
    def generate(cls, order_id: int, payment_method: str = "cash",
                 amount_paid: float = 0, tip: float = 0) -> 'Bill':
        conn = get_db()
        order = Order.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        totals = order.calculate_totals()
        change = max(amount_paid - totals['total'], 0)

        # Generate unique bill number
        date_str = datetime.now().strftime("%Y%m%d")

        # Use a transaction to ensure uniqueness
        conn.execute("BEGIN IMMEDIATE")

        try:
            # Get the last bill number for today
            result = conn.execute(
                "SELECT bill_number FROM bills WHERE bill_number LIKE ? ORDER BY bill_number DESC LIMIT 1",
                (f"B{date_str}%",)
            ).fetchone()

            if result:
                # Extract the sequence number and increment
                last_number = result[0]
                seq_num = int(last_number[-4:]) + 1
            else:
                seq_num = 1

            bill_number = f"B{date_str}{seq_num:04d}"

            # Insert the bill
            c = conn.cursor()
            c.execute("""
                      INSERT INTO bills (order_id, bill_number, payment_method, amount_paid,
                                         change_given, tip_amount, is_paid)
                      VALUES (?, ?, ?, ?, ?, ?, 1)
                      """, (order_id, bill_number, payment_method, amount_paid, change, tip))

            bill_id = c.lastrowid

            # Update order status
            conn.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (order_id,))

            # Update table status
            if not order.is_takeaway:
                conn.execute("""
                             UPDATE tables
                             SET status = 'cleaning'
                             WHERE id = (SELECT table_id FROM orders WHERE id = ?)
                             """, (order_id,))

            conn.commit()
            conn.close()

            return cls.get_by_id(bill_id)

        except Exception as e:
            conn.rollback()
            conn.close()
            raise e

    @classmethod
    def get_by_id(cls, bill_id: int) -> Optional['Bill']:
        conn = get_db()
        row = conn.execute("SELECT * FROM bills WHERE id = ?", (bill_id,)).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None

    @classmethod
    def get_by_order(cls, order_id: int) -> Optional['Bill']:
        conn = get_db()
        row = conn.execute("SELECT * FROM bills WHERE order_id = ? ORDER BY id DESC LIMIT 1", (order_id,)).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None


@dataclass
class MenuCategory:
    id: int
    name: str
    description: Optional[str]
    sort_order: int
    is_active: bool
    created_at: str

    @classmethod
    def get_all_active(cls) -> List['MenuCategory']:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM menu_categories WHERE is_active = 1 ORDER BY sort_order"
        ).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_id(cls, category_id: int) -> Optional['MenuCategory']:
        conn = get_db()
        row = conn.execute("SELECT * FROM menu_categories WHERE id = ?", (category_id,)).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None


@dataclass
class Staff:
    id: int
    name: str
    role: str
    pin_code: str
    is_active: bool
    created_at: str

    @classmethod
    def get_all_active(cls) -> List['Staff']:
        conn = get_db()
        rows = conn.execute("SELECT * FROM staff WHERE is_active = 1 ORDER BY name").fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_pin(cls, pin_code: str) -> Optional['Staff']:
        conn = get_db()
        row = conn.execute("SELECT * FROM staff WHERE pin_code = ? AND is_active = 1", (pin_code,)).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None


@dataclass
class Reservation:
    id: int
    table_id: Optional[int]
    customer_name: str
    customer_phone: Optional[str]
    customer_email: Optional[str]
    party_size: int
    reservation_time: str
    duration: int
    status: str
    special_requests: Optional[str]
    created_at: str

    @classmethod
    def get_by_date(cls, date: str) -> List['Reservation']:
        conn = get_db()
        rows = conn.execute("""
                            SELECT *
                            FROM reservations
                            WHERE DATE (reservation_time) = DATE (?)
                            ORDER BY reservation_time
                            """, (date,)).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def create(cls, **kwargs) -> 'Reservation':
        conn = get_db()
        c = conn.cursor()

        fields = ', '.join(kwargs.keys())
        placeholders = ', '.join(['?' for _ in kwargs])
        values = list(kwargs.values())

        c.execute(f"""
            INSERT INTO reservations ({fields}, created_at)
            VALUES ({placeholders}, CURRENT_TIMESTAMP)
        """, values)

        reservation_id = c.lastrowid
        conn.commit()
        conn.close()

        return cls.get_by_id(reservation_id)

    @classmethod
    def get_by_id(cls, reservation_id: int) -> Optional['Reservation']:
        conn = get_db()
        row = conn.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,)).fetchone()
        conn.close()
        return cls(**dict(row)) if row else None

    def update_status(self, status: str) -> bool:
        conn = get_db()
        conn.execute("UPDATE reservations SET status = ? WHERE id = ?", (status, self.id))
        conn.commit()
        conn.close()
        return True
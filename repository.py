"""SQLite persistence. Contains deliberate reliability/security problems."""
import sqlite3
from models import Product
from decimal import Decimal
from contextlib import closing



class StoreRepository:
    def __init__(self, db_path='shop.db'):
        self.db_path = db_path



    def connect(self):
        return sqlite3.connect(self.db_path, timeout=5)



    def get_product(self, sku):
        with closing(self.connect()) as conn:
            with conn:
                row = conn.execute(
                    """
                    SELECT sku, name, price, stock 
                    FROM products 
                    WHERE sku = ?
                    """,
                    (sku,)
                ).fetchone()

        if row is None:
            return None

        return Product(
            sku=row[0],
            name=row[1],
            price=Decimal(str(row[2])),
            stock=row[3]
        )



    def get_saved_cart(self, user_id):
        with closing(self.connect()) as conn:
            with conn:
                rows = conn.execute(
                    """
                    SELECT sku, quantity 
                    FROM saved_cart 
                    WHERE user_id = ?
                    """,
                    (user_id,)
                ).fetchall()
        
        return rows



    def save_cart(self, user_id, lines):
        with closing(self.connect()) as conn:
            with conn:
                conn.execute(
                    """
                    DELETE FROM saved_cart 
                    WHERE user_id = ?
                    """,
                    (user_id,)
                )
                conn.executemany(
                    """
                    INSERT INTO saved_cart (user_id, sku, quantity) 
                    VALUES (?, ?, ?)
                    """,
                    [(user_id, line.sku, line.quantity) for line in lines]
                )



    def update_stock(self, sku, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            return False

        with closing(self.connect()) as conn:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE products
                    SET stock = stock - ?
                    WHERE sku = ? AND stock >= ?
                    """,
                    (quantity, sku, quantity)
                )

        return cursor.rowcount == 1


    
    def restore_stock(self, sku, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            return False

        with closing(self.connect()) as conn:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE products
                    SET stock = stock + ?
                    WHERE sku = ?
                    """,
                    (quantity, sku)
                )

        return cursor.rowcount == 1

        

    def save_order(self, user_id, amount, status, request_id):
        with closing(self.connect()) as conn:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO orders
                    (user_id, amount, status, request_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, str(amount), status, request_id)
                )

        return cursor.lastrowid



    def get_order_by_request(self, user_id, request_id):
        with closing(self.connect()) as conn:
            with conn:
                row = conn.execute(
                    """
                    SELECT id, user_id, amount, status
                    FROM orders 
                    WHERE user_id = ? AND request_id = ?
                    """,
                    (user_id, request_id)
                ).fetchone()

        if row is None:
            return None
        
        return (
            row[0],
            row[1],
            Decimal(str(row[2])),
            row[3]
        )



    def list_orders(self, user_id):
        with closing(self.connect()) as conn:
            with conn:
                rows = conn.execute(
                    """
                    SELECT id, user_id, amount, status 
                    FROM orders 
                    WHERE user_id = ?
                    ORDER BY id DESC
                    """,
                    (user_id,)
                ).fetchall()
        
        return [
            (
                row[0],
                row[1],
                Decimal(str(row[2])),
                row[3]
            ) for row in rows
        ]

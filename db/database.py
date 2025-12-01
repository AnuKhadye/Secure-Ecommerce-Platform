import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash


class Database:
    def __init__(self, db_path='database.db', schema_path=None):
        self.db_path = db_path

        # Resolve schema.sql relative to this file if not explicitly given
        if schema_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.schema_path = os.path.join(base_dir, 'schema.sql')
        else:
            self.schema_path = schema_path

        # Ensure DB file exists (sqlite will create it on first connect anyway)
        if not os.path.exists(self.db_path):
            print("Database not found. Creating a new one...")

        # Always run schema to ensure all tables exist (CREATE TABLE IF NOT EXISTS is safe)
        self.initialize_database()

        # Then ensure extra columns for new features
        try:
            self.ensure_schema_enhancements()
        except Exception as e:
            print("Schema enhancement warning:", e)

    # -------------------------------------------------
    # CORE DB HELPERS
    # -------------------------------------------------
    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self):
        """Run schema.sql to create any missing tables."""
        try:
            conn = self.connect()
            with open(self.schema_path, encoding='utf-8') as f:
                sql = f.read()
            conn.executescript(sql)
            conn.commit()
            print("Database schema applied successfully.")
        except Exception as e:
            print(f"Error initializing database: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def list_tables(self):
        with self.connect() as conn:
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        return [row['name'] for row in result]

    # -------------------------------------------------
    # PRODUCTS
    # -------------------------------------------------
    def add_product(self, name, price, description):
        with self.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
                (name, price, description)
            )
            conn.commit()
            return cursor.lastrowid

    def add_product_with_seller(self, name, price, description, seller_id, inventory=0):
        with self.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO products (name, price, description, seller_id, inventory) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, price, description, seller_id, inventory)
            )
            conn.commit()
            return cursor.lastrowid

    def get_product(self, product_id):
        with self.connect() as conn:
            product = conn.execute(
                "SELECT * FROM products WHERE id = ?",
                (product_id,)
            ).fetchone()
        return dict(product) if product else None

    def get_product_with_seller(self, product_id):
        with self.connect() as conn:
            product = conn.execute(
                "SELECT p.*, u.username AS seller_name "
                "FROM products p "
                "LEFT JOIN users u ON p.seller_id = u.id "
                "WHERE p.id = ?",
                (product_id,)
            ).fetchone()
        return dict(product) if product else None

    def get_all_products(self):
        with self.connect() as conn:
            products = conn.execute("SELECT * FROM products").fetchall()
        return [dict(row) for row in products]

    def edit_product(self, product_id, name=None, price=None, description=None, inventory=None):
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if price is not None:
            updates.append("price = ?")
            params.append(price)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if inventory is not None:
            updates.append("inventory = ?")
            params.append(inventory)

        if not updates:
            return False

        params.append(product_id)
        sql = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"

        with self.connect() as conn:
            conn.execute(sql, tuple(params))
            conn.commit()
        return True

    def delete_product(self, product_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
        return True

    # -------------------------------------------------
    # REVIEWS
    # -------------------------------------------------
    def add_review(self, user_id, product_id, content, rating=5, image_url=None):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO reviews (user_id, product_id, content, image_url, rating) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, product_id, content, image_url, rating)
            )
            conn.commit()
        return True

    def get_reviews_for_product(self, product_id):
        with self.connect() as conn:
            reviews = conn.execute(
                "SELECT r.content, r.image_url, r.rating, r.created_at, u.username "
                "FROM reviews r "
                "JOIN users u ON r.user_id = u.id "
                "WHERE r.product_id = ? "
                "ORDER BY r.created_at DESC",
                (product_id,)
            ).fetchall()
        return [dict(row) for row in reviews]

    # -------------------------------------------------
    # USERS
    # -------------------------------------------------
    def add_user(self, username, password, email, role='user'):
        hashed_pw = generate_password_hash(password)
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO users (username, password, email, role) "
                    "VALUES (?, ?, ?, ?)",
                    (username, hashed_pw, email, role)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_users_info(self):
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM users").fetchall()
        return {row['username']: dict(row) for row in rows}

    def get_user_by_email(self, email):
        with self.connect() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()
        return dict(user) if user else None

    def get_user_by_id(self, user_id):
        with self.connect() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
        return dict(user) if user else None

    def validate_user(self, email, password):
        user = self.get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            return user
        return None

    def set_username(self, email, username):
        with self.connect() as conn:
            conn.execute(
                "UPDATE users SET username = ? WHERE email = ?",
                (username, email)
            )
            conn.commit()
        return True

    def show_all_users(self):
        with self.connect() as conn:
            users = conn.execute("SELECT username FROM users").fetchall()
        return [row["username"] for row in users]

    # -------------------------------------------------
    # CART
    # -------------------------------------------------
    def add_to_cart(self, user_id, product_id, quantity=1):
        if quantity <= 0:
            return False

        with self.connect() as conn:
            existing = conn.execute(
                "SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            ).fetchone()

            if existing:
                conn.execute(
                    "UPDATE cart_items "
                    "SET quantity = quantity + ? "
                    "WHERE user_id = ? AND product_id = ?",
                    (quantity, user_id, product_id)
                )
            else:
                conn.execute(
                    "INSERT INTO cart_items (user_id, product_id, quantity) "
                    "VALUES (?, ?, ?)",
                    (user_id, product_id, quantity)
                )
            conn.commit()
        return True

    def get_cart(self, user_id):
        with self.connect() as conn:
            items = conn.execute(
                """
                SELECT p.id, p.name, p.price, c.quantity
                FROM cart_items c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
                """,
                (user_id,)
            ).fetchall()
        return [dict(row) for row in items]

    def remove_from_cart(self, user_id, product_id):
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )
            conn.commit()
        return True

    # -------------------------------------------------
    # SCHEMA ENHANCEMENTS (COLUMNS)
    # -------------------------------------------------
    def ensure_column(self, table, column, definition):
        """Ensure a column exists; if not, add it via ALTER TABLE."""
        with self.connect() as conn:
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            col_names = [c['name'] for c in cols]
            if column not in col_names:
                try:
                    conn.execute(
                        f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                    )
                    conn.commit()
                    print(f"Added column {column} to {table}")
                except Exception as e:
                    print(f"Could not add column {column} to {table}: {e}")

    def ensure_schema_enhancements(self):
        """Add columns needed for new features without dropping data."""
        self.ensure_column('users', 'is_suspended', "INTEGER DEFAULT 0")
        self.ensure_column('users', 'role', "TEXT DEFAULT 'user'")
        self.ensure_column('products', 'seller_id', "INTEGER")
        self.ensure_column('products', 'inventory', "INTEGER DEFAULT 0")
        return True

    # -------------------------------------------------
    # ADMIN / USER MANAGEMENT
    # -------------------------------------------------
    def list_all_users(self):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, username, email, role, is_suspended, created_at FROM users"
            ).fetchall()
        return [dict(r) for r in rows]

    def suspend_user(self, user_id):
        with self.connect() as conn:
            conn.execute(
                "UPDATE users SET is_suspended = 1 WHERE id = ?",
                (user_id,)
            )
            conn.commit()
        return True

    def unsuspend_user(self, user_id):
        with self.connect() as conn:
            conn.execute(
                "UPDATE users SET is_suspended = 0 WHERE id = ?",
                (user_id,)
            )
            conn.commit()
        return True

    # -------------------------------------------------
    # INVENTORY / ORDERS
    # -------------------------------------------------
    def check_inventory(self, product_id):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT inventory FROM products WHERE id = ?",
                (product_id,)
            ).fetchone()
            if not row:
                return None
            return int(row['inventory'])

    def reduce_inventory(self, product_id, amount):
        with self.connect() as conn:
            conn.execute(
                "UPDATE products "
                "SET inventory = inventory - ? "
                "WHERE id = ? AND inventory >= ?",
                (amount, product_id, amount)
            )
            conn.commit()
            cur = conn.execute("SELECT changes() AS c").fetchone()
            return cur['c'] > 0

    def create_order(self, user_id, total):
        with self.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO orders (user_id, total) VALUES (?, ?)",
                (user_id, total)
            )
            conn.commit()
            return cursor.lastrowid

    def add_order_item(self, order_id, product_id, quantity, price):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) "
                "VALUES (?, ?, ?, ?)",
                (order_id, product_id, quantity, price)
            )
            conn.commit()
        return True

    def clear_cart_for_user(self, user_id):
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM cart_items WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
        return True

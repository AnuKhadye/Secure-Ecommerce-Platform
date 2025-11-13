import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self, db_path = 'database.db', schema_path = 'schema.sql'):
        self.db_path = db_path
        self.schema_path = schema_path

        if not os.path.exists(self.db_path):
            print("Database not found.\nCreating a new one...")
            self.initialize_database()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize_database(self):
        try:
            conn = self.connect()
            with open(self.schema_path) as f:
                conn.executescript(f.read())
            conn.commit()
            print("Database Initialised Sucessfully")
        except Exception as e:
            print(f"Error initializing database: {e}")

        finally:
            conn.close()


    def list_tables(self):
        with self.connect() as conn:
            result = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        return [row['name'] for row in result]



    # PRODUCTS section

    def add_product(self, name, price, description):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
                (name, price, description)
            )   
            conn.commit()
        print(f"Product {name} added.")


    def get_product(self, product_id):
        with self.connect() as conn:
            product = conn.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
        return dict(product) if product else None
    
    def get_all_products(self):
        with self.connect() as conn:
            products = conn.execute("SELECT * FROM products").fetchall()            
        return [dict(row) for row in products]
    
    
    # USER Section

    def add_user(self, username, password, email, role = 'user'):
        hashed_pw = generate_password_hash(password)
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                    (username, hashed_pw, email, role)
                )
                conn.commit()
            print(f"User created {username}")
        except sqlite3.IntegrityError as e:
            print(f"Error adding user: {e}")

    def get_users_info(self):
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM users").fetchall()
        
        # Convert each row to a dictionary
        users_dict = {row['username']: dict(row) for row in rows}
        return users_dict

    
    def get_user_by_email(self, email):
        with self.connect() as conn:
            user = conn.execute("SELECT * FROM users where email = ?", (email, )).fetchone()

        return dict(user) if user else None
    
    def validate_user(self, password, email):
        user = self.get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            return user
        return None

    def show_all_users(self):
        with self.connect() as conn:
            users = conn.execute(
                "SELECT username FROM users"
            ).fetchall()
        return [row["username"]for row in users ]
    

    # Cart Section

    def add_to_cart(self, user_id, product_id, quantity=1):
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT quantity from cart_items where user_id = ? AND product_id = ?",
                (user_id, product_id)
            ).fetchone()

            if existing:
                conn.execute(
                    "UPDATE cart_items SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?",
                    (quantity, user_id, product_id)
                )
            else:
                conn.execute(
                    "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                    (user_id, product_id, quantity)
                )
        print(f"Added product {product_id} to user {user_id}'s cart")

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

        print(f"Removed product {product_id} from user {user_id}'s cart")


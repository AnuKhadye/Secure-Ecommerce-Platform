import sqlite3
import os

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
    
    def initialize_database(self, schema_path = 'db/schema.sql'):
        conn = self.connect()
        with open(schema_path) as f:
            conn.executescript(f.read())

        conn.commit()
        conn.close()
        print("Database Initialised Sucessfully")


    # PRODUCTS section

    def add_product(self, name, price, description):
        conn = self.connect()
        conn.execute(
            "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
            (name, price, description)
        )
        
        conn.commit()
        conn.close()
        print(f"Product {name} added.")


    def get_product(self, product_id):
        conn = self.connect()
        product = conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()

        conn.close()
        return dict(product) if product else None
    
    def get_all_products(self):
        conn = self.connect()
        products = conn.execute("SELECT * FROM products").fetchall()
        
        conn.close()
        return [dict(row) for row in products]
    
    # USER Section

    def add_user(self, username, password):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        print(f"User created {username}")


    def show_all_users(self):
        with self.connect() as conn:
            users = conn.execute(
                "SELECT username FROM users"
            ).fetchall()
            conn.commit()

        return [row["username"]for row in users ]


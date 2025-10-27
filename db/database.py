import sqlite3

class Database:
    def __init__(self, db_path = 'database.db'):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize_database(self, schema_path = 'schema.sql'):
        conn = self.connect()
        with open(schema_path) as f:
            conn.executescript(f.read())

        conn.commit()
        conn.close()
        print("Database Initialised Sucessfully")


    # PRODUCTS section

    def add_product(self, name, price):
        conn = self.connect()
        conn.execute(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            (name, price)
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
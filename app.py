from flask import Flask, render_template, request, redirect, url_for, session
from db.database import Database

app = Flask(__name__)
db = Database()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shop')
def shop():
    products = db.get_all_products()
    return render_template('shop.html', products = products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    user_id = session.get('user_id', 1)  # temp: use 1 until login system works
    db.add_to_cart(user_id, product_id)
    return redirect(url_for('shop'))

@app.route('/cart')
def cart():
    user_id = session.get('user_id', 1)
    items = db.get_cart(user_id)
    total = sum(item['price'] * item['quantity'] for item in items)
    return render_template('cart.html', cart=items, total=total)
    
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    user_id = session.get('user_id', 1)
    db.remove_from_cart(user_id, product_id)
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)

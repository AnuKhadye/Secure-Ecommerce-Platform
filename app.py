from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shop')
def shop():
    products = [
        {"id": 1, "name": "Product 1", "price": 19.99, "image": "/static/images/p1.png"},
        {"id": 2, "name": "Product 2", "price": 29.99, "image": "/static/images/p2.png"},
    ]
    return render_template('shop.html', products=products)

@app.route('/cart')
def cart():
    cart = [{"name": "Product 1", "quantity": 2, "price": 19.99}]
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

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

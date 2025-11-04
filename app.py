from flask import Flask, render_template, request, redirect, url_for, session, flash
from forms import RegisterForm, LoginForm
from db.database import Database

app = Flask(__name__)
app.secret_key = 'SecretKey'
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

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.validate_user(form.username.data, form.password.data)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login Sucessful", "sucess")
            return redirect(url_for('shop'))
        else:
            flash("Invalid username or password", "danger")
    return render_template('login.html', form=form)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = db.get_user_by_username(form.username.data)
        if existing_user:
            flash("Username already taken", "danger")
            return redirect(url_for('register'))
        db.add_user(form.username.data, form.password.data)
        flash("Registration sucessful. Please log In.", "sucess")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    session.clear(0)
    flash("You have been logged out.", "info")
    return render_template(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

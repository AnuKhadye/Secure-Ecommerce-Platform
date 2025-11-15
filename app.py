from flask import Flask, render_template, request, redirect, url_for, session, flash
from forms import RegisterForm, LoginForm, SetUserName
from db.database import Database
from functools import wraps

app = Flask(__name__)
app.secret_key = 'Replace_With_A_Strong_Random_Secret'  # change this before submission
db = Database()

# Helper: login required
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

# Routes
@app.route('/')
def home():
    return redirect(url_for('shop'))

@app.route('/shop')
def shop():
    products = db.get_all_products()
    return render_template('shop.html', products=products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user_id = session.get('user_id')
    product = db.get_product(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('shop'))

    success = db.add_to_cart(user_id, product_id, quantity=1)
    if success:
        flash('Item added to cart.', 'success')
    else:
        flash('Could not add item to cart.', 'danger')
    return redirect(url_for('shop'))

@app.route('/cart')
@login_required
def cart():
    user_id = session.get('user_id')
    items = db.get_cart(user_id)
    total = sum(item['price'] * item['quantity'] for item in items) if items else 0
    return render_template('cart.html', cart=items, total=total)

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    user_id = session.get('user_id')
    db.remove_from_cart(user_id, product_id)
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    user_id = session.get('user_id')
    items = db.get_cart(user_id)
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('shop'))
    total = sum(item['price'] * item['quantity'] for item in items)
    return render_template('checkout.html', total=total)

# Registration / Username
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        # Check duplicate
        existing = db.get_user_by_email(email)
        if existing:
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        db.add_user(username=None, password=form.password.data, email=email)
        session['pending_email'] = email
        flash('Registration successful — please choose a username.', 'success')
        return redirect(url_for('set_username'))

    return render_template('register.html', form=form)

@app.route('/set_username', methods=['GET', 'POST'])
def set_username():
    if 'pending_email' not in session:
        flash('Please register first.', 'warning')
        return redirect(url_for('register'))

    form = SetUserName()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = session.pop('pending_email', None)
        if not email:
            flash('Session expired. Please register again.', 'warning')
            return redirect(url_for('register'))
        try:
            db.set_username(email, username)
        except Exception as e:
            flash('Could not set username. Try a different one.', 'danger')
            return redirect(url_for('set_username'))

        flash('Username set. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('set_username.html', form=form)

# Login / Logout
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data

        user = db.validate_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user.get('username') or ''
            if not session['username']:
                flash('Please choose a username to continue.', 'info')
                session['pending_email'] = email
                session.pop('user_id', None)
                session.pop('username', None)
                return redirect(url_for('set_username'))

            flash('Login successful!', 'success')
            return redirect(url_for('shop'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Run
if __name__ == '__main__':
    app.run(debug=True)

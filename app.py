from flask import Flask, render_template, request, redirect, url_for, session, flash
from forms import RegisterForm, LoginForm, SetUserNameForm
from db.database import Database
from functools import wraps
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'SecretKey123'
app.permanent_session_lifetime = timedelta(minutes=30)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False  # True if HTTPS
)

db = Database()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('shop'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

@app.route('/')
def home():
    products = db.get_all_products()
    return render_template('shop.html', products=products)

@app.route('/shop')
def shop():
    products = db.get_all_products()
    return render_template('shop.html', products=products)

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    product = db.get_product(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for('shop'))

    reviews = db.get_reviews_for_product(product_id)

    if request.method == 'POST':
        if not session.get('user_id'):
            flash("You must be logged in to review.", "warning")
            return redirect(url_for('login'))
        comment = request.form.get('comment')
        rating = int(request.form.get('rating', 5))
        db.add_review(session['user_id'], product_id, comment, rating)
        flash("Review submitted!", "success")
        return redirect(url_for('product_detail', product_id=product_id))

    return render_template('product_detail.html', product=product, reviews=reviews)


@app.route('/cart')
@login_required
def cart():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in to view your cart.", "warning")
        return redirect(url_for('login'))

    items = db.get_cart(user_id)
    total = sum(item['price'] * item['quantity'] for item in items)
    return render_template('cart.html', cart=items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in to add items to the cart.", "warning")
        return redirect(url_for('login'))

    db.add_to_cart(user_id, product_id)
    flash("Product added to cart.", "success")
    return redirect(url_for('shop'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in to remove items from the cart.", "warning")
        return redirect(url_for('login'))

    db.remove_from_cart(user_id, product_id)
    flash("Product removed from cart.", "info")
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in to checkout.", "warning")
        return redirect(url_for('login'))

    items = db.get_cart(user_id)
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('shop'))

    total = sum(item['price'] * item['quantity'] for item in items)
    return render_template('checkout.html', total=total)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data

        if db.get_user_by_email(email):
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))

        session['pending_email'] = email
        session['pending_password'] = password
        return redirect(url_for('set_username'))

    return render_template('register.html', form=form)

@app.route('/set_username', methods=['GET', 'POST'])
def set_username():
    if 'pending_email' not in session or 'pending_password' not in session:
        flash("Register first!", "warning")
        return redirect(url_for('register'))

    form = SetUserNameForm()
    if form.validate_on_submit():
        username = form.username.data
        email = session.pop('pending_email')
        password = session.pop('pending_password')

        success = db.add_user(username, password, email)
        if success:
            flash("Registration complete! You can now log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Username already taken, try a different one.", "danger")
            return redirect(url_for('set_username'))

    return render_template('set_username.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        user = db.validate_user(email, password)

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login successful!", "success")
            return redirect(url_for('shop'))
        else:
            flash("Invalid email or password.", "danger")

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)

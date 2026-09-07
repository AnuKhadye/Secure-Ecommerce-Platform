from flask import Flask, render_template, request, redirect, url_for, session, flash
from forms import RegisterForm, LoginForm, SetUserNameForm
from db.database import Database
from functools import wraps
from datetime import timedelta
import os
import uuid
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

IS_DEVELOPMENT = os.environ.get("FLASK_ENV") == "development"

app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY is not set. Copy .env.example to .env and generate a value with:\n"
        '  python -c "import secrets; print(secrets.token_hex(32))"'
    )

app.permanent_session_lifetime = timedelta(minutes=30)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,      
    SESSION_COOKIE_SAMESITE='Lax',     
    SESSION_COOKIE_SECURE=not IS_DEVELOPMENT,  
)

# CSRF protection
csrf = CSRFProtect(app)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# --- DB ---
db = Database()
# ensure_schema_enhancements is called inside Database.__init__ after DB creation

# --- AUTH HELPERS ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in.", "warning")
            return redirect(url_for('login'))
        user = db.get_user_by_id(session['user_id'])
        if not user:
            session.clear()
            flash("User not found, please log in.", "warning")
            return redirect(url_for('login'))
        if user.get('is_suspended'):
            session.clear()
            flash("Account suspended. Contact admin.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    roles = [r.lower() for r in roles]
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            role = session.get('role', '').lower()
            if role not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('shop'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# --- ADMIN ROUTES ---
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    users = db.list_all_users()
    products = db.get_all_products()
    return render_template('admin_dashboard.html', users=users, products=products)

@app.route('/suspend_user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def suspend_user(user_id):
    if session['user_id'] == user_id:
        flash("You cannot suspend your own admin account.", "warning")
        return redirect(url_for('admin_dashboard'))
    db.suspend_user(user_id)
    flash("User suspended.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/unsuspend_user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def unsuspend_user(user_id):
    db.unsuspend_user(user_id)
    flash("User unsuspended.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = db.get_product_with_seller(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for('shop'))

    # owner or admin required
    role = session.get('role', '').lower()
    if role != 'admin' and product.get('seller_id') != session.get('user_id'):
        flash("You do not have permission to delete this product.", "danger")
        return redirect(url_for('product_detail', product_id=product_id))

    db.delete_product(product_id)
    flash("Product deleted.", "info")
    # send admin to admin dashboard, sellers to shop
    return redirect(url_for('admin_dashboard') if role == 'admin' else url_for('shop'))

# --- PRODUCT MANAGEMENT ---
@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    # allow any logged-in user to add product OR restrict via role_required('seller','admin')
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        try:
            price = float(request.form.get('price') or 0)
        except ValueError:
            price = 0.0
        description = request.form.get('description') or ''
        try:
            inventory = int(request.form.get('inventory') or 0)
        except ValueError:
            inventory = 0

        seller_id = session.get('user_id')
        db.add_product_with_seller(name, price, description, seller_id, inventory)
        flash("Product added.", "success")
        return redirect(url_for('shop'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = db.get_product_with_seller(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for('shop'))

    role = session.get('role', '').lower()
    if role != 'admin' and product.get('seller_id') != session.get('user_id'):
        flash("You do not have permission to edit this product.", "danger")
        return redirect(url_for('product_detail', product_id=product_id))

    if request.method == 'POST':
        name = request.form.get('name') or product.get('name')
        try:
            price = float(request.form.get('price') or product.get('price') or 0)
        except ValueError:
            price = product.get('price') or 0
        description = request.form.get('description') or product.get('description') or ''
        try:
            inventory = int(request.form.get('inventory') or product.get('inventory') or 0)
        except ValueError:
            inventory = product.get('inventory') or 0

        db.edit_product(product_id, name=name, price=price, description=description, inventory=inventory)
        flash("Product updated.", "success")
        return redirect(url_for('product_detail', product_id=product_id))

    return render_template('edit_product.html', product=product)

# --- SHOP / PRODUCT / REVIEWS ---
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
        if 'user_id' not in session:
            flash("You must be logged in to review.", "warning")
            return redirect(url_for('login'))

        content = request.form.get('content')
        rating = int(request.form.get('rating', 5))

        # image handling: for now, ignore upload or add later
        image_url = None  # or build path if you implement uploads

        db.add_review(session['user_id'], product_id, content, rating, image_url)


        flash("Review submitted!", "success")
        return redirect(url_for('product_detail', product_id=product_id))

    return render_template('product_detail.html', product=product, reviews=reviews)

# --- CART / CHECKOUT ---
@app.route('/cart')
@login_required
def cart():
    user_id = session.get('user_id')
    items = db.get_cart(user_id)
    total = sum(item['price'] * item['quantity'] for item in items)
    return render_template('cart.html', cart=items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user_id = session.get('user_id')
    db.add_to_cart(user_id, product_id)
    flash("Product added to cart.", "success")
    return redirect(url_for('shop'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    user_id = session.get('user_id')
    db.remove_from_cart(user_id, product_id)
    flash("Product removed from cart.", "info")
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    user_id = session.get('user_id')
    items = db.get_cart(user_id)
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('shop'))

    total = sum(item['price'] * item['quantity'] for item in items)

    if request.method == 'POST':
        # Re-check inventory for each item (TOCTOU mitigation)
        for item in items:
            current_stock = db.check_inventory(item['id'])
            if current_stock is None:
                flash(f"Product {item['name']} not found.", "warning")
                return redirect(url_for('cart'))
            if current_stock < item['quantity']:
                flash(f"Sorry, '{item['name']}' sold out or insufficient stock while you checked out.", "warning")
                return redirect(url_for('cart'))

        # All items good: create order and reduce inventory atomically
        order_id = db.create_order(user_id, total)
        for item in items:
            ok = db.reduce_inventory(item['id'], item['quantity'])
            if not ok:
                flash(f"Could not reserve '{item['name']}', please try again.", "warning")
                return redirect(url_for('cart'))
            db.add_order_item(order_id, item['id'], item['quantity'], item['price'])

        db.clear_cart_for_user(user_id)
        flash("Order placed successfully!", "success")
        return redirect(url_for('shop'))

    return render_template('checkout.html', total=total)

# --- AUTH / REGISTRATION ---
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

        # default role 'user'
        success = db.add_user(username, password, email, role='user')
        if success:
            flash("Registration complete! You can now log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Username or email already taken, try a different one.", "danger")
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
            # regenerate session (prevent fixation)
            session.clear()
            session['session_id'] = str(uuid.uuid4())
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'user').lower()
            session.permanent = True

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
    app.run(debug=IS_DEVELOPMENT)

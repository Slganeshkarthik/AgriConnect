from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory, abort
from flask_cors import CORS
import sqlite3  # Add this import for SQLite
import os
import datetime
from datetime import timezone, timedelta
import json
import razorpay
from flask import request, jsonify

client = razorpay.Client(auth=("rzp_test_RnylgmQBIKOxI1", "pUlkDtWEWWO0tgQFkRIm3l3M"))
app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'TrashtoCash@123')  # Better secret key handling
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set max content length to 16MB
app.config['MAX_COOKIE_SIZE'] = 4096  # Set max cookie size to 4KB

# Enable CORS for React development
CORS(app, supports_credentials=True)

# Define database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'user_database.db')

# Store notifications for collectors with IDs and completion status
Farmers_notifications = {}
next_notification_id = 1

def get_current_time():
    # Get current UTC time
    utc_now = datetime.datetime.now(timezone.utc)
    # Convert to IST (UTC+5:30)
    ist = utc_now + timedelta(hours=5, minutes=30)
    return ist.strftime("%d-%m-%Y"), ist.strftime("%H:%M:%S")

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # coustomer login info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # coustomer's form details
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            name TEXT,
            address TEXT,
            phone TEXT,
            login_type TEXT       
        )
    ''')
    
    # Add pincode column if it doesn't exist (migration)
    try:
        cursor.execute("ALTER TABLE user_details ADD COLUMN pincode TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass

    # Farmers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            contact TEXT,
            address TEXT,
            pincode TEXT,
            prod_type TEXT NOT NULL
        )
    ''')

    # Ratings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Farmer_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Farmers_username TEXT NOT NULL,
            coustomer_username TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (Farmers_username) REFERENCES Farmers(username),
            FOREIGN KEY (coustomer_username) REFERENCES users(username),
            UNIQUE(Farmers_username, coustomer_username)
        )
    ''')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            name TEXT,
            address TEXT,
            pincode TEXT,
            phone TEXT,
            total_amount REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')

    # Order items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id TEXT,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')

    # Product ratings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username),
            UNIQUE(product_id, username)
        )
    ''')

    conn.commit() # save changes 
    conn.close()

def get_user_details(username: str):
    """Fetch user details by username from user_details table."""
    if not username:
        return None
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT name, address, pincode, phone, username FROM user_details WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'name': row[0],
        'address': row[1],
        'pincode':row[2],
        'phone': row[3],
        'username': row[4],
    }

def get_Farmers_rating(Farmers_username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT AVG(rating) as avg_rating, COUNT(rating) as total_ratings 
        FROM Farmer_ratings 
        WHERE Farmers_username = ?
    ''', (Farmers_username,))
    result = cursor.fetchone()
    conn.close()

    avg_rating = round(result[0], 1) if result and result[0] is not None else 0
    total_ratings = result[1] if result else 0
    return avg_rating, total_ratings

# Initialize Farmers_notifications for all collectors in DB
def initialize_Farmers_notifications():
    global Farmers_notifications
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # First ensure the collectors table exists
    init_db()
    
    cursor.execute('SELECT username FROM Farmers')
    for row in cursor.fetchall():
        Farmers_notifications[row[0]] = []
    conn.close()

@app.route('/')
def home():
    # Load JSON products
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', []) if isinstance(data, dict) else data
    except:
        products = []

    # pass user details (if logged in) to template
    user = get_user_details(session.get('username')) if session.get('username') else None
    return render_template('home.html', products=products, user=user)


@app.route('/login.html')
def login():
    return render_template('login.html')
@app.route('/signup.html')
def signup():
    return render_template('signup.html')

@app.route('/cart.html')
def cart():
    user = get_user_details(session.get('username')) if session.get('username') else None
    return render_template('cart.html', user=user)

# ---------------------- SIGNUP POST ROUTE ----------------------
@app.route('/signup', methods=['POST'])
def signup_post():
    try:
        name = (request.form.get('name') or '').strip()
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        address = (request.form.get('address') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        pincode = (request.form.get('pincode') or '').strip()
        login_type = (request.form.get('login_type') or '').strip()

        if not username or not password:
            return "Username and password are required!", 400

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Check duplicate username
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        exists = cur.fetchone()

        if exists:
            conn.close()
            return "Username already exists! Choose another one."

        # Insert into users table (only username, password - no login_type column)
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))

        # Insert user details with pincode and phone
        cur.execute(
            "INSERT INTO user_details (username, name, address, pincode, phone, login_type) VALUES (?, ?, ?, ?, ?, ?)",
            (username, name, address, pincode, phone, login_type)
        )

        conn.commit()
        conn.close()

        # Auto login after signup
        session['username'] = username
        return redirect(url_for('home'))

    except Exception as e:
        return f"Signup error: {str(e)}", 500


# ---------------------- LOGIN POST ROUTE ----------------------
@app.route('/login', methods=['POST'])
def login_post():
    try:
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()

        if not username or not password:
            return "Username and password are required!", 400

        # Hardcoded admin login
        if username == 'admin' and password == 'admin123':
            session['username'] = 'admin'
            session['is_admin'] = True
            return redirect(url_for('admin_panel'))

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Check credentials (users table only has username and password)
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()

        if not user:
            return "Invalid username or password!", 401

        # Save login session
        session['username'] = username
        session['is_admin'] = False
        
        # Check if user was trying to checkout
        if session.get('checkout_redirect'):
            session.pop('checkout_redirect')
            return redirect(url_for('checkout'))
        
        return redirect(url_for('home'))

    except Exception as e:
        return f"Login error: {str(e)}", 500


# ---------------------- LOGOUT ROUTE ----------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/products.xlsx')
def products_xlsx():
    # Serve the products.xlsx file from project root so the client can fetch it
    root = os.path.dirname(__file__)
    return send_from_directory(root, 'products.xlsx')

@app.route('/farmers2.html')
def load_products():
    # Load farm product list from `farm_product.json` and pass to template
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'farm_product.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            farm_products = json.load(f)
            # farm_product.json is expected to be an array of product objects
            if isinstance(farm_products, dict):
                # defensively handle object-wrapped arrays
                products = farm_products.get('products', [])
            else:
                products = farm_products
    except Exception:
        products = []

    user = get_user_details(session.get('username')) if session.get('username') else None
    return render_template('farmers2.html', products=products, user=user)

@app.route('/30-min.html')
def fast_delivery():
    # Show products available for 30-minute delivery based on pincode match
    # Get source parameter to determine which JSON to use
    source = request.args.get('source', 'home')  # 'home' for products.json, 'farmers' for farm_product.json
    user = get_user_details(session.get('username')) if session.get('username') else None
    return render_template('30-min.html', user=user, source=source)


@app.route('/profile.html')
def profile():
    # Show user profile with order history
    if not session.get('username'):
        return redirect(url_for('login'))
    
    username = session.get('username')
    user = get_user_details(username)
    
    if not user:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all orders for the user
    cur.execute('''
        SELECT id, order_number, username, name, address, pincode, phone, 
               total_amount, status, created_at
        FROM orders
        WHERE username = ?
        ORDER BY created_at DESC
    ''', (username,))
    
    orders_data = cur.fetchall()
    
    # Get order items for each order
    orders = []
    total_spent = 0
    pending_count = 0
    completed_count = 0
    
    for order in orders_data:
        order_id = order[0]
        
        # Get items for this order
        cur.execute('''
            SELECT product_name, quantity, price
            FROM order_items
            WHERE order_id = ?
        ''', (order_id,))
        
        items = cur.fetchall()
        
        orders.append({
            'id': order[0],
            'order_number': order[1],
            'username': order[2],
            'name': order[3],
            'address': order[4],
            'pincode': order[5],
            'phone': order[6],
            'total_amount': order[7],
            'status': order[8],
            'created_at': order[9],
            'item_count': len(items)
        })
        
        total_spent += order[7] if order[7] else 0
        
        if order[8] == 'pending':
            pending_count += 1
        elif order[8] == 'completed':
            completed_count += 1
    
    # Get member since date (first order date or account creation)
    cur.execute('SELECT MIN(created_at) FROM orders WHERE username = ?', (username,))
    first_order = cur.fetchone()
    member_since = first_order[0] if first_order and first_order[0] else 'Recent'
    
    conn.close()
    
    return render_template('profile.html', 
                         user=user, 
                         orders=orders,
                         total_orders=len(orders),
                         pending_orders=pending_count,
                         completed_orders=completed_count,
                         total_spent=total_spent,
                         member_since=member_since)


@app.route('/api/products')
def api_products():
    # Return products from farm_product.json
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'farm_product.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        # If file missing or invalid, return empty list with error info
        return jsonify({"error": str(e), "products": []}), 500

    return jsonify(products)


@app.route('/api/home-products')
def api_home_products():
    # Return products from products.json (home page products)
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', []) if isinstance(data, dict) else data
    except Exception as e:
        return jsonify({"error": str(e), "products": []}), 500

    return jsonify(products)


@app.route('/api/products/<product_id>')
def api_product(product_id):
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'farm_product.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    product = next((p for p in products if str(p.get('id')) == str(product_id)), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


@app.route('/checkout')
def checkout():
    # Check if user is logged in
    if not session.get('username'):
        # Store the intended destination in session
        session['checkout_redirect'] = True
        return redirect(url_for('login'))
    
    # Get user details for address confirmation
    user = get_user_details(session.get('username'))
    if not user:
        return redirect(url_for('login'))
    
    return render_template('proceedToCheckOutCart.html', user=user)

@app.route('/create-razorpay-order', methods=['POST'])
def create_razorpay_order():
    data = request.json
    amount = int(data['amount']) * 100  # convert ₹ to paise

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify(order)

@app.route('/payment.html')
def payment():
    # Check if user is logged in
    if not session.get('username'):
        return redirect(url_for('login'))
    
    # Get user details for payment page
    user = get_user_details(session.get('username'))
    if not user:
        return redirect(url_for('login'))
    
    return render_template('payment.html', user=user)

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    data = request.json

    try:
        client.utility.verify_payment_signature({
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_signature': data['razorpay_signature']
        })

        return jsonify({"success": True})

    except:
        return jsonify({"success": False})

@app.route('/api/place-order', methods=['POST'])
def place_order():
    try:
        if not session.get('username'):
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        data = request.get_json()
        cart_items = data.get('cart', [])
        
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400
        
        username = session.get('username')
        user = get_user_details(username)
        
        if not user or not user.get('name') or not user.get('address') or not user.get('phone') or not user.get('pincode'):
            return jsonify({'success': False, 'message': 'Please complete your delivery details'}), 400
        
        # Calculate total
        total = sum((float(item.get('price', 0)) * int(item.get('qty', 1))) for item in cart_items)
        
        # Generate order number
        import random, string
        order_number = 'ORD' + ''.join(random.choices(string.digits, k=8))
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Insert order
        cur.execute(
            """INSERT INTO orders (order_number, username, name, address, pincode, phone, total_amount, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (order_number, username, user['name'], user['address'], user['pincode'], user['phone'], total)
        )
        order_id = cur.lastrowid
        
        # Insert order items
        for item in cart_items:
            cur.execute(
                """INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                   VALUES (?, ?, ?, ?, ?)""",
                (order_id, item.get('id'), item.get('name'), item.get('qty', 1), item.get('price'))
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Order placed successfully!',
            'order_number': order_number
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin')
@app.route('/admin.html')
def admin_panel():
    # Check if user is logged in as admin
    if not session.get('username'):
        return redirect(url_for('login'))
    
    # Admin doesn't have user details in database
    if session.get('username') == 'admin':
        user = {'username': 'admin', 'name': 'Administrator', 'address': None, 'phone': None, 'pincode': None}
    else:
        user = get_user_details(session.get('username'))
        if not user:
            return redirect(url_for('login'))
    
    # Get all orders grouped by pincode
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, order_number, username, name, address, pincode, phone, 
               total_amount, status, created_at
        FROM orders
        ORDER BY pincode, created_at DESC
    ''')
    orders = cur.fetchall()
    conn.close()
    
    # Group orders by pincode
    orders_by_pincode = {}
    for order in orders:
        pincode = order[5] or 'No Pincode'
        if pincode not in orders_by_pincode:
            orders_by_pincode[pincode] = []
        orders_by_pincode[pincode].append({
            'id': order[0],
            'order_number': order[1],
            'username': order[2],
            'name': order[3],
            'address': order[4],
            'pincode': order[5],
            'phone': order[6],
            'total_amount': order[7],
            'status': order[8],
            'created_at': order[9]
        })
    
    # Count pending orders and total orders
    pending_count = sum(1 for order in orders if order[8] == 'pending')
    total_orders = len(orders)
    
    return render_template('admin.html', 
                         orders_by_pincode=orders_by_pincode, 
                         pending_count=pending_count,
                         total_orders=total_orders,
                         user=user)


@app.route('/api/update-order-status', methods=['POST'])
def update_order_status():
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    order_id = data.get('order_id')
    status = data.get('status')
    
    if not order_id or not status:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        cur.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Order status updated to {status}'
        })
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/update-user-details', methods=['POST'])
def update_user_details():
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        address = data.get('address', '').strip()
        pincode = data.get('pincode', '').strip()
        phone = data.get('phone', '').strip()
        
        if not name or not address or not pincode or not phone:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Validate pincode (6 digits)
        if not pincode.isdigit() or len(pincode) != 6:
            return jsonify({'success': False, 'message': 'Pincode must be 6 digits'}), 400
        
        # Validate phone (10 digits)
        if not phone.isdigit() or len(phone) != 10:
            return jsonify({'success': False, 'message': 'Phone number must be 10 digits'}), 400
        
        username = session.get('username')
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Update user details
        cur.execute(
            """UPDATE user_details 
               SET name = ?, address = ?, pincode = ?, phone = ? 
               WHERE username = ?""",
            (name, address, pincode, phone, username)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Details updated successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/product/<product_id>')
def product_page(product_id):
    # Render a product detail page by id
    # Check both products.json and farm_product.json
    product = None
    
    # First check products.json (home page products)
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', []) if isinstance(data, dict) else data
            product = next((p for p in products if str(p.get('id')) == str(product_id)), None)
    except Exception:
        pass
    
    # If not found, check farm_product.json (farmers page products)
    if not product:
        try:
            data_path = os.path.join(os.path.dirname(__file__), 'farm_product.json')
            with open(data_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
                product = next((p for p in products if str(p.get('id')) == str(product_id)), None)
        except Exception:
            pass
    
    if not product:
        abort(404)
    
    user = get_user_details(session.get('username')) if session.get('username') else None
    username = session.get('username')
    
    # Get product ratings
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Calculate average rating
    cur.execute('SELECT AVG(rating), COUNT(*) FROM product_ratings WHERE product_id = ?', (product_id,))
    rating_data = cur.fetchone()
    avg_rating = round(rating_data[0], 1) if rating_data and rating_data[0] else 0
    total_ratings = rating_data[1] if rating_data else 0
    
    # Get all ratings with user details
    cur.execute('''
        SELECT pr.rating, pr.comment, pr.created_at, pr.username
        FROM product_ratings pr
        WHERE pr.product_id = ?
        ORDER BY pr.created_at DESC
    ''', (product_id,))
    ratings = cur.fetchall()
    
    # Check if user has purchased this product (completed orders only)
    has_purchased = False
    user_rating = None
    if username:
        cur.execute('''
            SELECT COUNT(*) FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.username = ? AND oi.product_id = ? AND o.status = 'completed'
        ''', (username, product_id))
        has_purchased = cur.fetchone()[0] > 0
        
        # Get user's existing rating
        cur.execute('SELECT rating, comment FROM product_ratings WHERE product_id = ? AND username = ?', 
                   (product_id, username))
        user_rating_data = cur.fetchone()
        if user_rating_data:
            user_rating = {'rating': user_rating_data[0], 'comment': user_rating_data[1]}
    
    conn.close()
    
    return render_template('product.html', 
                         product=product, 
                         user=user,
                         avg_rating=avg_rating,
                         total_ratings=total_ratings,
                         ratings=ratings,
                         has_purchased=has_purchased,
                         user_rating=user_rating)


# ============== React API Endpoints ==============

@app.route('/api/me', methods=['GET'])
def api_me():
    """Get current user info"""
    if not session.get('username'):
        return jsonify({'success': False}), 401
    
    user = get_user_details(session.get('username'))
    if user:
        return jsonify({
            'success': True,
            'user': {
                'username': user.get('username'),
                'name': user.get('name'),
                'address': user.get('address'),
                'pincode': user.get('pincode'),
                'phone': user.get('phone')
            }
        })
    return jsonify({'success': False}), 401


@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] == password:
        session['username'] = username
        user = get_user_details(username)
        return jsonify({
            'success': True,
            'user': {
                'username': user.get('username'),
                'name': user.get('name'),
                'address': user.get('address'),
                'pincode': user.get('pincode'),
                'phone': user.get('phone')
            }
        })
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/api/signup', methods=['POST'])
def api_signup():
    """API endpoint for signup"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        cursor.execute('INSERT INTO user_details (username) VALUES (?)', (username,))
        conn.commit()
        
        session['username'] = username
        user = get_user_details(username)
        
        return jsonify({
            'success': True,
            'user': {
                'username': user.get('username'),
                'name': user.get('name'),
                'address': user.get('address'),
                'pincode': user.get('pincode'),
                'phone': user.get('phone')
            }
        })
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    finally:
        conn.close()


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API endpoint for logout"""
    session.pop('username', None)
    return jsonify({'success': True})


@app.route('/api/profile', methods=['GET'])
def api_profile():
    """Get user profile with order history"""
    if not session.get('username'):
        return jsonify({'success': False}), 401
    
    username = session.get('username')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all orders for the user
    cur.execute('''
        SELECT id, order_number, username, name, address, pincode, phone, 
               total_amount, status, created_at 
        FROM orders 
        WHERE username = ?
        ORDER BY created_at DESC
    ''', (username,))
    
    orders = []
    total_spent = 0
    pending_count = 0
    completed_count = 0
    
    for order in cur.fetchall():
        # Get item count for this order
        cur.execute('SELECT COUNT(*) FROM order_items WHERE order_id = ?', (order['id'],))
        item_count = cur.fetchone()[0]
        
        orders.append({
            'id': order['id'],
            'order_number': order['order_number'],
            'username': order['username'],
            'name': order['name'],
            'address': order['address'],
            'pincode': order['pincode'],
            'phone': order['phone'],
            'total_amount': order['total_amount'],
            'status': order['status'],
            'created_at': order['created_at'],
            'item_count': item_count
        })
        
        total_spent += order['total_amount']
        if order['status'] == 'pending':
            pending_count += 1
        elif order['status'] == 'completed':
            completed_count += 1
    
    conn.close()
    
    return jsonify({
        'success': True,
        'orders': orders,
        'total_orders': len(orders),
        'pending_orders': pending_count,
        'completed_orders': completed_count,
        'total_spent': total_spent
    })


@app.route('/api/admin/orders', methods=['GET'])
def api_admin_orders():
    """Get all orders for admin"""
    if not session.get('username') or session.get('username') != 'admin':
        return jsonify({'success': False}), 403
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute('''
        SELECT id, order_number, username, name, address, pincode, phone, 
               total_amount, status, created_at 
        FROM orders 
        ORDER BY created_at DESC
    ''')
    
    orders = []
    for order in cur.fetchall():
        orders.append({
            'id': order['id'],
            'order_number': order['order_number'],
            'username': order['username'],
            'name': order['name'],
            'address': order['address'],
            'pincode': order['pincode'],
            'phone': order['phone'],
            'total_amount': order['total_amount'],
            'status': order['status'],
            'created_at': order['created_at']
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'orders': orders
    })


@app.route('/api/submit-rating', methods=['POST'])
def submit_rating():
    """Submit product rating"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        
        if not product_id or not rating:
            return jsonify({'success': False, 'message': 'Product ID and rating required'}), 400
        
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400
        
        username = session.get('username')
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Check if user has purchased this product
        cur.execute('''
            SELECT COUNT(*) FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.username = ? AND oi.product_id = ? AND o.status = 'completed'
        ''', (username, product_id))
        
        has_purchased = cur.fetchone()[0] > 0
        
        if not has_purchased:
            conn.close()
            return jsonify({'success': False, 'message': 'You can only rate products you have purchased'}), 403
        
        # Insert or update rating
        cur.execute('''
            INSERT INTO product_ratings (product_id, username, rating, comment)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(product_id, username) 
            DO UPDATE SET rating = ?, comment = ?, created_at = CURRENT_TIMESTAMP
        ''', (product_id, username, rating, comment, rating, comment))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Rating submitted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/download-invoice/<int:order_id>', methods=['GET'])
def download_invoice(order_id):
    """Generate and download invoice for an order"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    username = session.get('username')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get order details
    cur.execute('''
        SELECT id, order_number, username, name, address, pincode, phone, 
               total_amount, status, created_at 
        FROM orders 
        WHERE id = ? AND (username = ? OR ? = 'admin')
    ''', (order_id, username, username))
    
    order = cur.fetchone()
    
    if not order:
        conn.close()
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    
    # Get order items
    cur.execute('''
        SELECT product_name, quantity, price 
        FROM order_items 
        WHERE order_id = ?
    ''', (order_id,))
    
    items = cur.fetchall()
    conn.close()
    
    # Render invoice template
    return render_template('invoice.html',
                         order_number=order['order_number'],
                         created_at=order['created_at'],
                         status=order['status'],
                         name=order['name'],
                         phone=order['phone'],
                         username=order['username'],
                         address=order['address'],
                         pincode=order['pincode'],
                         items=items,
                         total_amount=order['total_amount'])

if __name__ == '__main__':
    init_db()  # Initialize database first
    initialize_Farmers_notifications()  # Then initialize notifications
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

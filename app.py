from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory, abort
from flask_cors import CORS
import sqlite3  # Add this import for SQLite
import os
import datetime
from datetime import timezone, timedelta
import json
from flask import request, jsonify

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'AgriConnect@123')  # Better secret key handling
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
    
    # Add payment_method column if it doesn't exist (migration)
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Add payment_id column if it doesn't exist (migration)
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_id TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Add otp column if it doesn't exist (migration)
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN otp TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass

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

    # Farmer order notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmer_order_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_username TEXT NOT NULL,
            order_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            customer_username TEXT NOT NULL,
            customer_name TEXT,
            status TEXT DEFAULT 'pending',
            read_status INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (farmer_username) REFERENCES users(username),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')
    
    # Add price column to farmer_order_notifications if it doesn't exist (migration)
    try:
        cursor.execute("ALTER TABLE farmer_order_notifications ADD COLUMN price REAL DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Soil test bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS soil_test_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            farm_location TEXT NOT NULL,
            farm_size REAL NOT NULL,
            contact_number TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            test_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    
    # Customer feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            message TEXT,
            page_source TEXT,
            created_at TEXT
        )
    ''')
    
    # Add phone column to customer_feedback if it doesn't exist (migration)
    try:
        cursor.execute("ALTER TABLE customer_feedback ADD COLUMN phone TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Community posts table for farmer social media
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image_path TEXT,
            created_at TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    
    # Community replies table for solutions/comments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS community_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (post_id) REFERENCES community_posts(id),
            FOREIGN KEY (username) REFERENCES users(username)
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
    cur.execute('SELECT name, address, pincode, phone, username, login_type FROM user_details WHERE username = ?', (username,))
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
        'login_type': row[5],
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

# Admin notifications storage
admin_notifications = []

def notify_admin_new_farmer(username, name):
    """Notify second admin about new farmer registration"""
    date_str, time_str = get_current_time()
    notification = {
        'id': len(admin_notifications) + 1,
        'type': 'new_farmer',
        'username': username,
        'name': name,
        'message': f'New farmer registered: {name} ({username})',
        'timestamp': f'{date_str} {time_str}',
        'read': False
    }
    admin_notifications.append(notification)
    return notification

def notify_admin_soil_test(username, name, booking_id, test_type):
    """Notify admin2 about soil test booking"""
    date_str, time_str = get_current_time()
    notification = {
        'id': len(admin_notifications) + 1,
        'type': 'soil_test',
        'username': username,
        'name': name,
        'booking_id': booking_id,
        'test_type': test_type,
        'message': f'Soil test booked by {name}: {test_type} (ID: {booking_id})',
        'timestamp': f'{date_str} {time_str}',
        'read': False
    }
    admin_notifications.append(notification)
    return notification

@app.route('/')
@app.route('/home.html')
def home():
    force_home = (request.args.get('force') or '').lower() in {'1', 'true', 'yes'}

    # Check if user is a farmer and redirect to farmers2.html unless forced
    if session.get('username') and not force_home:
        user = get_user_details(session.get('username'))
        if user and user.get('login_type', '').lower() == 'farmer':
            return redirect(url_for('load_products'))
    
    # Load JSON products
    all_products = []
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', []) if isinstance(data, dict) else data
            all_products.extend(products)
    except:
        pass

    # pass user details (if logged in) to template
    user = get_user_details(session.get('username')) if session.get('username') else None
    return render_template('home.html', products=all_products, user=user)


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
        session['login_type'] = login_type
        
        # Redirect based on user type
        if login_type.lower() == 'farmer':
            # Notify admin about new farmer registration
            notify_admin_new_farmer(username, name)
            return redirect(url_for('load_products'))
        else:
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
            session['login_type'] = 'admin'
            return redirect(url_for('admin_panel'))
        
        # Hardcoded second admin login
        if username == 'admin2' and password == 'admin123':
            session['username'] = 'admin2'
            session['is_admin'] = True
            session['login_type'] = 'admin'
            return redirect(url_for('admin_panel'))

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Check credentials (users table only has username and password)
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        
        if not user:
            conn.close()
            return "Invalid username or password!", 401
        
        # Get user type from user_details
        cur.execute("SELECT login_type FROM user_details WHERE username=?", (username,))
        user_type_row = cur.fetchone()
        user_type = user_type_row[0] if user_type_row else 'customer'
        conn.close()

        # Save login session
        session['username'] = username
        session['is_admin'] = False
        session['login_type'] = user_type
        
        # Check if user was trying to checkout
        if session.get('checkout_redirect'):
            session.pop('checkout_redirect')
            return redirect(url_for('checkout'))
        
        # Redirect based on user type
        if user_type.lower() == 'farmer':
            return redirect(url_for('load_products'))
        else:
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

@app.route('/farmer_products.html')
def farmer_products():
    # Check if user is logged in as farmer
    if not session.get('username'):
        return redirect(url_for('login'))
    
    user = get_user_details(session.get('username'))
    if not user or user.get('login_type', '').lower() != 'farmer':
        return redirect(url_for('home'))
    
    return render_template('farmer_products.html', user=user)

@app.route('/contact.html')
def contact():
    user = get_user_details(session.get('username')) if session.get('username') else None
    
    # Load dealers data from JSON file
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'dealers.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            dealers = json.load(f)
    except Exception as e:
        print(f"Error loading dealers.json: {e}")
        dealers = {}
    
    return render_template('contact.html', user=user, dealers=dealers)

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
    
    # Get soil test bookings if user is a farmer
    soil_tests = []
    if user.get('login_type', '').lower() == 'farmer':
        cur.execute('''
            SELECT id, booking_id, farm_location, farm_size, contact_number, 
                   preferred_date, test_type, status, created_at
            FROM soil_test_bookings
            WHERE username = ?
            ORDER BY id DESC
        ''', (username,))
        
        soil_test_data = cur.fetchall()
        for st in soil_test_data:
            soil_tests.append({
                'id': st[0],
                'booking_id': st[1],
                'farm_location': st[2],
                'farm_size': st[3],
                'contact_number': st[4],
                'preferred_date': st[5],
                'test_type': st[6],
                'status': st[7],
                'created_at': st[8]
            })
    
    # Get all orders for the user
    cur.execute('''
        SELECT id, order_number, username, name, address, pincode, phone, 
               total_amount, status, created_at, payment_method, otp
        FROM orders
        WHERE username = ?
        ORDER BY id DESC
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
            'payment_method': order[10],
            'otp': order[11],
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
                         member_since=member_since,
                         soil_tests=soil_tests)


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


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Store customer feedback from home.html and farmers2.html"""
    try:
        data = request.json
        
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        phone = (data.get('phone') or '').strip()
        rating = int(data.get('rating', 0))
        message = (data.get('message') or '').strip()
        page_source = (data.get('page_source') or 'unknown').strip()
        
        if not name or not email or rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Please provide name, email, and a valid rating (1-5)'}), 400
        
        # Get current IST time
        date_str, time_str = get_current_time()
        created_at = f"{date_str} {time_str}"
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute(
            '''INSERT INTO customer_feedback (name, email, phone, rating, message, page_source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (name, email, phone, rating, message, page_source, created_at)
        )
        
        conn.commit()
        feedback_id = cur.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'message': 'Thank you for your feedback!', 'feedback_id': feedback_id})
        
    except Exception as e:
        print(f"Feedback error: {e}")
        return jsonify({'success': False, 'message': 'Could not save feedback'}), 500


@app.route('/api/home-products')
def api_home_products():
    # Return products from products.json
    all_products = []
    seller_cache = {}
    
    # Load JSON products
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', []) if isinstance(data, dict) else data
            for product in products:
                enriched = dict(product)
                seller_username = enriched.get('seller_username')
                if seller_username:
                    if seller_username not in seller_cache:
                        seller_cache[seller_username] = get_user_details(seller_username)
                    seller_info = seller_cache.get(seller_username)
                    if seller_info:
                        if not enriched.get('farmer'):
                            enriched['farmer'] = seller_info.get('name', seller_username)
                        enriched['pincode'] = seller_info.get('pincode', '')
                        if seller_info.get('address') and not enriched.get('location'):
                            enriched['location'] = seller_info['address']
                all_products.append(enriched)
    except Exception as e:
        print(f"Error loading products.json: {e}")

    return jsonify(all_products)


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
    """Dummy payment order creation - simulates payment gateway"""
    data = request.json
    amount = int(data['amount']) * 100  # convert ₹ to paise

    # Simulate order creation with dummy data
    import random, string
    dummy_order = {
        "id": "order_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=14)),
        "amount": amount,
        "currency": "INR",
        "status": "created"
    }

    return jsonify(dummy_order)

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

@app.route('/create-order', methods=['POST'])
def create_order():
    """Create order for COD payments"""
    try:
        if not session.get('username'):
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        data = request.json
        payment_method = data.get('payment_method')
        amount = data.get('amount')
        cart_items = data.get('cart', [])
        
        username = session.get('username')
        user = get_user_details(username)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart items missing for this order'}), 400
        
        # Generate order number and OTP
        import random, string
        order_number = 'ORD' + ''.join(random.choices(string.digits, k=8))
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Get current IST time
        date_str, time_str = get_current_time()
        created_at = f"{date_str} {time_str}"
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Insert order with payment method, OTP and IST timestamp
        cur.execute(
            """INSERT INTO orders (order_number, username, name, address, pincode, phone, total_amount, status, payment_method, otp, created_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)""",
            (order_number, username, user.get('name', ''), user.get('address', ''), 
             user.get('pincode', ''), user.get('phone', ''), amount, payment_method, otp, created_at)
        )
        order_id = cur.lastrowid
        
        # Load products.json for farmer lookup
        farmer_products = {}
        try:
            data_path = os.path.join(os.path.dirname(__file__), 'products.json')
            with open(data_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                products_list = json_data.get('products', []) if isinstance(json_data, dict) else json_data
                for p in products_list:
                    if p.get('seller_type') == 'farmer':
                        farmer_products[p['id']] = p['seller_username']
        except Exception as e:
            print(f"Error loading products.json for notifications: {e}")
        
        # Optimize: Batch insert order items and notifications
        order_items_to_insert = []
        notifications_to_insert = []
        
        for item in cart_items:
            product_id = item.get('id')
            product_name = item.get('name')
            quantity = int(item.get('qty', 1))
            price = float(item.get('price', 0))

            order_items_to_insert.append((
                order_id,
                product_id,
                product_name,
                quantity,
                price
            ))
            
            # Check if this is a farmer product from JSON
            farmer_username = farmer_products.get(product_id)
            if farmer_username:
                notifications_to_insert.append((
                    farmer_username, order_id, product_id, product_name, quantity, 
                    username, user.get('name', ''), 'pending', created_at, price
                ))
        
        if order_items_to_insert:
            cur.executemany(
                """INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                   VALUES (?, ?, ?, ?, ?)""",
                order_items_to_insert
            )
        
        if notifications_to_insert:
            cur.executemany(
                """INSERT INTO farmer_order_notifications 
                   (farmer_username, order_id, product_id, product_name, quantity, 
                    customer_username, customer_name, status, created_at, price)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                notifications_to_insert
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'order_number': order_number,
            'otp': otp
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    """Dummy payment verification - always succeeds for simulation"""
    data = request.json

    try:
        # Simulate payment verification (always successful in dummy mode)
        # Save payment details to database if needed
        if session.get('username'):
            username = session.get('username')
            user = get_user_details(username)
            amount = data.get('amount')
            cart_items = data.get('cart', [])
            
            if not cart_items:
                return jsonify({'success': False, 'error': 'Cart items missing for this order'}), 400
            
            # Generate order number, payment ID and OTP
            import random, string
            order_number = 'ORD' + ''.join(random.choices(string.digits, k=8))
            payment_id = data.get('razorpay_payment_id', 'DUMMY_' + ''.join(random.choices(string.digits, k=10)))
            otp = ''.join(random.choices(string.digits, k=6))
            
            # Get current IST time
            date_str, time_str = get_current_time()
            created_at = f"{date_str} {time_str}"
            
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # Insert order with payment details, OTP and IST timestamp
            cur.execute(
                """INSERT INTO orders (order_number, username, name, address, pincode, phone, total_amount, status, payment_method, payment_id, otp, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'paid', 'Online', ?, ?, ?)""",
                (order_number, username, user.get('name', ''), user.get('address', ''), 
                 user.get('pincode', ''), user.get('phone', ''), amount, payment_id, otp, created_at)
            )
            order_id = cur.lastrowid
            
            # Load products.json for farmer lookup
            farmer_products = {}
            try:
                data_path = os.path.join(os.path.dirname(__file__), 'products.json')
                with open(data_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    products_list = json_data.get('products', []) if isinstance(json_data, dict) else json_data
                    for p in products_list:
                        if p.get('seller_type') == 'farmer':
                            farmer_products[p['id']] = p['seller_username']
            except Exception as e:
                print(f"Error loading products.json for notifications: {e}")
            
            # Optimize: Batch insert order items and notifications
            order_items_to_insert = []
            notifications_to_insert = []
            
            for item in cart_items:
                product_id = item.get('id')
                product_name = item.get('name')
                quantity = int(item.get('qty', 1))
                price = float(item.get('price', 0))
                
                order_items_to_insert.append((
                    order_id,
                    product_id,
                    product_name,
                    quantity,
                    price
                ))
                
                # Check if this is a farmer product from JSON
                farmer_username = farmer_products.get(product_id)
                if farmer_username:
                    notifications_to_insert.append((
                        farmer_username, order_id, product_id, product_name, quantity, 
                        username, user.get('name', ''), 'paid', created_at, price
                    ))
            
            if order_items_to_insert:
                cur.executemany(
                    """INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                       VALUES (?, ?, ?, ?, ?)""",
                    order_items_to_insert
                )
            
            if notifications_to_insert:
                cur.executemany(
                    """INSERT INTO farmer_order_notifications 
                       (farmer_username, order_id, product_id, product_name, quantity, 
                        customer_username, customer_name, status, created_at, price)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    notifications_to_insert
                )
            
            conn.commit()
            conn.close()

        return jsonify({"success": True, "otp": otp, "order_number": order_number})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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
        
        # Insert order items and notify farmers
        date_str, time_str = get_current_time()
        created_at = f"{date_str} {time_str}"
        
        # Load products.json for farmer lookup
        farmer_products = {}
        try:
            data_path = os.path.join(os.path.dirname(__file__), 'products.json')
            with open(data_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                products_list = json_data.get('products', []) if isinstance(json_data, dict) else json_data
                for p in products_list:
                    if p.get('seller_type') == 'farmer':
                        farmer_products[p['id']] = p['seller_username']
        except Exception as e:
            print(f"Error loading products.json for notifications: {e}")
        
        # Optimize: Batch insert order items and notifications
        order_items_to_insert = []
        notifications_to_insert = []
        
        for item in cart_items:
            product_id = item.get('id')
            product_name = item.get('name')
            quantity = item.get('qty', 1)
            price = item.get('price')
            
            order_items_to_insert.append((order_id, product_id, product_name, quantity, price))
            
            # Check if this is a farmer product from JSON
            farmer_username = farmer_products.get(product_id)
            if farmer_username:
                notifications_to_insert.append((
                    farmer_username, order_id, product_id, product_name, quantity, 
                    username, user['name'], 'pending', created_at, price
                ))
        
        # Batch insert order items
        if order_items_to_insert:
            cur.executemany(
                """INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                   VALUES (?, ?, ?, ?, ?)""",
                order_items_to_insert
            )
            
        # Batch insert notifications
        if notifications_to_insert:
            cur.executemany(
                """INSERT INTO farmer_order_notifications 
                   (farmer_username, order_id, product_id, product_name, quantity, 
                    customer_username, customer_name, status, created_at, price)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                notifications_to_insert
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
    
    # Check if user is admin or admin2
    if session.get('username') not in ['admin', 'admin2']:
        return redirect(url_for('home'))
    
    # Admin doesn't have user details in database
    if session.get('username') in ['admin', 'admin2']:
        user = {'username': session.get('username'), 'name': 'Administrator', 'address': None, 'phone': None, 'pincode': None}
    else:
        user = get_user_details(session.get('username'))
        if not user:
            return redirect(url_for('login'))
    
    # Get all orders grouped by pincode
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, order_number, username, name, address, pincode, phone, 
               total_amount, status, created_at, payment_method, otp
        FROM orders
        ORDER BY id DESC
    ''')
    orders = cur.fetchall()
    
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
            'created_at': order[9],
            'payment_method': order[10],
            'otp': order[11]
        })
    
    # Count pending orders and total orders
    pending_count = sum(1 for order in orders if order[8] == 'pending')
    total_orders = len(orders)
    
    # Get notifications for admin2
    notifications = []
    soil_test_bookings = []
    if session.get('username') == 'admin2':
        # Show the freshest alerts first so new soil test requests are visible
        notifications = sorted(admin_notifications, key=lambda n: n.get('id', 0), reverse=True)
        
        # Get all soil test bookings
        cur.execute('''
            SELECT st.id, st.booking_id, st.username, st.farm_location, st.farm_size, 
                   st.contact_number, st.preferred_date, st.test_type, st.status, st.created_at,
                   ud.name
            FROM soil_test_bookings st
            LEFT JOIN user_details ud ON st.username = ud.username
            ORDER BY st.id DESC
        ''')
        
        bookings_data = cur.fetchall()
        for booking in bookings_data:
            soil_test_bookings.append({
                'id': booking[0],
                'booking_id': booking[1],
                'username': booking[2],
                'farm_location': booking[3],
                'farm_size': booking[4],
                'contact_number': booking[5],
                'preferred_date': booking[6],
                'test_type': booking[7],
                'status': booking[8],
                'created_at': booking[9],
                'farmer_name': booking[10] or booking[2]
            })
    
    conn.close()
    
    # Load dealers data from JSON file
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'dealers.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            dealers_data = json.load(f)
    except Exception as e:
        print(f"Error loading dealers.json: {e}")
        dealers_data = {}
    
    return render_template('admin.html', 
                         orders_by_pincode=orders_by_pincode, 
                         pending_count=pending_count,
                         total_orders=total_orders,
                         user=user,
                         notifications=notifications,
                         soil_test_bookings=soil_test_bookings,
                         dealers_data=dealers_data)


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
        # Check payment method before updating
        cur.execute('SELECT payment_method FROM orders WHERE id = ?', (order_id,))
        result = cur.fetchone()
        payment_method = result[0] if result else None
        
        cur.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        
        # If order is completed, reduce stock for farmer products
        if status == 'completed':
            # Get all order items
            cur.execute(
                'SELECT product_id, quantity FROM order_items WHERE order_id = ?',
                (order_id,)
            )
            order_items = cur.fetchall()
            
            # Update stock in products.json
            try:
                json_path = os.path.join(os.path.dirname(__file__), 'products.json')
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                products_list = json_data.get('products', []) if isinstance(json_data, dict) else json_data
                
                for product_id, quantity in order_items:
                    # Find and update the product stock
                    for p in products_list:
                        if p.get('id') == product_id and p.get('seller_type') == 'farmer':
                            if p.get('stock', 0) >= quantity:
                                p['stock'] -= quantity
                            break
                
                # Write back to file
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2)
                    
            except Exception as e:
                print(f"Error updating stock in products.json: {e}")
            
            # Update farmer notifications status
            cur.execute(
                'UPDATE farmer_order_notifications SET status = ? WHERE order_id = ?',
                (status, order_id)
            )

            # Remove notifications after completion so they no longer appear for the farmer
            cur.execute(
                'DELETE FROM farmer_order_notifications WHERE order_id = ?',
                (order_id,)
            )
        
        # If order is cancelled, update farmer notifications
        if status == 'cancelled':
            cur.execute(
                'UPDATE farmer_order_notifications SET status = ? WHERE order_id = ?',
                (status, order_id)
            )
        
        conn.commit()
        conn.close()
        
        response = {
            'success': True,
            'message': f'Order status updated to {status}'
        }
        
        # Add refund message for cancelled prepaid orders
        if status == 'cancelled' and payment_method == 'Online':
            response['refund_message'] = '💰 Refund will be processed within 2 business days.'
        
        return jsonify(response)
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/update-soil-test-status', methods=['POST'])
def update_soil_test_status():
    """Update soil test booking status"""
    if not session.get('username') or session.get('username') not in ['admin', 'admin2']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    booking_id = data.get('booking_id')
    status = data.get('status')
    
    if not booking_id or not status:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        cur.execute('UPDATE soil_test_bookings SET status = ? WHERE id = ?', (status, booking_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Soil test booking status updated to {status}'
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


@app.route('/api/get-order-items/<int:order_id>', methods=['GET'])
def get_order_items(order_id):
    """Get items for a specific order (Admin only)"""
    if not session.get('username') or session.get('username') not in ['admin', 'admin2']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT product_name, quantity, price 
            FROM order_items 
            WHERE order_id = ?
        ''', (order_id,))
        
        items = []
        for row in cur.fetchall():
            items.append({
                'product_name': row['product_name'],
                'quantity': row['quantity'],
                'price': row['price']
            })
            
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/download-invoice/<int:order_id>', methods=['GET'])
def download_invoice(order_id):
    """Generate and download invoice for an order"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    username = session.get('username')
    is_admin = username in ['admin', 'admin2']
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get order details
    if is_admin:
        cur.execute('''
            SELECT id, order_number, username, name, address, pincode, phone, 
                   total_amount, status, created_at 
            FROM orders 
            WHERE id = ?
        ''', (order_id,))
    else:
        cur.execute('''
            SELECT id, order_number, username, name, address, pincode, phone, 
                   total_amount, status, created_at 
            FROM orders 
            WHERE id = ? AND username = ?
        ''', (order_id, username))
    
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

@app.route('/api/book-soil-test', methods=['POST'])
def book_soil_test():
    """Book a soil test"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        farm_location = data.get('farm_location', '').strip()
        farm_size = data.get('farm_size')
        contact_number = data.get('contact_number', '').strip()
        preferred_date = data.get('preferred_date', '').strip()
        test_type = data.get('test_type', '').strip()
        
        if not all([farm_location, farm_size, contact_number, preferred_date, test_type]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        username = session.get('username')
        user = get_user_details(username)
        
        # Generate booking ID
        import random, string
        booking_id = 'ST' + ''.join(random.choices(string.digits, k=8))
        
        # Get current IST time
        date_str, time_str = get_current_time()
        created_at = f"{date_str} {time_str}"
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Insert booking
        cur.execute(
            """INSERT INTO soil_test_bookings 
               (booking_id, username, farm_location, farm_size, contact_number, preferred_date, test_type, status, created_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (booking_id, username, farm_location, farm_size, contact_number, preferred_date, test_type, created_at)
        )
        
        conn.commit()
        conn.close()
        
        # Notify admin2 about soil test booking
        notify_admin_soil_test(username, user.get('name', username), booking_id, test_type)
        
        return jsonify({
            'success': True,
            'message': 'Soil test booked successfully',
            'booking_id': booking_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/notifications', methods=['GET'])
def get_admin_notifications():
    """Get admin notifications"""
    if not session.get('username') or session.get('username') != 'admin2':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    return jsonify({
        'success': True,
        'notifications': admin_notifications,
        'count': len(admin_notifications)
    })

@app.route('/api/farmer/add-product', methods=['POST'])
def farmer_add_product():
    """Farmer adds a new product"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user = get_user_details(session.get('username'))
    if not user or user.get('login_type', '').lower() != 'farmer':
        return jsonify({'success': False, 'message': 'Only farmers can add products'}), 403
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        category = data.get('category', '').strip()
        price = data.get('price')
        stock = data.get('stock')
        unit = data.get('unit', '').strip()
        image = data.get('image', '').strip()
        description = data.get('description', '').strip()
        
        if not all([name, category, price, stock]):
            return jsonify({'success': False, 'message': 'Name, category, price, and stock are required'}), 400
        
        # Generate product ID
        import random, string
        product_id = 'FP' + ''.join(random.choices(string.digits, k=8))
        
        farmer_username = session.get('username')
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute(
            """INSERT INTO farmer_products 
               (product_id, farmer_username, name, category, price, stock, unit, image, description) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_id, farmer_username, name, category, price, stock, unit, image, description)
        )
        
        conn.commit()
        conn.close()
        
        # Add to products.json
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'products.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                products_list = json_data.get('products', []) if isinstance(json_data, dict) else json_data
                if isinstance(json_data, list):
                    json_data = {'products': products_list}
                
                new_product_json = {
                    "id": product_id,
                    "name": name,
                    "category": category,
                    "price": float(price),
                    "unit": unit,
                    "stock": int(stock),
                    "description": description,
                    "image": image or "https://via.placeholder.com/150",
                    "seller_username": farmer_username,
                    "seller_type": "farmer",
                    "location": "Local Farm"
                }
                
                products_list.append(new_product_json)
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2)
        except Exception as e:
            print(f"Error writing to products.json: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Product added successfully',
            'product_id': product_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/farmer/products', methods=['GET'])
def get_farmer_products():
    """Get all products for the logged-in farmer"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user = get_user_details(session.get('username'))
    if not user or user.get('login_type', '').lower() != 'farmer':
        return jsonify({'success': False, 'message': 'Only farmers can access this'}), 403
    
    farmer_username = session.get('username')
    
    # Load products from JSON file
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            products_list = json_data.get('products', []) if isinstance(json_data, dict) else json_data
            
        products = []
        for p in products_list:
            if p.get('seller_username') == farmer_username and p.get('seller_type') == 'farmer':
                products.append({
                    'product_id': p['id'],
                    'name': p['name'],
                    'category': p['category'],
                    'price': p['price'],
                    'stock': p['stock'],
                    'unit': p.get('unit', ''),
                    'image': p.get('image', ''),
                    'description': p.get('description', ''),
                    'created_at': p.get('created_at', '')
                })
        
        return jsonify({
            'success': True,
            'products': products
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading products: {str(e)}'}), 500

@app.route('/api/farmer/update-product/<product_id>', methods=['PUT'])
def farmer_update_product(product_id):
    """Update farmer's product"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user = get_user_details(session.get('username'))
    if not user or user.get('login_type', '').lower() != 'farmer':
        return jsonify({'success': False, 'message': 'Only farmers can update products'}), 403
    
    try:
        data = request.get_json()
        farmer_username = session.get('username')
        
        # Update product in products.json
        json_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        products_list = json_data.get('products', []) if isinstance(json_data, dict) else json_data
        
        # Find and update the product
        product_found = False
        for p in products_list:
            if p.get('id') == product_id and p.get('seller_username') == farmer_username and p.get('seller_type') == 'farmer':
                if 'name' in data:
                    p['name'] = data['name']
                if 'category' in data:
                    p['category'] = data['category']
                if 'price' in data:
                    p['price'] = float(data['price'])
                if 'stock' in data:
                    p['stock'] = int(data['stock'])
                if 'unit' in data:
                    p['unit'] = data['unit']
                if 'image' in data:
                    p['image'] = data['image']
                if 'description' in data:
                    p['description'] = data['description']
                product_found = True
                break
        
        if not product_found:
            return jsonify({'success': False, 'message': 'Product not found or unauthorized'}), 404
        
        # Write back to file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        
        return jsonify({'success': True, 'message': 'Product updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/farmer/delete-product/<product_id>', methods=['DELETE'])
def farmer_delete_product(product_id):
    """Delete farmer's product"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user = get_user_details(session.get('username'))
    if not user or user.get('login_type', '').lower() != 'farmer':
        return jsonify({'success': False, 'message': 'Only farmers can delete products'}), 403
    
    try:
        farmer_username = session.get('username')
        
        # Delete product from products.json
        json_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        products_list = json_data.get('products', []) if isinstance(json_data, dict) else json_data
        
        # Find and remove the product
        product_found = False
        for i, p in enumerate(products_list):
            if p.get('id') == product_id and p.get('seller_username') == farmer_username and p.get('seller_type') == 'farmer':
                products_list.pop(i)
                product_found = True
                break
        
        if not product_found:
            return jsonify({'success': False, 'message': 'Product not found or unauthorized'}), 404
        
        # Write back to file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/products-by-category', methods=['GET'])
def get_products_by_category():
    """Get all farmer products grouped by category"""
    try:
        # Load products from JSON file
        data_path = os.path.join(os.path.dirname(__file__), 'products.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            products_list = json_data.get('products', []) if isinstance(json_data, dict) else json_data
        
        products_by_category = {}
        for p in products_list:
            if p.get('seller_type') == 'farmer' and p.get('stock', 0) > 0:
                category = p['category']
                if category not in products_by_category:
                    products_by_category[category] = []
                
                # Get farmer name from user details
                farmer_name = p.get('seller_username')  # Default to username
                try:
                    user = get_user_details(p.get('seller_username'))
                    if user and user.get('name'):
                        farmer_name = user['name']
                except:
                    pass
                
                products_by_category[category].append({
                    'product_id': p['id'],
                    'name': p['name'],
                    'price': p['price'],
                    'stock': p['stock'],
                    'unit': p.get('unit', ''),
                    'image': p.get('image', ''),
                    'description': p.get('description', ''),
                    'farmer_username': p.get('seller_username'),
                    'farmer_name': farmer_name
                })
        
        return jsonify({
            'success': True,
            'products_by_category': products_by_category
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading products: {str(e)}'}), 500

@app.route('/api/farmer/notifications', methods=['GET'])
def get_farmer_notifications():
    """Get notifications for farmer about orders"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user = get_user_details(session.get('username'))
    if not user or user.get('login_type', '').lower() != 'farmer':
        return jsonify({'success': False, 'message': 'Only farmers can access this'}), 403
    
    farmer_username = session.get('username')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Add index on farmer_username for faster lookups if not exists
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_farmer_notifications ON farmer_order_notifications(farmer_username)")
    except:
        pass
    
    cur.execute(
        """SELECT id, order_id, product_id, product_name, quantity, customer_username, 
                  customer_name, status, read_status, created_at, price
           FROM farmer_order_notifications
           WHERE farmer_username = ?
           ORDER BY created_at DESC""",
        (farmer_username,)
    )
    
    notifications = []
    for row in cur.fetchall():
        notifications.append({
            'id': row['id'],
            'order_id': row['order_id'],
            'product_id': row['product_id'],
            'product_name': row['product_name'],
            'quantity': row['quantity'],
            'customer_username': row['customer_username'],
            'customer_name': row['customer_name'],
            'status': row['status'],
            'read_status': row['read_status'],
            'created_at': row['created_at'],
            'price': row['price'] or 0
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'notifications': notifications
    })

@app.route('/api/farmer/mark-notification-read/<int:notification_id>', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark farmer notification as read"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user = get_user_details(session.get('username'))
    if not user or user.get('login_type', '').lower() != 'farmer':
        return jsonify({'success': False, 'message': 'Only farmers can access this'}), 403
    
    try:
        farmer_username = session.get('username')
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute(
            'UPDATE farmer_order_notifications SET read_status = 1 WHERE id = ? AND farmer_username = ?',
            (notification_id, farmer_username)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/farmer/clear-notifications', methods=['DELETE'])
def clear_farmer_notifications():
    """Delete all notifications for the logged-in farmer"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user = get_user_details(session.get('username'))
    if not user or user.get('login_type', '').lower() != 'farmer':
        return jsonify({'success': False, 'message': 'Only farmers can access this'}), 403
    
    try:
        farmer_username = session.get('username')
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('DELETE FROM farmer_order_notifications WHERE farmer_username = ?', (farmer_username,))
        deleted = cur.rowcount or 0
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============== FARMER COMMUNITY SOCIAL MEDIA ==============

# Configure upload folder for community images
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/community.html')
def community():
    """Render community page for farmers"""
    user = get_user_details(session.get('username')) if session.get('username') else None
    return render_template('community.html', user=user)

@app.route('/api/community/posts', methods=['GET'])
def get_community_posts():
    """Fetch all community posts with replies"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Get all posts with user details
        cur.execute('''
            SELECT cp.id, cp.username, cp.title, cp.content, cp.image_path, cp.created_at,
                   ud.name as author_name
            FROM community_posts cp
            LEFT JOIN user_details ud ON cp.username = ud.username
            ORDER BY cp.id DESC
        ''')
        posts_data = cur.fetchall()
        
        posts = []
        for post in posts_data:
            post_id = post[0]
            
            # Get replies for this post
            cur.execute('''
                SELECT cr.id, cr.username, cr.content, cr.created_at,
                       ud.name as author_name
                FROM community_replies cr
                LEFT JOIN user_details ud ON cr.username = ud.username
                WHERE cr.post_id = ?
                ORDER BY cr.id ASC
            ''', (post_id,))
            replies_data = cur.fetchall()
            
            replies = [{
                'id': r[0],
                'username': r[1],
                'content': r[2],
                'created_at': r[3],
                'author_name': r[4] or r[1]
            } for r in replies_data]
            
            posts.append({
                'id': post[0],
                'username': post[1],
                'title': post[2],
                'content': post[3],
                'image_path': post[4],
                'created_at': post[5],
                'author_name': post[6] or post[1],
                'replies': replies,
                'reply_count': len(replies)
            })
        
        conn.close()
        return jsonify({'success': True, 'posts': posts})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/community/posts', methods=['POST'])
def create_community_post():
    """Create a new community post"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login to post'}), 401
    
    try:
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            return jsonify({'success': False, 'message': 'Title and content are required'}), 400
        
        username = session.get('username')
        date_str, time_str = get_current_time()
        created_at = f"{date_str} {time_str}"
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                # Generate unique filename
                import uuid
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                image_path = f"/static/uploads/{filename}"
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute(
            '''INSERT INTO community_posts (username, title, content, image_path, created_at)
               VALUES (?, ?, ?, ?, ?)''',
            (username, title, content, image_path, created_at)
        )
        
        post_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Post created successfully!',
            'post_id': post_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/community/posts/<int:post_id>/replies', methods=['POST'])
def add_community_reply(post_id):
    """Add a reply/solution to a community post"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login to reply'}), 401
    
    try:
        data = request.json
        content = (data.get('content') or '').strip()
        
        if not content:
            return jsonify({'success': False, 'message': 'Reply content is required'}), 400
        
        username = session.get('username')
        date_str, time_str = get_current_time()
        created_at = f"{date_str} {time_str}"
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Verify post exists
        cur.execute('SELECT id FROM community_posts WHERE id = ?', (post_id,))
        if not cur.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Post not found'}), 404
        
        cur.execute(
            '''INSERT INTO community_replies (post_id, username, content, created_at)
               VALUES (?, ?, ?, ?)''',
            (post_id, username, content, created_at)
        )
        
        reply_id = cur.lastrowid
        conn.commit()
        
        # Get author name for response
        cur.execute('SELECT name FROM user_details WHERE username = ?', (username,))
        name_row = cur.fetchone()
        author_name = name_row[0] if name_row else username
        
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Reply added successfully!',
            'reply': {
                'id': reply_id,
                'username': username,
                'content': content,
                'created_at': created_at,
                'author_name': author_name
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/community/posts/<int:post_id>', methods=['DELETE'])
def delete_community_post(post_id):
    """Delete a community post (only by author)"""
    if not session.get('username'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        username = session.get('username')
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Verify ownership
        cur.execute('SELECT username, image_path FROM community_posts WHERE id = ?', (post_id,))
        post = cur.fetchone()
        
        if not post:
            conn.close()
            return jsonify({'success': False, 'message': 'Post not found'}), 404
        
        if post[0] != username:
            conn.close()
            return jsonify({'success': False, 'message': 'You can only delete your own posts'}), 403
        
        # Delete image file if exists
        if post[1]:
            image_file = os.path.join(os.path.dirname(__file__), post[1].lstrip('/'))
            if os.path.exists(image_file):
                os.remove(image_file)
        
        # Delete replies first
        cur.execute('DELETE FROM community_replies WHERE post_id = ?', (post_id,))
        # Delete post
        cur.execute('DELETE FROM community_posts WHERE id = ?', (post_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Post deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    init_db()  # Initialize database first
    initialize_Farmers_notifications()  # Then initialize notifications
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

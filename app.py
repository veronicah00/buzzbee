"""
Buzz Bee Naturals - Backend Server
Handles orders, database management, and WhatsApp notifications
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime
import sqlite3
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Database and notification configuration
DB_PATH = 'buzzbee_orders.db'
ADMIN_PHONE = os.getenv('ADMIN_PHONE', '254735754185')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize database
def init_db():
    """Initialize SQLite database with orders table"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  location TEXT NOT NULL,
                  product TEXT NOT NULL,
                  quantity INTEGER NOT NULL,
                  delivery_option TEXT NOT NULL DEFAULT 'Pickup - Nairobi CBD',
                  delivery_date TEXT NOT NULL,
                  message TEXT,
                  status TEXT DEFAULT 'pending',
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  notification_sent BOOLEAN DEFAULT 0)''')

    c.execute('PRAGMA table_info(orders)')
    columns = [row[1] for row in c.fetchall()]
    if 'delivery_option' not in columns:
        c.execute('ALTER TABLE orders ADD COLUMN delivery_option TEXT NOT NULL DEFAULT "Pickup - Nairobi CBD"')
    if 'notification_sent' not in columns:
        c.execute('ALTER TABLE orders ADD COLUMN notification_sent BOOLEAN DEFAULT 0')

    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  price REAL NOT NULL,
                  description TEXT,
                  available BOOLEAN DEFAULT 1)''')

    conn.commit()
    conn.close()

def add_default_products():
    """Add default products if not exist"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    products = [
        ("Raw Honey - 500ml", 1500, "Pure, unfiltered raw honey"),
        ("Organic Wildflower Honey - 500ml", 1800, "Premium organic wildflower honey"),
        ("Honey Combo Pack", 3500, "Assorted honey products"),
        ("Premium Gift Box", 4500, "Luxury gift packaged honey")
    ]

    for product in products:
        try:
            c.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)", product)
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

def normalize_phone(phone_number):
    phone = str(phone_number).strip()
    if phone.startswith('+'):
        return phone
    if phone.startswith('0') and len(phone) == 10:
        return f'+254{phone[1:]}'
    return f'+{phone}'


def send_sms_message(phone_number, message):
    """Send SMS notification via Twilio if configured, otherwise log message."""
    normalized_phone = normalize_phone(phone_number)
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        try:
            payload = {
                'From': TWILIO_PHONE_NUMBER,
                'To': normalized_phone,
                'Body': message
            }
            response = requests.post(
                f'https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json',
                data=payload,
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending SMS via Twilio: {e}")
            print(f"SMS message to {normalized_phone}: {message}")
            return False
    else:
        print(f"SMS message to {normalized_phone}: {message}")
        return False

@app.route('/')
def index():
    """Serve index.html"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

@app.route('/api/order', methods=['POST'])
def create_order():
    """Create a new order and send WhatsApp notification"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'location', 'product', 'quantity', 'deliveryOption', 'deliveryDate']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Store order in database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('''INSERT INTO orders
                     (name, email, phone, location, product, quantity, delivery_option, delivery_date, message)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (data['name'], data['email'], data['phone'], data['location'],
                  data['product'], data['quantity'], data['deliveryOption'], data['deliveryDate'], data.get('message', '')))

        order_id = c.lastrowid
        conn.commit()
        conn.close()

        delivery_option_text = data['deliveryOption']
        delivery_note = 'Please collect your order from Nairobi CBD.' if 'Pickup' in delivery_option_text else 'Doorstep delivery fee applies. We will arrange Uber or Bolt boda.'

        customer_message = f"""Hello {data['name']}, your order has been received!\n
Order Details:
- Order ID: {order_id}
- Product: {data['product']}
- Quantity: {data['quantity']}
- Delivery Option: {delivery_option_text}
- Delivery Date: {data['deliveryDate']}
- Location: {data['location']}
\n{delivery_note}\n\nWe'll confirm your order shortly. Thank you for choosing Buzz Bee Naturals!"""

        admin_message = f"""New Order Received!\n
Customer: {data['name']}
Phone: {data['phone']}
Email: {data['email']}
Location: {data['location']}
Product: {data['product']}
Quantity: {data['quantity']}
Delivery Option: {delivery_option_text}
Delivery Date: {data['deliveryDate']}
Message: {data.get('message', 'N/A')}

Order ID: {order_id}"""

        # Send notifications
        send_sms_message(data['phone'], customer_message)
        send_sms_message(ADMIN_PHONE, admin_message)

        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order_id': order_id
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders (with basic auth in production)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM orders ORDER BY timestamp DESC')

        columns = [description[0] for description in c.description]
        orders = [dict(zip(columns, row)) for row in c.fetchall()]

        conn.close()
        return jsonify(orders), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a specific order"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM orders WHERE id = ?', (order_id,))

        row = c.fetchone()
        conn.close()

        if row:
            columns = [description[0] for description in c.description]
            order = dict(zip(columns, row))
            return jsonify(order), 200
        else:
            return jsonify({'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.get_json()
        new_status = data.get('status', '')

        if new_status not in ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']:
            return jsonify({'error': 'Invalid status'}), 400

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Order status updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all available products"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM products WHERE available = 1')

        columns = [description[0] for description in c.description]
        products = [dict(zip(columns, row)) for row in c.fetchall()]

        conn.close()
        return jsonify(products), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get order statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('SELECT COUNT(*) FROM orders')
        total_orders = c.fetchone()[0]

        c.execute('SELECT COUNT(*) FROM orders WHERE status = "confirmed"')
        confirmed = c.fetchone()[0]

        c.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
        pending = c.fetchone()[0]

        conn.close()

        return jsonify({
            'total_orders': total_orders,
            'confirmed': confirmed,
            'pending': pending
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Initialize database on import so this works whether the app is started
# with `python app.py` (development) or with gunicorn (production on Render).
# The old code only called these inside `if __name__ == '__main__':`, which
# never runs under gunicorn -- so the `orders` table was never created,
# and every order submission failed with "no such table: orders".
init_db()
add_default_products()

if __name__ == '__main__':
    # Run server (use env vars for production hosting)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() in ('1', 'true', 'yes')
    app.run(debug=debug, host='0.0.0.0', port=port)
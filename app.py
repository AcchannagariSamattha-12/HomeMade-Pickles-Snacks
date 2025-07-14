from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import boto3
import os
import uuid
from dotenv import load_dotenv
import signal
import sys

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

# DynamoDB setup
aws_region = os.getenv('AWS_REGION_NAME')
dynamodb = boto3.resource('dynamodb', region_name=aws_region)
users_table = dynamodb.Table(os.getenv('USERS_TABLE_NAME'))
orders_table = dynamodb.Table(os.getenv('ORDERS_TABLE_NAME'))

@app.context_processor
def inject_globals():
    cart = session.get('cart', [])
    return {
        'now': datetime.now(),
        'cart_count': sum(item['quantity'] for item in cart)
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        response = users_table.get_item(Key={'Email': email})
        if 'Item' in response:
            flash('Email already registered.', 'error')
        else:
            users_table.put_item(Item={'Email': email, 'username': username, 'password': password})
            flash('Registered successfully! Please login.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        response = users_table.get_item(Key={'Email': email})
        user = response.get('Item')

        if user and check_password_hash(user['password'], password_input):
            session['user'] = user['username']
            session['email'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('veg_pickles'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('email', None)
    session.pop('cart', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/veg_pickles')
def veg_pickles():
    session['last_category'] = 'veg_pickles'
    return render_template('veg_pickles.html')

@app.route('/non_veg_pickles')
def non_veg_pickles():
    session['last_category'] = 'non_veg_pickles'
    return render_template('non_veg_pickles.html')

@app.route('/snacks')
def snacks():
    session['last_category'] = 'snacks'
    return render_template('snacks.html')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user' not in session:
        flash('Please log in to add items to your cart.', 'error')
        return redirect(url_for('login'))

    name = request.form['name']
    price = int(request.form['price'])
    quantity = int(request.form.get('quantity', 1))
    session.setdefault('cart', []).append({'name': name, 'price': price, 'quantity': quantity})
    flash('Item added to cart!', 'success')
    return redirect(url_for('cart_page'))

@app.route('/cart')
def cart_page():
    if 'user' not in session:
        flash('Please log in to view your cart.', 'error')
        return redirect(url_for('login'))

    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart_items=cart, total_amount=total)

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    name = request.form['item_name']
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item['name'] != name]
    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart_page'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        if 'email' not in session:
            flash('Please log in to place an order.', 'error')
            return redirect(url_for('login'))

        email = session['email']
        name = request.form.get('name', 'Customer')
        order_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        cart_items = session.get('cart', [])

        for item in cart_items:
            orders_table.put_item(
                Item={
                    'order_id': order_id,
                    'Email': email,
                    'name': name,
                    'item_name': item['name'],
                    'price': item['price'],
                    'quantity': item['quantity'],
                    'timestamp': timestamp
                }
            )

        session.pop('cart', None)
        flash("Order placed successfully!", 'success')
        return render_template('success.html', name=name, order_id=order_id, last_category=session.get('last_category', 'veg_pickles'))
    return render_template('checkout.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    name = request.form.get('name')
    message = request.form.get('message')

    print(f"[Contact Message] From: {name} | Message: {message}")
    flash("Thank you for your message! We'll get back to you soon.", 'info')
    return redirect(url_for('contact_us'))

@app.route('/send_email')
def send_email():
    msg = Message(
        subject='Test Email from Flask',
        sender=app.config['MAIL_USERNAME'],
        recipients=['your_real_email@example.com'],
        body='This is a test email sent using Flask-Mail via Gmail SMTP.'
    )
    mail.send(msg)
    return 'Email sent successfully!'

# Graceful exit handler
def handle_exit(sig, frame):
    print("\nExiting Flask app gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

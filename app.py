from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Simulated in-memory user database
users_db = {}

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_real_email@gmail.com'  # Replace this
app.config['MAIL_PASSWORD'] = 'your_generated_app_password'  # Replace this

mail = Mail(app)

# Inject current time and cart count into all templates
@app.context_processor
def inject_globals():
    cart = session.get('cart', [])
    return {
        'now': datetime.now(),
        'cart_count': sum(item['quantity'] for item in cart)
    }

# Home
@app.route('/')
def home():
    return render_template('index.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if email in users_db:
            flash('Email already registered.', 'error')
        else:
            users_db[email] = {'username': username, 'password': password}
            flash('Registered successfully! Please login.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']
        user = users_db.get(email)

        if user and check_password_hash(user['password'], password_input):
            session['user'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('veg_pickles'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('cart', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

# Veg Pickles Page
@app.route('/veg_pickles')
def veg_pickles():
    session['last_category'] = 'veg_pickles'
    return render_template('veg_pickles.html')

# Non-Veg Pickles Page
@app.route('/non_veg_pickles')
def non_veg_pickles():
    session['last_category'] = 'non_veg_pickles'
    return render_template('non_veg_pickles.html')

# Snacks Page
@app.route('/snacks')
def snacks():
    session['last_category'] = 'snacks'
    return render_template('snacks.html')

# Add to Cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    name = request.form['name']
    price = int(request.form['price'])

    cart = session.get('cart', [])

    for item in cart:
        if item['name'] == name:
            item['quantity'] += 1
            break
    else:
        cart.append({'name': name, 'price': price, 'quantity': 1})

    session['cart'] = cart
    return redirect(url_for('cart_page'))

# View Cart
@app.route('/cart')
def cart_page():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart_items=cart, total_amount=total)

# Remove from Cart
@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    item_name = request.form['item_name']
    cart = session.get('cart', [])
    cart = [item for item in cart if item['name'] != item_name]
    session['cart'] = cart
    return redirect(url_for('cart_page'))

# Checkout Page
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form.get('name', 'Customer')
        order_id = datetime.now().strftime("%Y%m%d%H%M%S")
        last_category = session.get('last_category', 'veg_pickles')  # Default fallback
        session.pop('cart', None)
        return render_template('success.html', name=name, order_id=order_id, last_category=last_category)
    return render_template('checkout.html')

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# Contact Us Page
@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')

# Handle contact form submission
@app.route('/send_message', methods=['POST'])
def send_message():
    name = request.form.get('name')
    message = request.form.get('message')

    print(f"[Contact Message] From: {name} | Message: {message}")
    flash("Thank you for your message! We'll get back to you soon.")
    return redirect(url_for('contact_us'))

# Optional test email route
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

if __name__ == '__main__':
    app.run(debug=True)

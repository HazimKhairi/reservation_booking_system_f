from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import bcrypt
import uuid
from datetime import datetime
from config import Config
from db import execute_query

app = Flask(__name__)
app.config.from_object(Config)


# ============== Decorators ==============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('patron_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def patron_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        if session.get('role') != 'patron':
            flash('Access denied.', 'error')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ============== Helper Functions ==============

def calculate_hours(start_time, end_time):
    start = datetime.strptime(str(start_time), '%H:%M:%S' if ':' in str(start_time) and str(start_time).count(':') == 2 else '%H:%M')
    end = datetime.strptime(str(end_time), '%H:%M:%S' if ':' in str(end_time) and str(end_time).count(':') == 2 else '%H:%M')
    diff = (end - start).seconds / 3600
    return max(diff, 1)


def generate_transaction_id():
    return f"TXN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


# ============== Authentication Routes ==============

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('patron_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = execute_query(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (username,),
            fetch_one=True
        )
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('patron_dashboard'))
        
        flash('Invalid username or password.', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        existing_user = execute_query(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email),
            fetch_one=True
        )
        
        if existing_user:
            flash('Username or email already exists. Please login instead.', 'error')
            return redirect(url_for('login'))
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        execute_query(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, 'patron')",
            (username, email, hashed_password.decode('utf-8'))
        )
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# ============== Admin Routes ==============

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_rooms = execute_query("SELECT COUNT(*) as count FROM rooms", fetch_one=True)['count']
    total_bookings = execute_query("SELECT COUNT(*) as count FROM reservations WHERE status = 'confirmed'", fetch_one=True)['count']
    total_patrons = execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'patron'", fetch_one=True)['count']
    maintenance_rooms = execute_query("SELECT COUNT(*) as count FROM rooms WHERE status = 'maintenance'", fetch_one=True)['count']
    
    return render_template('admin/dashboard.html', 
                         total_rooms=total_rooms,
                         total_bookings=total_bookings,
                         total_patrons=total_patrons,
                         maintenance_rooms=maintenance_rooms)


@app.route('/admin/rooms')
@admin_required
def admin_rooms():
    rooms = execute_query("SELECT * FROM rooms ORDER BY name", fetch_all=True)
    return render_template('admin/rooms.html', rooms=rooms)


@app.route('/admin/rooms/add', methods=['GET', 'POST'])
@admin_required
def admin_add_room():
    if request.method == 'POST':
        name = request.form.get('name')
        capacity = request.form.get('capacity')
        equipment = request.form.get('equipment')
        price_per_hour = request.form.get('price_per_hour', 10.00)
        status = request.form.get('status')
        
        execute_query(
            "INSERT INTO rooms (name, capacity, equipment, price_per_hour, status) VALUES (%s, %s, %s, %s, %s)",
            (name, capacity, equipment, price_per_hour, status)
        )
        
        flash('Room added successfully!', 'success')
        return redirect(url_for('admin_rooms'))
    
    return render_template('admin/add_room.html')


@app.route('/admin/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_room(room_id):
    if request.method == 'POST':
        name = request.form.get('name')
        capacity = request.form.get('capacity')
        equipment = request.form.get('equipment')
        price_per_hour = request.form.get('price_per_hour', 10.00)
        status = request.form.get('status')
        
        execute_query(
            "UPDATE rooms SET name = %s, capacity = %s, equipment = %s, price_per_hour = %s, status = %s WHERE id = %s",
            (name, capacity, equipment, price_per_hour, status, room_id)
        )
        
        flash('Room updated successfully!', 'success')
        return redirect(url_for('admin_rooms'))
    
    room = execute_query("SELECT * FROM rooms WHERE id = %s", (room_id,), fetch_one=True)
    if not room:
        flash('Room not found.', 'error')
        return redirect(url_for('admin_rooms'))
    
    return render_template('admin/edit_room.html', room=room)


@app.route('/admin/rooms/delete/<int:room_id>')
@admin_required
def admin_delete_room(room_id):
    execute_query("DELETE FROM rooms WHERE id = %s", (room_id,))
    flash('Room deleted successfully!', 'success')
    return redirect(url_for('admin_rooms'))


@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    bookings = execute_query("""
        SELECT r.id, r.reservation_date, r.start_time, r.end_time, r.status,
               rm.name as room_name, u.username
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        JOIN users u ON r.user_id = u.id
        ORDER BY r.reservation_date DESC, r.start_time
    """, fetch_all=True)
    return render_template('admin/bookings.html', bookings=bookings)


@app.route('/admin/payments')
@admin_required
def admin_payments():
    payments = execute_query("""
        SELECT p.*, u.username, r.reservation_date, rm.name as room_name
        FROM payments p
        JOIN users u ON p.user_id = u.id
        JOIN reservations r ON p.reservation_id = r.id
        JOIN rooms rm ON r.room_id = rm.id
        ORDER BY p.created_at DESC
    """, fetch_all=True)
    return render_template('admin/payments.html', payments=payments)


# ============== Patron Routes ==============

@app.route('/patron/dashboard')
@patron_required
def patron_dashboard():
    upcoming_bookings = execute_query("""
        SELECT r.id, r.reservation_date, r.start_time, r.end_time, rm.name as room_name
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        WHERE r.user_id = %s AND r.status = 'confirmed' AND r.reservation_date >= CURDATE()
        ORDER BY r.reservation_date, r.start_time
        LIMIT 5
    """, (session['user_id'],), fetch_all=True)
    
    total_bookings = execute_query(
        "SELECT COUNT(*) as count FROM reservations WHERE user_id = %s AND status = 'confirmed'",
        (session['user_id'],),
        fetch_one=True
    )['count']
    
    return render_template('patron/dashboard.html', 
                         upcoming_bookings=upcoming_bookings,
                         total_bookings=total_bookings)


@app.route('/patron/rooms')
@patron_required
def patron_rooms():
    rooms = execute_query("SELECT * FROM rooms WHERE status = 'available' ORDER BY name", fetch_all=True)
    return render_template('patron/rooms.html', rooms=rooms)


@app.route('/patron/book/<int:room_id>', methods=['GET', 'POST'])
@patron_required
def patron_book_room(room_id):
    room = execute_query("SELECT * FROM rooms WHERE id = %s AND status = 'available'", (room_id,), fetch_one=True)
    
    if not room:
        flash('Room not available.', 'error')
        return redirect(url_for('patron_rooms'))
    
    if request.method == 'POST':
        reservation_date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        
        conflict = execute_query("""
            SELECT COUNT(*) as count FROM reservations 
            WHERE room_id = %s 
              AND reservation_date = %s 
              AND status IN ('pending', 'confirmed')
              AND ((start_time < %s AND end_time > %s) 
                OR (start_time < %s AND end_time > %s)
                OR (start_time >= %s AND end_time <= %s))
        """, (room_id, reservation_date, end_time, start_time, end_time, start_time, start_time, end_time), fetch_one=True)
        
        if conflict['count'] > 0:
            flash('This time slot is already booked. Please choose a different time.', 'error')
            return render_template('patron/booking.html', room=room)
        
        # Create pending reservation
        reservation_id = execute_query(
            "INSERT INTO reservations (room_id, user_id, reservation_date, start_time, end_time, status) VALUES (%s, %s, %s, %s, %s, 'pending')",
            (room_id, session['user_id'], reservation_date, start_time, end_time)
        )
        
        # Redirect to checkout
        return redirect(url_for('patron_checkout', reservation_id=reservation_id))
    
    return render_template('patron/booking.html', room=room)


@app.route('/patron/checkout/<int:reservation_id>', methods=['GET', 'POST'])
@patron_required
def patron_checkout(reservation_id):
    reservation = execute_query("""
        SELECT r.*, rm.name as room_name, rm.capacity, rm.equipment, rm.price_per_hour
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        WHERE r.id = %s AND r.user_id = %s AND r.status = 'pending'
    """, (reservation_id, session['user_id']), fetch_one=True)
    
    if not reservation:
        flash('Reservation not found or already processed.', 'error')
        return redirect(url_for('patron_my_bookings'))
    
    # Calculate total
    hours = calculate_hours(reservation['start_time'], reservation['end_time'])
    total_amount = float(reservation['price_per_hour']) * hours
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        bank_name = request.form.get('bank_name')
        account_number = request.form.get('account_number')
        account_holder = request.form.get('account_holder')

        try:
            # Generate transaction ID
            transaction_id = generate_transaction_id()

            # Create payment record
            payment_id = execute_query("""
                INSERT INTO payments (reservation_id, user_id, amount, payment_method,
                                     bank_name, account_number, account_holder, transaction_id, status, paid_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'completed', NOW())
            """, (reservation_id, session['user_id'], total_amount, payment_method,
                  bank_name, account_number, account_holder, transaction_id))

            # Update reservation to confirmed
            execute_query(
                "UPDATE reservations SET status = 'confirmed' WHERE id = %s",
                (reservation_id,)
            )

            # Update user bank details
            execute_query("""
                UPDATE users SET bank_name = %s, bank_account_number = %s, bank_account_holder = %s
                WHERE id = %s
            """, (bank_name, account_number, account_holder, session['user_id']))

            flash('Payment successful! Your booking is confirmed.', 'success')
            return redirect(url_for('patron_receipt', payment_id=payment_id))
        except Exception as e:
            print(f"Payment error: {e}")
            flash('Payment processing failed. Please try again.', 'error')
            return redirect(url_for('patron_my_bookings'))
    
    # Get user's saved bank details
    user = execute_query(
        "SELECT bank_name, bank_account_number, bank_account_holder FROM users WHERE id = %s",
        (session['user_id'],),
        fetch_one=True
    )
    
    return render_template('patron/checkout.html', 
                         reservation=reservation, 
                         hours=hours, 
                         total_amount=total_amount,
                         user=user)


@app.route('/patron/receipt/<int:payment_id>')
@patron_required
def patron_receipt(payment_id):
    payment = execute_query("""
        SELECT p.*, u.username, u.email,
               r.reservation_date, r.start_time, r.end_time,
               rm.name as room_name, rm.capacity, rm.equipment, rm.price_per_hour
        FROM payments p
        JOIN users u ON p.user_id = u.id
        JOIN reservations r ON p.reservation_id = r.id
        JOIN rooms rm ON r.room_id = rm.id
        WHERE p.id = %s AND p.user_id = %s
    """, (payment_id, session['user_id']), fetch_one=True)
    
    if not payment:
        flash('Receipt not found.', 'error')
        return redirect(url_for('patron_my_bookings'))
    
    hours = calculate_hours(payment['start_time'], payment['end_time'])
    
    return render_template('patron/receipt.html', payment=payment, hours=hours)


@app.route('/patron/my-bookings')
@patron_required
def patron_my_bookings():
    bookings = execute_query("""
        SELECT r.id, r.reservation_date, r.start_time, r.end_time, r.status,
               rm.name as room_name, rm.capacity,
               p.id as payment_id, p.transaction_id
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        LEFT JOIN payments p ON r.id = p.reservation_id
        WHERE r.user_id = %s
        ORDER BY r.reservation_date DESC, r.start_time
    """, (session['user_id'],), fetch_all=True)
    return render_template('patron/my_bookings.html', bookings=bookings)


@app.route('/patron/cancel/<int:booking_id>')
@patron_required
def patron_cancel_booking(booking_id):
    booking = execute_query(
        "SELECT * FROM reservations WHERE id = %s AND user_id = %s",
        (booking_id, session['user_id']),
        fetch_one=True
    )
    
    if not booking:
        flash('Booking not found.', 'error')
        return redirect(url_for('patron_my_bookings'))
    
    execute_query(
        "UPDATE reservations SET status = 'cancelled' WHERE id = %s",
        (booking_id,)
    )
    
    # Update payment status if exists
    execute_query(
        "UPDATE payments SET status = 'refunded' WHERE reservation_id = %s",
        (booking_id,)
    )
    
    flash('Booking cancelled successfully!', 'success')
    return redirect(url_for('patron_my_bookings'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)


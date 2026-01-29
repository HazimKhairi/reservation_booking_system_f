"""
Library Room Reservation System - Flask Web Application
Integrates with SQLite database (reservation_system.db)
Supports both Patron and Admin roles
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime, date, timedelta
import pytz
import bcrypt
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this!

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "reservation_system.db")

# ================= DATABASE =================
def connect_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_malaysia_time():
    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    return datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")

# ================= AUTHENTICATION =================
@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin' or session.get('role') == 'librarian':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('patron_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()
        
        if user:
            stored_password = user['password']
            # Check if password is hashed (bcrypt) or plain text
            if stored_password.startswith('$2b$'):
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['name'] = user['name']
                    
                    if user['role'] in ['admin', 'librarian']:
                        return redirect(url_for('admin_dashboard'))
                    else:
                        return redirect(url_for('patron_dashboard'))
            else:
                # Plain text password (backward compatibility)
                if password == stored_password:
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['name'] = user['name']
                    
                    if user['role'] in ['admin', 'librarian']:
                        return redirect(url_for('admin_dashboard'))
                    else:
                        return redirect(url_for('patron_dashboard'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name', username)
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        conn = connect_db()
        cur = conn.cursor()
        
        # Check if username or email exists
        cur.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email))
        if cur.fetchone():
            flash('Username or email already exists', 'error')
            conn.close()
            return render_template('register.html')
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        now = get_malaysia_time()
        
        try:
            cur.execute("""
                INSERT INTO users (name, student_id, faculty, email, username, password, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'student', ?, ?)
            """, (name, '', '', email, username, hashed_password.decode('utf-8'), now, now))
            
            user_id = cur.lastrowid
            cur.execute("INSERT INTO bank VALUES (?, 0)", (user_id,))
            cur.execute("INSERT INTO user_bank_acc VALUES (?, 1000)", (user_id,))
            
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# ================= PATRON ROUTES =================
@app.route('/patron/dashboard')
def patron_dashboard():
    if 'user_id' not in session or session.get('role') not in ['student', 'patron']:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Get total bookings count
    cur.execute("SELECT COUNT(*) as total FROM reservations WHERE user_id = ?", (session['user_id'],))
    total_bookings = cur.fetchone()['total']
    
    # Get upcoming bookings
    cur.execute("""
        SELECT r.*, rm.room_name, rm.price_per_hour
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        WHERE r.user_id = ? AND r.status IN ('Confirmed', 'Pending')
        ORDER BY r.date DESC, r.start_time DESC
        LIMIT 5
    """, (session['user_id'],))
    upcoming_bookings = cur.fetchall()
    
    # Get balance
    cur.execute("SELECT balance FROM bank WHERE user_id=?", (session['user_id'],))
    balance_row = cur.fetchone()
    balance = balance_row['balance'] if balance_row else 0
    
    conn.close()
    
    return render_template('patron/dashboard.html', 
                         total_bookings=total_bookings,
                         upcoming_bookings=upcoming_bookings, 
                         balance=balance)

@app.route('/patron/rooms')
def patron_rooms():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM rooms WHERE status='available' ORDER BY room_name")
    rooms = cur.fetchall()
    conn.close()
    
    return render_template('patron/rooms.html', rooms=rooms)

@app.route('/patron/book/<int:room_id>', methods=['GET', 'POST'])
def patron_book_room(room_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    if request.method == 'POST':
        booking_date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        num_people = request.form.get('num_people', 1)
        
        # Get room details
        cur.execute("SELECT * FROM rooms WHERE id=?", (room_id,))
        room = cur.fetchone()
        
        # Calculate cost
        time_slots = [
            "08:00 AM","09:00 AM","10:00 AM","11:00 AM",
            "12:00 PM","01:00 PM","02:00 PM","03:00 PM",
            "04:00 PM","05:00 PM","06:00 PM","07:00 PM","08:00 PM"
        ]
        start_idx = time_slots.index(start_time)
        end_idx = time_slots.index(end_time)
        hours = end_idx - start_idx
        total_cost = hours * room['price_per_hour']
        
        # Create reservation
        now = get_malaysia_time()
        cur.execute("""
            INSERT INTO reservations (user_id, room_id, date, start_time, end_time, num_people, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
        """, (session['user_id'], room_id, booking_date, start_time, end_time, num_people, now, now))
        
        reservation_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # Redirect to checkout
        return redirect(url_for('patron_checkout', reservation_id=reservation_id))
    
    # GET request - show booking form
    cur.execute("SELECT * FROM rooms WHERE id=?", (room_id,))
    room = cur.fetchone()
    conn.close()
    
    return render_template('patron/booking.html', room=room)

@app.route('/patron/checkout/<int:reservation_id>', methods=['GET', 'POST'])
def patron_checkout(reservation_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Get reservation details
    cur.execute("""
        SELECT r.*, rm.room_name, rm.price_per_hour
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        WHERE r.id = ? AND r.user_id = ?
    """, (reservation_id, session['user_id']))
    reservation = cur.fetchone()
    
    if not reservation:
        flash('Reservation not found', 'error')
        conn.close()
        return redirect(url_for('patron_dashboard'))
    
    # Calculate cost
    time_slots = [
        "08:00 AM","09:00 AM","10:00 AM","11:00 AM",
        "12:00 PM","01:00 PM","02:00 PM","03:00 PM",
        "04:00 PM","05:00 PM","06:00 PM","07:00 PM","08:00 PM"
    ]
    start_idx = time_slots.index(reservation['start_time'])
    end_idx = time_slots.index(reservation['end_time'])
    hours = end_idx - start_idx
    total_cost = hours * reservation['price_per_hour']
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        bank_name = request.form.get('bank_name')
        account_number = request.form.get('account_number')
        account_holder = request.form.get('account_holder')
        
        # Generate transaction ID
        transaction_id = f"TXN-{int(time.time())}"
        now = get_malaysia_time()
        
        # Check balance if using system balance
        if payment_method == 'System Balance':
            cur.execute("SELECT balance FROM bank WHERE user_id=?", (session['user_id'],))
            balance = cur.fetchone()['balance']
            if balance < total_cost:
                flash('Insufficient balance', 'error')
                conn.close()
                return render_template('patron/checkout.html', reservation=reservation, total_cost=total_cost, hours=hours)
            
            # Deduct balance
            cur.execute("UPDATE bank SET balance = balance - ? WHERE user_id=?", (total_cost, session['user_id']))
        
        # Create payment record
        cur.execute("""
            INSERT INTO payments (
                reservation_id, user_id, amount, payment_method,
                bank_name, account_number, account_holder,
                transaction_id, status, paid_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?)
        """, (reservation_id, session['user_id'], total_cost, payment_method,
              bank_name, account_number, account_holder,
              transaction_id, now, now))
        
        # Update reservation status
        cur.execute("UPDATE reservations SET status='Confirmed' WHERE id=?", (reservation_id,))
        
        conn.commit()
        conn.close()
        
        flash('Payment successful! Booking confirmed.', 'success')
        return redirect(url_for('patron_receipt', reservation_id=reservation_id))
    
    conn.close()
    return render_template('patron/checkout.html', reservation=reservation, total_cost=total_cost, hours=hours)

@app.route('/patron/receipt/<int:reservation_id>')
def patron_receipt(reservation_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Get reservation and payment details
    cur.execute("""
        SELECT r.*, rm.room_name, rm.price_per_hour, p.transaction_id, p.amount, p.payment_method, p.paid_at
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        LEFT JOIN payments p ON p.reservation_id = r.id
        WHERE r.id = ? AND r.user_id = ?
    """, (reservation_id, session['user_id']))
    reservation = cur.fetchone()
    conn.close()
    
    if not reservation:
        flash('Reservation not found', 'error')
        return redirect(url_for('patron_dashboard'))
    
    return render_template('patron/receipt.html', reservation=reservation)

@app.route('/patron/my-bookings')
def patron_my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT r.*, rm.room_name, rm.price_per_hour
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        WHERE r.user_id = ?
        ORDER BY r.date DESC, r.start_time DESC
    """, (session['user_id'],))
    bookings = cur.fetchall()
    conn.close()
    
    return render_template('patron/my_bookings.html', bookings=bookings)

@app.route('/patron/edit-booking/<int:booking_id>', methods=['GET', 'POST'])
def patron_edit_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Get booking details
    cur.execute("""
        SELECT r.*, rm.room_name, rm.price_per_hour
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        WHERE r.id = ? AND r.user_id = ?
    """, (booking_id, session['user_id']))
    booking = cur.fetchone()
    
    if not booking:
        flash('Booking not found', 'error')
        conn.close()
        return redirect(url_for('patron_my_bookings'))
    
    if request.method == 'POST':
        new_date = request.form.get('date')
        new_start_time = request.form.get('start_time')
        new_end_time = request.form.get('end_time')
        
        now = get_malaysia_time()
        cur.execute("""
            UPDATE reservations 
            SET date=?, start_time=?, end_time=?, updated_at=?
            WHERE id=?
        """, (new_date, new_start_time, new_end_time, now, booking_id))
        
        conn.commit()
        conn.close()
        
        flash('Booking updated successfully', 'success')
        return redirect(url_for('patron_my_bookings'))
    
    conn.close()
    return render_template('patron/edit_booking.html', booking=booking)

@app.route('/patron/cancel-booking/<int:booking_id>', methods=['POST'])
def patron_cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Get booking details
    cur.execute("""
        SELECT r.*, p.amount, p.id as payment_id
        FROM reservations r
        LEFT JOIN payments p ON p.reservation_id = r.id
        WHERE r.id = ? AND r.user_id = ?
    """, (booking_id, session['user_id']))
    booking = cur.fetchone()
    
    if not booking:
        flash('Booking not found', 'error')
        conn.close()
        return redirect(url_for('patron_my_bookings'))
    
    # Refund if payment exists
    if booking['payment_id'] and booking['amount']:
        cur.execute("UPDATE bank SET balance = balance + ? WHERE user_id=?", 
                   (booking['amount'], session['user_id']))
        cur.execute("UPDATE payments SET status='refunded' WHERE id=?", 
                   (booking['payment_id'],))
        flash(f'Booking cancelled. Refund of {booking["amount"]} credits processed.', 'success')
    else:
        flash('Booking cancelled.', 'success')
    
    # Update reservation status
    now = get_malaysia_time()
    cur.execute("UPDATE reservations SET status='Cancelled', updated_at=? WHERE id=?", 
               (now, booking_id))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('patron_my_bookings'))

@app.route('/patron/delete-account', methods=['POST'])
def patron_delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    user_id = session['user_id']
    username = session.get('username', 'Unknown')
    
    # Log the deletion action before deleting the user
    now = get_malaysia_time()
    cur.execute("""
        INSERT INTO user_actions (user_id, action_type, details, date)
        VALUES (?, ?, ?, ?)
    """, (user_id, "Account Deletion", f"User '{username}' deleted their own account", now))
    
    # Hard delete user data
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    cur.execute("DELETE FROM bank WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM user_bank_acc WHERE user_id=?", (user_id,))
    
    conn.commit()
    conn.close()
    
    # Clear session
    session.clear()
    
    flash('Your account has been successfully deleted.', 'success')
    return redirect(url_for('login'))

# ================= ADMIN ROUTES =================
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') not in ['admin', 'librarian']:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Get statistics
    cur.execute("SELECT COUNT(*) as total FROM rooms")
    total_rooms = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM rooms WHERE status='available'")
    available_rooms = cur.fetchone()['total']
    
    cur.execute("SELECT status, COUNT(*) as count FROM reservations GROUP BY status")
    reservation_stats = cur.fetchall()
    
    cur.execute("SELECT SUM(amount) as total FROM payments WHERE status='completed'")
    total_revenue = cur.fetchone()['total'] or 0
    
    # Recent bookings
    cur.execute("""
        SELECT r.*, u.name, rm.room_name
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN rooms rm ON r.room_id = rm.id
        ORDER BY r.created_at DESC
        LIMIT 10
    """)
    recent_bookings = cur.fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         total_rooms=total_rooms,
                         available_rooms=available_rooms,
                         reservation_stats=reservation_stats,
                         total_revenue=total_revenue,
                         recent_bookings=recent_bookings)

@app.route('/admin/rooms')
def admin_rooms():
    if 'user_id' not in session or session.get('role') not in ['admin', 'librarian']:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM rooms ORDER BY room_name")
    rooms = cur.fetchall()
    conn.close()
    
    return render_template('admin/rooms.html', rooms=rooms)

@app.route('/admin/rooms/add', methods=['GET', 'POST'])
def admin_add_room():
    if 'user_id' not in session or session.get('role') not in ['admin', 'librarian']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        room_name = request.form.get('name')
        capacity = request.form.get('capacity')
        price_per_hour = request.form.get('price_per_hour', 10.0)
        
        conn = connect_db()
        cur = conn.cursor()
        now = get_malaysia_time()
        
        cur.execute("""
            INSERT INTO rooms (room_name, capacity, price_per_hour, status, created_at, updated_at)
            VALUES (?, ?, ?, 'available', ?, ?)
        """, (room_name, capacity, price_per_hour, now, now))
        
        conn.commit()
        conn.close()
        
        flash('Room added successfully', 'success')
        return redirect(url_for('admin_rooms'))
    
    return render_template('admin/add_room.html')

@app.route('/admin/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
def admin_edit_room(room_id):
    if 'user_id' not in session or session.get('role') not in ['admin', 'librarian']:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Get room details
    cur.execute("SELECT * FROM rooms WHERE id=?", (room_id,))
    room = cur.fetchone()
    
    if not room:
        flash('Room not found', 'error')
        conn.close()
        return redirect(url_for('admin_rooms'))
    
    if request.method == 'POST':
        room_name = request.form.get('name')
        capacity = request.form.get('capacity')
        price_per_hour = request.form.get('price_per_hour')
        status = request.form.get('status', 'available')
        
        now = get_malaysia_time()
        cur.execute("""
            UPDATE rooms 
            SET room_name=?, capacity=?, price_per_hour=?, status=?, updated_at=?
            WHERE id=?
        """, (room_name, capacity, price_per_hour, status, now, room_id))
        
        conn.commit()
        conn.close()
        
        flash('Room updated successfully', 'success')
        return redirect(url_for('admin_rooms'))
    
    conn.close()
    return render_template('admin/edit_room.html', room=room)

@app.route('/admin/rooms/delete/<int:room_id>', methods=['POST'])
def admin_delete_room(room_id):
    if 'user_id' not in session or session.get('role') not in ['admin', 'librarian']:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Delete related records first (cascade)
    cur.execute("DELETE FROM reservation_equipment WHERE reservation_id IN (SELECT id FROM reservations WHERE room_id=?)", (room_id,))
    cur.execute("DELETE FROM payments WHERE reservation_id IN (SELECT id FROM reservations WHERE room_id=?)", (room_id,))
    cur.execute("DELETE FROM reservations WHERE room_id=?", (room_id,))
    cur.execute("DELETE FROM rooms WHERE id=?", (room_id,))
    
    conn.commit()
    conn.close()
    
    flash('Room deleted successfully', 'success')
    return redirect(url_for('admin_rooms'))

@app.route('/admin/bookings')
def admin_bookings():
    if 'user_id' not in session or session.get('role') not in ['admin', 'librarian']:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT r.*, u.name, u.student_id, rm.room_name
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN rooms rm ON r.room_id = rm.id
        ORDER BY r.date DESC, r.start_time DESC
    """)
    bookings = cur.fetchall()
    conn.close()
    
    return render_template('admin/bookings.html', bookings=bookings)

@app.route('/admin/payments')
def admin_payments():
    if 'user_id' not in session or session.get('role') not in ['admin', 'librarian']:
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.*, u.name, u.student_id, r.date, rm.room_name
        FROM payments p
        JOIN users u ON p.user_id = u.id
        JOIN reservations r ON p.reservation_id = r.id
        JOIN rooms rm ON r.room_id = rm.id
        ORDER BY p.paid_at DESC
    """)
    payments = cur.fetchall()
    conn.close()
    
    return render_template('admin/payments.html', payments=payments)

# ================= ERROR HANDLERS =================
@app.errorhandler(404)
def not_found(e):
    return render_template('login.html'), 404

@app.errorhandler(500)
def server_error(e):
    return "Internal Server Error", 500

# ================= RUN APP =================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)

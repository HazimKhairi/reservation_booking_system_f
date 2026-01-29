import sqlite3
import os
from datetime import datetime
import pytz
import bcrypt
import time
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "reservation_system.db")

# ================= DATABASE =================
def connect_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def setup_db():
    conn = connect_db()
    cur = conn.cursor()

    # Users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        student_id TEXT,
        faculty TEXT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # Bank / balance
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bank(
        user_id INTEGER UNIQUE,
        balance INTEGER DEFAULT 0
    )
    """)

    # Add this in setup_db() selepas table bank
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_bank_acc(
        user_id INTEGER UNIQUE,
        bank_balance INTEGER DEFAULT 1000
    )
    """)


    # Rooms
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT,
        capacity INTEGER
    )
    """)

    # Reservations (start & end time)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reservations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        room_id INTEGER,
        date TEXT,
        start_time TEXT,
        end_time TEXT,
        num_people INTEGER,
        status TEXT DEFAULT 'Active'

    )
    """)

    # Booking rules
    cur.execute("""
    CREATE TABLE IF NOT EXISTS booking_rules(
        id INTEGER PRIMARY KEY,
        max_active INTEGER
    )
    """)

    # Equipment
    cur.execute("""
    CREATE TABLE IF NOT EXISTS equipment(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER
    )
    """)

    # Reservation <-> Equipment
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reservation_equipment(
        reservation_id INTEGER,
        equipment_id INTEGER
    )
    """)

    # Transactions (Topup record)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bank_name TEXT,
        amount INTEGER,
        date TEXT,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS room_actions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER,
        action TEXT,
        date TEXT
    )
    """)

    # ================= USER ACTION LOG =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_actions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action_type TEXT,
        details TEXT,
        date TEXT
    )
    """)


    # Default booking rule
    cur.execute("SELECT * FROM booking_rules")
    if not cur.fetchone():
        cur.execute("INSERT INTO booking_rules VALUES (1,2)")

    # Default librarian
    cur.execute("SELECT * FROM users WHERE role='librarian'")
    if not cur.fetchone():
        cur.execute("""
        INSERT INTO users (name,student_id,faculty,username,password,role)
        VALUES ('Admin','-','Library','admin','admin123','librarian')
        """)
        admin_id = cur.lastrowid
        cur.execute("INSERT INTO bank VALUES (?,0)", (admin_id,))

    # Default equipment
    cur.execute("SELECT COUNT(*) FROM equipment")
    if cur.fetchone()[0]==0:
        equipments = [("Microphone",5),("Projector",10),("Speaker",7)]
        for e in equipments:
            cur.execute("INSERT INTO equipment (name,price) VALUES (?,?)", e)

    conn.commit()
    conn.close()

# ================= USER =================
def register():
    name = input("Name: ")
    student_id = input("Student ID: ")
    faculty = input("Faculty: ")
    email = input("Email: ")
    
    # Validate email format
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        print(" Invalid email format")
        return
    
    username = input("Username: ")
    password = input("Password: ")

    conn = connect_db()
    cur = conn.cursor()
    
    # Check if email already exists
    cur.execute("SELECT id FROM users WHERE email=?", (email,))
    if cur.fetchone():
        print(" Email already exists")
        conn.close()
        return
    
    try:
        # Hash password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Get current timestamp
        malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
        now = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute("""
        INSERT INTO users (name,student_id,faculty,email,username,password,role,created_at,updated_at)
        VALUES (?,?,?,?,?,?,'student',?,?)
        """,(name,student_id,faculty,email,username,hashed_password.decode('utf-8'),now,now))

        uid = cur.lastrowid  # dapatkan ID user baru
        cur.execute("INSERT INTO bank VALUES (?,0)", (uid,))  # system balance
        cur.execute("INSERT INTO user_bank_acc VALUES (?,1000)", (uid,))  # bank account

        conn.commit()
        print(" Registration successful. Bank account created with balance 1000.")
    except sqlite3.IntegrityError:
        print(" Username exists")
    conn.close()

def login():
    u = input("Username: ")
    p = input("Password: ")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (u,))
    user = cur.fetchone()
    
    if user:
        stored_password = user['password']
        # Check if password is hashed (bcrypt) or plain text
        if stored_password.startswith('$2b$'):
            # Bcrypt hashed password
            if bcrypt.checkpw(p.encode('utf-8'), stored_password.encode('utf-8')):
                conn.close()
                return user
        else:
            # Plain text password (backward compatibility)
            if p == stored_password:
                conn.close()
                return user
    
    conn.close()
    return None

# ================= STUDENT =================
def view_rooms(user=None, ai_suggestion=False, date=None, start_time=None, end_time=None):
    conn = connect_db()
    cur = conn.cursor()
    # Filter by status - only show available rooms
    cur.execute("SELECT * FROM rooms WHERE status='available'")
    rooms = cur.fetchall()
    for r in rooms:
        status = "Available"
        if date and start_time and end_time:
            # Check overlapping reservations (updated to use 'Confirmed' status)
            cur.execute("""
            SELECT * FROM reservations
            WHERE room_id=? AND date=? AND status IN ('Confirmed', 'Pending')
            AND NOT (end_time <= ? OR start_time >= ?)
            """, (r["id"], date, start_time, end_time))
            if cur.fetchone():
                status = "Not Available"

        # Show room with pricing
        print(f"{r['id']}. {r['room_name']} | Capacity: {r['capacity']} | {r['price_per_hour']} credits/hour | Status: {status}")

    if ai_suggestion and user:
        print("\n Suggested rooms for your faculty:")
        if user["faculty"].lower() == "science":
            print("Lab rooms recommended")
        elif user["faculty"].lower() == "art":
            print("Studio rooms recommended")
    conn.close()


def view_equipment(user=None, ai_suggestion=False):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM equipment")
    print("\nAvailable Equipment (Optional, pay from balance):")
    for e in cur.fetchall():
        print(f"{e['id']}. {e['name']} - {e['price']} credits")
    if ai_suggestion and user:
        print("\n Suggested equipment based on faculty:")
        if user["faculty"].lower() == "science":
            print("Projector recommended")
        elif user["faculty"].lower() == "art":
            print("Speaker recommended")
    conn.close()

# ================= HELPER FUNCTIONS =================
def calculate_hours(start_time, end_time):
    """Calculate hours between two time slots"""
    time_slots = [
        "08:00 AM","09:00 AM","10:00 AM","11:00 AM",
        "12:00 PM","01:00 PM","02:00 PM","03:00 PM",
        "04:00 PM","05:00 PM","06:00 PM","07:00 PM","08:00 PM"
    ]
    try:
        start_idx = time_slots.index(start_time)
        end_idx = time_slots.index(end_time)
        return end_idx - start_idx
    except ValueError:
        return 0

# ================= STUDENT =================
def view_balance_and_topup(user):

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM bank WHERE user_id=?", (user["id"],))
    system_balance = cur.fetchone()["balance"]
    print(f" System Balance: {system_balance}")
    conn.close()

    print("\nDo you want to topup your balance?")
    print("1. Yes")
    print("2. No")
    choice = input("Choose: ")

    if choice != "1":
        print("Returning to menu...")
        return

    print("""
Choose Bank:
1. Bank Islam
2. CIMB
3. Hong Leong
4. Maybank
    """)
    bank_choice = input("Choose bank: ")

    banks = {
        "1": "Bank Islam",
        "2": "CIMB",
        "3": "Hong Leong",
        "4": "Maybank"
    }

    if bank_choice not in banks:
        print(" Invalid bank selection")
        return

    try:
        amt = int(input("Enter amount to topup: "))
        if amt <= 0:
            raise ValueError
    except:
        print(" Invalid amount")
        return

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT bank_balance FROM user_bank_acc WHERE user_id=?", (user["id"],))
    bank_acc = cur.fetchone()["bank_balance"]
    if bank_acc < amt:
        print(f" Not enough money in your bank account (Available: {bank_acc})")
        conn.close()
        return

    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    malaysia_time = datetime.now(malaysia_tz)

    cur.execute("UPDATE user_bank_acc SET bank_balance = bank_balance - ? WHERE user_id=?", (amt, user["id"]))
    cur.execute("UPDATE bank SET balance = balance + ? WHERE user_id=?", (amt, user["id"]))
    cur.execute("""
        INSERT INTO transactions (user_id, bank_name, amount, date, status)
        VALUES (?,?,?,?,?)
    """, (user["id"], banks[bank_choice], amt, malaysia_time.strftime("%Y-%m-%d %H:%M"), "SUCCESS"))

    conn.commit()

    cur.execute("SELECT balance FROM bank WHERE user_id=?", (user["id"],))
    print(f" Updated System Balance: {cur.fetchone()['balance']}")

    cur.execute("SELECT bank_balance FROM user_bank_acc WHERE user_id=?", (user["id"],))
    print(f" Updated Bank Account Balance: {cur.fetchone()['bank_balance']}")

    conn.close()
    print(f" Topup SUCCESS via {banks[bank_choice]} (+{amt} credits)")



# ================= RESERVATION =================
def choose_time(label):
    time_slots = [
        "08:00 AM","09:00 AM","10:00 AM","11:00 AM",
        "12:00 PM","01:00 PM","02:00 PM","03:00 PM",
        "04:00 PM","05:00 PM","06:00 PM","07:00 PM","08:00 PM"
    ]
    print(f"\nSelect {label}:")
    for i, t in enumerate(time_slots, 1):
        print(f"{i}. {t}")
    try:
        choice = int(input("Choose: "))
        return choice, time_slots[choice-1]
    except:
        return None, None

def reserve_room(user):
    conn = connect_db()
    cur = conn.cursor()

    # Check booking rule (count only Confirmed and Pending)
    cur.execute("SELECT max_active FROM booking_rules")
    rule = cur.fetchone()["max_active"]
    cur.execute("SELECT COUNT(*) FROM reservations WHERE user_id=? AND status IN ('Confirmed', 'Pending')", (user["id"],))
    if cur.fetchone()[0] >= rule:
        print(" Max reservation reached")
        conn.close()
        return

    view_rooms(user, ai_suggestion=True)
    room = input("Room ID: ")
    date = input("Date (YYYY-MM-DD): ")

    # Validate date
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except:
        print(" Invalid date format")
        conn.close()
        return

    # Time slots
    time_slots = [
        "08:00 AM","09:00 AM","10:00 AM","11:00 AM",
        "12:00 PM","01:00 PM","02:00 PM","03:00 PM",
        "04:00 PM","05:00 PM","06:00 PM","07:00 PM","08:00 PM"
    ]

    print("\nSelect Start Time:")
    for i, t in enumerate(time_slots, 1):
        print(f"{i}. {t}")
    s = int(input("Choose start time: "))
    start_time = time_slots[s-1]

    print("\nSelect End Time:")
    for i, t in enumerate(time_slots, 1):
        print(f"{i}. {t}")
    e = int(input("Choose end time: "))
    end_time = time_slots[e-1]

    if e <= s:
        print(" End time must be after start time")
        conn.close()
        return

    # Show rooms with status
    view_rooms(user, date=date, start_time=start_time, end_time=end_time)

    room = input("Room ID to reserve (choose an available room): ")

    # Get room details for pricing
    cur.execute("SELECT * FROM rooms WHERE id=?", (room,))
    room_data = cur.fetchone()
    if not room_data:
        print(" Invalid room ID")
        conn.close()
        return

    # Safety check - updated to use Confirmed/Pending
    cur.execute("""
    SELECT * FROM reservations
    WHERE room_id=? AND date=? AND status IN ('Confirmed', 'Pending')
    AND NOT (end_time <= ? OR start_time >= ?)
    """, (room, date, start_time, end_time))
    if cur.fetchone():
        print(" Room already booked in this time range")
        conn.close()
        return

    # Calculate room cost
    hours = calculate_hours(start_time, end_time)
    room_cost = room_data['price_per_hour'] * hours

    # Equipment
    view_equipment(user, ai_suggestion=True)
    equip_ids = input("Equipment IDs (comma separated) or Enter to skip: ")

    equipment_cost = 0
    equip_list = []

    if equip_ids:
        for i in equip_ids.split(","):
            cur.execute("SELECT price FROM equipment WHERE id=?", (i.strip(),))
            row = cur.fetchone()
            if row:
                equipment_cost += row["price"]
                equip_list.append(i.strip())
            else:
                print(" Invalid equipment ID")
                conn.close()
                return

    # Total cost
    total_cost = room_cost + equipment_cost

    # Number of people
    num_people = int(input("Number of people: "))

    # Show cost breakdown
    print("\n" + "="*50)
    print(" COST BREAKDOWN")
    print("="*50)
    print(f"Room: {room_data['room_name']}")
    print(f"Duration: {hours} hour(s)")
    print(f"Room cost: {room_cost} credits ({hours} × {room_data['price_per_hour']} credits/hour)")
    print(f"Equipment cost: {equipment_cost} credits")
    print(f"Total: {total_cost} credits")
    print("="*50)

    # Get current timestamp
    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    now = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")

    # Insert reservation with Pending status
    cur.execute("""
    INSERT INTO reservations (user_id, room_id, date, start_time, end_time, num_people, status, created_at, updated_at)
    VALUES (?,?,?,?,?,?,'Pending',?,?)
    """,(user["id"], room, date, start_time, end_time, num_people, now, now))

    res_id = cur.lastrowid

    # Add equipment
    for e in equip_list:
        cur.execute("INSERT INTO reservation_equipment VALUES (?,?)",(res_id,e))

    conn.commit()

    print(f"\n Reservation created (Status: Pending)")
    print(f"Reservation ID: {res_id}")

    # Payment flow
    print("\n" + "="*50)
    print("PAYMENT")
    print("="*50)
    print("1. Pay Now (Confirm booking)")
    print("2. Pay Later (Booking will remain Pending)")
    choice = input("Choose: ")

    if choice == "1":
        # Process payment
        success = process_payment(user, res_id, total_cost)
        if not success:
            print("\n Payment failed. Booking saved as Pending.")
            print("You can pay later to confirm your booking.")
    else:
        print("\n Booking saved as Pending. Please pay to confirm.")

    conn.close()
    print(f"\n Reservation process completed!")
    view_balance_and_topup(user)


def process_payment(user, reservation_id, amount):
    """Process payment for a reservation"""
    conn = connect_db()
    cur = conn.cursor()
    
    # Generate transaction ID
    transaction_id = f"TXN-{int(time.time())}"
    
    # Get payment details
    print("\n Payment Method:")
    print("1. Online Banking")
    print("2. Credit Card")
    print("3. Use System Balance")
    method = input("Choose payment method: ")
    
    payment_method = {
        "1": "Online Banking",
        "2": "Credit Card",
        "3": "System Balance"
    }.get(method, "System Balance")
    
    bank_name = None
    account_number = None
    account_holder = None
    
    if payment_method == "Online Banking":
        print("\n Bank Details:")
        bank_name = input("Bank name: ")
        account_number = input("Account number: ")
        account_holder = input("Account holder: ")
    elif payment_method == "Credit Card":
        print("\n Card Details:")
        account_holder = input("Card holder name: ")
        account_number = input("Card number (last 4 digits): ")
        bank_name = "Credit Card"
    
    # Check balance if using system balance
    if payment_method == "System Balance":
        cur.execute("SELECT balance FROM bank WHERE user_id=?", (user["id"],))
        balance = cur.fetchone()["balance"]
        if balance < amount:
            print(f" Insufficient balance (Available: {balance} credits)")
            conn.close()
            return False
        
        # Deduct balance
        cur.execute("UPDATE bank SET balance = balance - ? WHERE user_id=?", (amount, user["id"]))
    
    # Create payment record
    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    paid_at = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
        INSERT INTO payments (
            reservation_id, user_id, amount, payment_method,
            bank_name, account_number, account_holder,
            transaction_id, status, paid_at, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (reservation_id, user["id"], amount, payment_method,
          bank_name, account_number, account_holder,
          transaction_id, 'completed', paid_at, paid_at))
    
    # Update reservation status to Confirmed
    cur.execute("UPDATE reservations SET status='Confirmed' WHERE id=?", (reservation_id,))
    
    conn.commit()
    conn.close()
    
    print(f"\n Payment Successful!")
    print(f"Transaction ID: {transaction_id}")
    print(f"Amount: {amount} credits")
    print(f"Method: {payment_method}")
    print(f"Status: Confirmed")
    
    return True


def update_reservation(user):
    conn = connect_db()
    cur = conn.cursor()

    # Papar reservation sedia ada
    cur.execute("""
    SELECT r.id, rm.room_name, r.date, r.start_time, r.end_time
    FROM reservations r
    JOIN rooms rm ON r.room_id = rm.id
    WHERE r.user_id=?
    """, (user["id"],))

    rows = cur.fetchall()
    if not rows:
        print(" No reservation")
        conn.close()
        return

    for r in rows:
        print(f"{r['id']}. {r['room_name']} on {r['date']} ({r['start_time']} - {r['end_time']})")

    rid = input("Reservation ID to update: ")

    print("1. Change Room")
    print("2. Change Date & Time")
    c = input("Choose: ")

    if c == "1":
        view_rooms(user, ai_suggestion=True)
        new_room = input("New Room ID: ")

        cur.execute("""
        UPDATE reservations SET room_id=? WHERE id=? AND user_id=?
        """, (new_room, rid, user["id"]))

    elif c == "2":
        d = input("New Date (YYYY-MM-DD): ")
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except:
            print(" Invalid date format")
            conn.close()
            return

        # Pilih start & end time menggunakan choose_time()
        s, start_time = choose_time("Start Time")
        e, end_time = choose_time("End Time")

        if not start_time or not end_time or e <= s:
            print(" Invalid time selection")
            conn.close()
            return

        # Dapatkan room_id semasa
        cur.execute("SELECT room_id FROM reservations WHERE id=?", (rid,))
        room_id = cur.fetchone()["room_id"]

        # Check overlapping booking (exclude current reservation)
        cur.execute("""
        SELECT * FROM reservations
        WHERE room_id=? AND date=? AND id!=?
        AND NOT (end_time <= ? OR start_time >= ?)
        """, (room_id, d, rid, start_time, end_time))

        if cur.fetchone():
            print(" Room already booked in this time range")
            conn.close()
            return

        # Update reservation
        cur.execute("""
        UPDATE reservations
        SET date=?, start_time=?, end_time=?
        WHERE id=? AND user_id=?
        """, (d, start_time, end_time, rid, user["id"]))

    conn.commit()
    conn.close()
    print(" Updated reservation")

def cancel_reservation(user):
    conn = connect_db()
    cur = conn.cursor()

    # Get active reservations (Confirmed or Pending)
    cur.execute("""
    SELECT r.id, rm.room_name, r.date, r.start_time, r.end_time, r.status
    FROM reservations r
    JOIN rooms rm ON r.room_id = rm.id
    WHERE r.user_id=? AND r.status IN ('Confirmed', 'Pending')
    """, (user["id"],))

    rows = cur.fetchall()
    if not rows:
        print(" No active reservation")
        conn.close()
        return

    for r in rows:
        status_emoji = {'Pending': '', 'Confirmed': ''}.get(r['status'], '')
        print(
            f"{r['id']}. {r['room_name']} on {r['date']} "
            f"({r['start_time']} - {r['end_time']}) | {status_emoji} {r['status']}"
        )

    rid = input("Reservation ID to cancel: ")

    # Get payment info for refund
    cur.execute("""
        SELECT p.*, r.status as reservation_status
        FROM payments p
        JOIN reservations r ON p.reservation_id = r.id
        WHERE p.reservation_id=? AND p.status='completed'
    """, (rid,))
    
    payment = cur.fetchone()
    
    refund_amount = 0
    
    if payment:
        # Full refund for confirmed booking
        refund_amount = payment['amount']
        
        # Update payment status to refunded
        cur.execute("UPDATE payments SET status='refunded' WHERE id=?", (payment['id'],))
        
        # Refund to balance
        cur.execute("UPDATE bank SET balance = balance + ? WHERE user_id=?", (refund_amount, user["id"]))
        
        print(f" Refunded {refund_amount} credits to your balance")
    else:
        # No payment found (Pending reservation)
        print(" No payment to refund (reservation was Pending)")

    # Update reservation status to Cancelled
    cur.execute("""
    UPDATE reservations
    SET status='Cancelled'
    WHERE id=? AND user_id=?
    """, (rid, user["id"]))

    # Clear equipment link
    cur.execute(
        "DELETE FROM reservation_equipment WHERE reservation_id=?",
        (rid,)
    )

    conn.commit()
    conn.close()

    print(" Reservation cancelled")
    balance = get_balance(user)
    print(f" System Balance: {balance}")

# ================= helper =================
def get_balance(user):
    """Return system balance untuk user"""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM bank WHERE user_id=?", (user["id"],))
    row = cur.fetchone()
    conn.close()
    return row["balance"] if row else 0

def get_user_bank_balance(user):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT bank_balance FROM user_bank_acc WHERE user_id=?", (user["id"],))
    row = cur.fetchone()
    conn.close()
    return row["bank_balance"] if row else 0

def view_history(user):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT r.id, rm.room_name, r.date, r.start_time, r.end_time
    FROM reservations r
    JOIN rooms rm ON r.room_id = rm.id
    WHERE r.user_id=?
    """, (user["id"],))

    reservations = cur.fetchall()
    total_spent = 0

    if not reservations:
        print(" No reservation history")
        conn.close()
        return

    for r in reservations:
        print(
            f"Reservation {r['id']}: {r['room_name']} on {r['date']} "
            f"({r['start_time']} - {r['end_time']})"
        )

        cur.execute("""
        SELECT e.name, e.price
        FROM reservation_equipment re
        JOIN equipment e ON re.equipment_id = e.id
        WHERE re.reservation_id=?
        """, (r["id"],))

        equip_list = cur.fetchall()
        for e in equip_list:
            print(f"  - Equipment: {e['name']} ({e['price']} credits)")
            total_spent += e["price"]

    print(f" Total spent on equipment: {total_spent} credits")
    conn.close()


def view_transactions(user):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT bank_name, amount, date, status
    FROM transactions
    WHERE user_id=?
    """,(user["id"],))

    rows = cur.fetchall()
    if not rows:
        print(" No transaction history")
    else:
        print("\n Transaction History")
        for r in rows:
            print(f"{r['date']} | {r['bank_name']} | +{r['amount']} | {r['status']}")
    conn.close()

def view_payment_history(user):
    """View all payment records for bookings"""
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.*, r.date, r.start_time, r.end_time, rm.room_name
        FROM payments p
        JOIN reservations r ON p.reservation_id = r.id
        JOIN rooms rm ON r.room_id = rm.id
        WHERE p.user_id=?
        ORDER BY p.paid_at DESC
    """, (user["id"],))
    
    payments = cur.fetchall()
    
    if not payments:
        print(" No payment history")
    else:
        print("\n Payment History")
        print("="*60)
        for p in payments:
            status_emoji = {
                'completed': '',
                'pending': '',
                'failed': '',
                'refunded': ''
            }.get(p['status'], '')
            
            print(f"\n{status_emoji} Transaction ID: {p['transaction_id']}")
            print(f"   Room: {p['room_name']}")
            print(f"   Date: {p['date']} ({p['start_time']} - {p['end_time']})")
            print(f"   Amount: {p['amount']} credits")
            print(f"   Method: {p['payment_method']}")
            if p['paid_at']:
                print(f"   Paid: {p['paid_at']}")
            print(f"   Status: {p['status']}")
    
    conn.close()

def delete_own_account(user):
    conn = connect_db()
    cur = conn.cursor()

    # Rekod tindakan dalam logs
    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    now = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
    INSERT INTO user_actions (user_id, action_type, details, date)
    VALUES (?,?,?,?)
    """, (user["id"], "Account Deletion", "User deleted their own account", now))

    # Soft delete user
    # Pilihan 1: tandakan active = 0 (perlukan column active dalam users)
    # cur.execute("UPDATE users SET active=0 WHERE id=?", (user["id"],))

    # Pilihan 2: hard delete (hapus terus, tapi log dah ada)
    cur.execute("DELETE FROM users WHERE id=?", (user["id"],))
    cur.execute("DELETE FROM bank WHERE user_id=?", (user["id"],))
    cur.execute("DELETE FROM user_bank_acc WHERE user_id=?", (user["id"],))

    conn.commit()
    conn.close()

    print(" Your account has been deleted. Librarian can see this action in logs.")


# ================= LIBRARIAN =================
def add_room():
    name = input("Room name: ")
    cap = int(input("Capacity: "))
    price = float(input("Price per hour (credits): "))
    
    conn = connect_db()
    cur = conn.cursor()
    
    # Get current timestamp
    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    now = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
        INSERT INTO rooms (room_name, capacity, price_per_hour, status, created_at, updated_at)
        VALUES (?,?,?,'available',?,?)
    """,(name, cap, price, now, now))
    
    conn.commit()
    conn.close()
    print(f" Room '{name}' added successfully!")

def update_room_capacity():
    view_rooms()  # Tunjuk semua rooms dulu
    rid = input("Room ID: ")

    try:
        cap = int(input("New capacity: "))
        if cap <= 0:
            print(" Capacity must be greater than 0")
            return
    except ValueError:
        print(" Invalid capacity")
        return

    conn = connect_db()
    cur = conn.cursor()

    # Semak Room ID wujud
    cur.execute("SELECT capacity, room_name FROM rooms WHERE id=?", (rid,))
    row = cur.fetchone()
    if not row:
        print(" Room ID not found")
        conn.close()
        return

    old_cap = row["capacity"]
    room_name = row["room_name"]

    # Update capacity
    cur.execute("UPDATE rooms SET capacity=? WHERE id=?", (cap, rid))

    # Log action
    from datetime import datetime

    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    now = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M")
    cur.execute("""
        INSERT INTO room_actions (room_id, action, date)
        VALUES (?,?,?)
    """, (rid, f"Capacity updated: {old_cap} → {cap}", now))

    conn.commit()
    conn.close()

    print(f" Room '{room_name}' capacity updated: {old_cap} → {cap}")

def delete_room():
    view_rooms()
    rid = input("Room ID to delete: ")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM reservation_equipment WHERE reservation_id IN (SELECT id FROM reservations WHERE room_id=?)",(rid,))
    cur.execute("DELETE FROM reservations WHERE room_id=?", (rid,))
    cur.execute("DELETE FROM rooms WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    print(" Room deleted")

def update_room_status():
    """Update room status (available/maintenance)"""
    conn = connect_db()
    cur = conn.cursor()
    
    # Show all rooms with current status
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()
    
    print("\n All Rooms:")
    for r in rooms:
        status_emoji = '' if r['status'] == 'available' else ''
        print(f"{r['id']}. {r['room_name']} | {status_emoji} {r['status']}")
    
    rid = input("\nRoom ID to update: ")
    
    print("\n1. Available")
    print("2. Maintenance")
    choice = input("New status: ")
    
    new_status = 'available' if choice == '1' else 'maintenance'
    
    # Get current timestamp
    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    now = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("UPDATE rooms SET status=?, updated_at=? WHERE id=?", (new_status, now, rid))
    conn.commit()
    conn.close()
    
    print(f" Room status updated to: {new_status}")

def librarian_dashboard():
    """Display dashboard with statistics"""
    conn = connect_db()
    cur = conn.cursor()
    
    print("\n" + "="*60)
    print(" LIBRARIAN DASHBOARD")
    print("="*60)
    
    # Total rooms
    cur.execute("SELECT COUNT(*) as total FROM rooms")
    total_rooms = cur.fetchone()['total']
    
    # Available vs Maintenance
    cur.execute("SELECT COUNT(*) as total FROM rooms WHERE status='available'")
    available_rooms = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM rooms WHERE status='maintenance'")
    maintenance_rooms = cur.fetchone()['total']
    
    # Total reservations by status
    cur.execute("SELECT status, COUNT(*) as count FROM reservations GROUP BY status")
    reservation_stats = cur.fetchall()
    
    # Total revenue from payments
    cur.execute("SELECT SUM(amount) as total FROM payments WHERE status='completed'")
    total_revenue = cur.fetchone()['total'] or 0
    
    # Refunded amount
    cur.execute("SELECT SUM(amount) as total FROM payments WHERE status='refunded'")
    refunded = cur.fetchone()['total'] or 0
    
    # Recent bookings (last 5)
    cur.execute("""
        SELECT r.id, u.name, rm.room_name, r.date, r.status
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN rooms rm ON r.room_id = rm.id
        ORDER BY r.created_at DESC
        LIMIT 5
    """)
    recent_bookings = cur.fetchall()
    
    # Display statistics
    print(f"\n ROOMS")
    print(f"   Total: {total_rooms}")
    print(f"    Available: {available_rooms}")
    print(f"    Maintenance: {maintenance_rooms}")
    
    print(f"\n RESERVATIONS")
    for stat in reservation_stats:
        emoji = {'Confirmed': '', 'Pending': '', 'Cancelled': ''}.get(stat['status'], '')
        print(f"   {emoji} {stat['status']}: {stat['count']}")
    
    print(f"\n REVENUE")
    print(f"   Total Revenue: {total_revenue} credits")
    print(f"   Refunded: {refunded} credits")
    print(f"   Net Revenue: {total_revenue - refunded} credits")
    
    print(f"\n RECENT BOOKINGS")
    for booking in recent_bookings:
        status_emoji = {'Confirmed': '', 'Pending': '', 'Cancelled': ''}.get(booking['status'], '')
        print(f"   {status_emoji} #{booking['id']} | {booking['name']} | {booking['room_name']} | {booking['date']}")
    
    print("="*60)
    conn.close()

def view_all_payments():
    """View all payment records (librarian only)"""
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.*, u.name, u.student_id, r.date, r.start_time, r.end_time, rm.room_name
        FROM payments p
        JOIN users u ON p.user_id = u.id
        JOIN reservations r ON p.reservation_id = r.id
        JOIN rooms rm ON r.room_id = rm.id
        ORDER BY p.paid_at DESC
    """)
    
    payments = cur.fetchall()
    
    if not payments:
        print(" No payment records")
    else:
        print("\n ALL PAYMENT RECORDS")
        print("="*80)
        for p in payments:
            status_emoji = {
                'completed': '',
                'pending': '',
                'failed': '',
                'refunded': ''
            }.get(p['status'], '')
            
            print(f"\n{status_emoji} TXN: {p['transaction_id']}")
            print(f"   Student: {p['name']} ({p['student_id']})")
            print(f"   Room: {p['room_name']}")
            print(f"   Date: {p['date']} ({p['start_time']} - {p['end_time']})")
            print(f"   Amount: {p['amount']} credits | Method: {p['payment_method']}")
            if p['paid_at']:
                print(f"   Paid: {p['paid_at']}")
            print(f"   Status: {p['status']}")
    
    conn.close()

def view_all_reservations():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT r.id, u.username, u.name, rm.room_name, r.date, r.start_time, r.end_time, r.status
    FROM reservations r
    JOIN users u ON r.user_id = u.id
    JOIN rooms rm ON r.room_id = rm.id
    ORDER BY r.date, r.start_time
    """)

    rows = cur.fetchall()
    if not rows:
        print(" No reservations found")
        conn.close()
        return

    print("\n All Reservations")
    for r in rows:
        print(
            f"{r['username']} ({r['name']}) - {r['room_name']} on {r['date']} "
            f"({r['start_time']} - {r['end_time']}) | Status: {r['status']}"
        )

    conn.close()

def update_booking_rules():
    maxa = int(input("Max active reservation: "))
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM booking_rules")
    cur.execute("INSERT INTO booking_rules VALUES (1,?)",(maxa,))
    conn.commit()
    conn.close()
    print(" Rules updated")

def update_student_balance():
    sid = input("Student ID: ")
    amt = int(input("Credit to add: "))
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE student_id=?", (sid,))
    u = cur.fetchone()
    if u:
        cur.execute("UPDATE bank SET balance=balance+? WHERE user_id=?", (amt,u["id"]))
        conn.commit()
        print(" Credit added")
    else:
        print(" Student not found")
    conn.close()

def view_user_actions():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT ua.id, u.username, ua.action_type, ua.details, ua.date
    FROM user_actions ua
    LEFT JOIN users u ON ua.user_id = u.id
    ORDER BY ua.date DESC
    """)
    rows = cur.fetchall()
    if not rows:
        print(" No actions recorded")
    else:
        for r in rows:
            uname = r["username"] if r["username"] else "Deleted User"
            print(f"{r['date']} | {uname} | {r['action_type']} - {r['details']}")
    conn.close()

# ================= MENU =================
def main():
    setup_db()

    while True:
        print("\n1.Register  2.Login  0.Exit")
        c = input("Choose: ")
        if c == "1":
            register()
        elif c == "2":
            user = login()
            if not user:
                print(" Login failed")
                continue

            if user["role"] == "student":
                student_menu(user)
            elif user["role"] == "librarian":
                librarian_menu()
        elif c == "0":
            print("Goodbye!")
            break
        else:
            print(" Invalid choice")


# ================= MENU STUDENT =================
def student_menu(user):
    while True:
        print("""
1. View Rooms
2. Reserve Room + Equipment
3. Update Reservation
4. Cancel Reservation
5. View Balance & Topup
6. View History
7. View Transactions
8. View Bank Account
9. View Payment History
10. Delete Account
0. Logout
        """)
        s = input("Choose: ")

        if s == "1":
            view_rooms(user, ai_suggestion=True)
        elif s == "2":
            reserve_room(user)
        elif s == "3":
            update_reservation(user)
        elif s == "4":
            cancel_reservation(user)
        elif s == "5":
            view_balance_and_topup(user)
        elif s == "6":
            view_history(user)
        elif s == "7":
            view_transactions(user)
        elif s == "8":
            bank_balance = get_user_bank_balance(user)
            print(f" Bank Account Balance: {bank_balance} credits")
        elif s == "9":
            view_payment_history(user)
        elif s == "10":
            confirm = input("Are you sure you want to delete your account? (yes/no): ")
            if confirm.lower() == "yes":
                delete_own_account(user)
                break
        elif s == "0":
            break
        else:
            print(" Invalid choice, try again.")


# ================= LIBRARIAN MENU =================
def librarian_menu():
    while True:
        print("""
1. Dashboard
2. View Rooms
3. Add Room
4. Update Room Capacity
5. Update Room Status
6. Delete Room
7. View All Reservations
8. View All Payments
9. Update Booking Rules
10. View User Actions
0. Logout
        """)
        l = input("Choose: ")
        if l == "1":
            librarian_dashboard()
        elif l == "2":
            view_rooms()  # untuk librarian, user=None
        elif l == "3":
            add_room()
        elif l == "4":
            update_room_capacity()
        elif l == "5":
            update_room_status()
        elif l == "6":
            delete_room()
        elif l == "7":
            view_all_reservations()
        elif l == "8":
            view_all_payments()
        elif l == "9":
            update_booking_rules()
        elif l == "10":
            view_user_actions()
        elif l == "0":
            break
        else:
            print(" Invalid choice")


if __name__ == "__main__":
    main()

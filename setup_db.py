"""
Database Setup Script for Library Room Reservation System
Run this script to set up or reset the SQLite database
"""

import sqlite3
import bcrypt
import os
import sys
from datetime import datetime
import pytz

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "reservation_system.db")

def get_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_malaysia_time():
    """Get current time in Malaysia timezone"""
    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    return datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")

def create_tables():
    """Create all database tables"""
    print("Creating tables...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            student_id TEXT,
            faculty TEXT,
            email TEXT UNIQUE,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    # Bank balance table (system credits)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank (
            user_id INTEGER UNIQUE,
            balance INTEGER DEFAULT 0
        )
    """)
    
    # User bank account table (external bank balance)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_bank_acc (
            user_id INTEGER UNIQUE,
            bank_balance INTEGER DEFAULT 1000
        )
    """)
    
    # Rooms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            price_per_hour REAL NOT NULL DEFAULT 10.0,
            status TEXT NOT NULL DEFAULT 'available',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    # Reservations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            num_people INTEGER,
            status TEXT DEFAULT 'Pending',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            bank_name TEXT,
            account_number TEXT,
            account_holder TEXT,
            transaction_id TEXT UNIQUE,
            status TEXT NOT NULL DEFAULT 'pending',
            paid_at TEXT,
            created_at TEXT,
            FOREIGN KEY (reservation_id) REFERENCES reservations(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Equipment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL
        )
    """)
    
    # Reservation equipment junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservation_equipment (
            reservation_id INTEGER,
            equipment_id INTEGER,
            FOREIGN KEY (reservation_id) REFERENCES reservations(id),
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        )
    """)
    
    # Transactions table (topup records)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bank_name TEXT,
            amount INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Booking rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS booking_rules (
            id INTEGER PRIMARY KEY,
            max_active INTEGER
        )
    """)
    
    # Room actions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER,
            action TEXT,
            date TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    """)
    
    # User actions log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_type TEXT,
            details TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ Tables created successfully.")

def create_admin():
    """Create default admin user"""
    print("Creating admin user...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    now = get_malaysia_time()
    
    if admin:
        # Update admin password
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "UPDATE users SET password = ?, updated_at = ? WHERE username = 'admin'",
            (password_hash, now)
        )
        print("✓ Admin password updated.")
    else:
        # Create admin
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO users (name, student_id, faculty, email, username, password, role, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('Admin', '-', 'Library', 'admin@library.com', 'admin', password_hash, 'librarian', now, now))
        
        admin_id = cursor.lastrowid
        
        # Create bank accounts for admin
        cursor.execute("INSERT INTO bank (user_id, balance) VALUES (?, ?)", (admin_id, 0))
        cursor.execute("INSERT INTO user_bank_acc (user_id, bank_balance) VALUES (?, ?)", (admin_id, 1000))
        
        print("✓ Admin user created.")
    
    conn.commit()
    cursor.close()
    conn.close()

def create_booking_rules():
    """Create default booking rules"""
    print("Setting up booking rules...")
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM booking_rules WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO booking_rules (id, max_active) VALUES (1, 2)")
        print("✓ Booking rules created (max 2 active reservations per user).")
    else:
        print("✓ Booking rules already exist.")
    
    conn.commit()
    cursor.close()
    conn.close()

def create_sample_rooms():
    """Create sample rooms"""
    print("Creating sample rooms...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if rooms exist
    cursor.execute("SELECT COUNT(*) FROM rooms")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"✓ {count} rooms already exist. Skipping.")
    else:
        now = get_malaysia_time()
        rooms = [
            ('Study Room A', 4, 5.0, 'available', now, now),
            ('Conference Room 1', 12, 15.0, 'available', now, now),
            ('Quiet Study Pod', 1, 3.0, 'available', now, now),
            ('Group Study Room B', 8, 10.0, 'available', now, now),
            ('Media Room', 6, 20.0, 'available', now, now),
            ('Computer Lab', 20, 25.0, 'available', now, now),
        ]
        
        cursor.executemany("""
            INSERT INTO rooms (room_name, capacity, price_per_hour, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, rooms)
        
        print(f"✓ Created {len(rooms)} sample rooms.")
    
    conn.commit()
    cursor.close()
    conn.close()

def create_sample_equipment():
    """Create sample equipment"""
    print("Creating sample equipment...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if equipment exists
    cursor.execute("SELECT COUNT(*) FROM equipment")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"✓ {count} equipment items already exist. Skipping.")
    else:
        equipment = [
            ('Microphone', 5),
            ('Projector', 10),
            ('Speaker', 7),
            ('Whiteboard', 3),
            ('Laptop', 15),
        ]
        
        cursor.executemany("INSERT INTO equipment (name, price) VALUES (?, ?)", equipment)
        print(f"✓ Created {len(equipment)} equipment items.")
    
    conn.commit()
    cursor.close()
    conn.close()

def verify_database():
    """Verify database setup"""
    print("\nVerifying database setup...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"✓ Found {len(tables)} tables:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  • {table[0]}: {count} records")
    
    cursor.close()
    conn.close()

def main():
    """Main setup function"""
    print("=" * 60)
    print("Library Room Reservation System - Database Setup (SQLite)")
    print("=" * 60)
    print()
    
    try:
        # Check if database already exists
        db_exists = os.path.exists(DB_PATH)
        if db_exists:
            print(f"⚠ Database already exists at: {DB_PATH}")
            response = input("Do you want to continue? (existing data will be preserved) [y/N]: ")
            if response.lower() != 'y':
                print("Setup cancelled.")
                sys.exit(0)
        
        create_tables()
        create_admin()
        create_booking_rules()
        create_sample_rooms()
        create_sample_equipment()
        verify_database()
        
        print("\n" + "=" * 60)
        print("✓ Setup completed successfully!")
        print("=" * 60)
        print("\nDatabase location:", DB_PATH)
        print("\nAdmin credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n⚠ IMPORTANT: Change the admin password after first login!")
        print("\nYou can now run the app:")
        print("  python app.py")
        print("\nOr deploy to PythonAnywhere following the deployment guide.")
        print()
        
    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

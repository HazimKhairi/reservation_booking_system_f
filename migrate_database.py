"""
Database Migration Script
Migrates reservation_system.db to support new website features:
1. Add email field to users
2. Add timestamps to users, rooms, reservations
3. Add room pricing and status
4. Create payments table
5. Migrate existing passwords to bcrypt
"""

import sqlite3
import os
import bcrypt
from datetime import datetime
import pytz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "reservation_system.db")
BACKUP_DB = os.path.join(BASE_DIR, "reservation_system.db.backup")

def connect_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_database():
    """Run all migration steps"""
    print("="*60)
    print("DATABASE MIGRATION - Adding Website Features")
    print("="*60)
    
    # Verify backup exists
    if not os.path.exists(BACKUP_DB):
        print(" Backup not found! Creating backup first...")
        import shutil
        shutil.copy2(DB, BACKUP_DB)
        print(" Backup created: reservation_system.db.backup")
    else:
        print(" Backup found: reservation_system.db.backup")
    
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        # Step 1: Add email to users table (without UNIQUE constraint initially)
        print("\n[1/7] Adding email field to users table...")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
            print(" Email field added")
            # Note: UNIQUE constraint will be enforced in application code
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  Email field already exists, skipping")
            else:
                raise
        
        # Step 2: Add timestamps to users
        print("\n[2/7] Adding timestamps to users table...")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")
            # Set current timestamp for existing users
            malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
            now = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("UPDATE users SET created_at=?, updated_at=? WHERE created_at IS NULL", (now, now))
            print(" Timestamps added to users")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  Timestamps already exist, skipping")
            else:
                raise
        
        # Step 3: Add price and status to rooms
        print("\n[3/7] Adding pricing and status to rooms table...")
        try:
            cur.execute("ALTER TABLE rooms ADD COLUMN price_per_hour REAL DEFAULT 0.0")
            cur.execute("ALTER TABLE rooms ADD COLUMN status TEXT DEFAULT 'available'")
            print(" Room pricing and status added")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  Room fields already exist, skipping")
            else:
                raise
        
        # Step 4: Add timestamps to rooms
        print("\n[4/7] Adding timestamps to rooms table...")
        try:
            cur.execute("ALTER TABLE rooms ADD COLUMN created_at TEXT")
            cur.execute("ALTER TABLE rooms ADD COLUMN updated_at TEXT")
            # Set current timestamp for existing rooms
            malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
            now = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("UPDATE rooms SET created_at=?, updated_at=? WHERE created_at IS NULL", (now, now))
            print(" Timestamps added to rooms")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  Timestamps already exist, skipping")
            else:
                raise
        
        # Step 5: Add timestamps to reservations
        print("\n[5/7] Adding timestamps to reservations table...")
        try:
            cur.execute("ALTER TABLE reservations ADD COLUMN created_at TEXT")
            cur.execute("ALTER TABLE reservations ADD COLUMN updated_at TEXT")
            # Set current timestamp for existing reservations
            malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
            now = datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("UPDATE reservations SET created_at=?, updated_at=? WHERE created_at IS NULL", (now, now))
            print(" Timestamps added to reservations")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("  Timestamps already exist, skipping")
            else:
                raise
        
        # Step 6: Create payments table
        print("\n[6/7] Creating payments table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id INTEGER,
                user_id INTEGER,
                amount REAL,
                payment_method TEXT,
                bank_name TEXT,
                account_number TEXT,
                account_holder TEXT,
                transaction_id TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                paid_at TEXT,
                created_at TEXT
            )
        """)
        print(" Payments table created")
        
        # Step 7: Migrate existing passwords to bcrypt
        print("\n[7/7] Migrating passwords to bcrypt...")
        cur.execute("SELECT id, password FROM users")
        users = cur.fetchall()
        
        migrated = 0
        skipped = 0
        
        for user in users:
            password = user['password']
            
            # Check if already hashed (bcrypt hashes start with $2b$)
            if password and not password.startswith('$2b$'):
                # Hash the plain text password
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cur.execute("UPDATE users SET password=? WHERE id=?", 
                           (hashed.decode('utf-8'), user['id']))
                migrated += 1
            else:
                skipped += 1
        
        print(f" Passwords migrated: {migrated}, Already hashed: {skipped}")
        
        # Step 8: Set default prices for existing rooms
        print("\n[8/7] Setting default prices for existing rooms...")
        cur.execute("UPDATE rooms SET price_per_hour = 10.0 WHERE price_per_hour = 0.0")
        rows_updated = cur.rowcount
        print(f" Updated {rows_updated} rooms with default price (10.0 credits/hour)")
        
        # Step 9: Update 'Active' status to 'Confirmed' for backward compatibility
        print("\n[9/7] Updating reservation statuses...")
        cur.execute("UPDATE reservations SET status = 'Confirmed' WHERE status = 'Active'")
        rows_updated = cur.rowcount
        print(f" Updated {rows_updated} reservations from 'Active' to 'Confirmed'")
        
        conn.commit()
        
        # Verification
        print("\n" + "="*60)
        print("MIGRATION VERIFICATION")
        print("="*60)
        
        # Check users table
        cur.execute("PRAGMA table_info(users)")
        user_cols = [col[1] for col in cur.fetchall()]
        print(f"\n Users columns: {', '.join(user_cols)}")
        
        # Check rooms table
        cur.execute("PRAGMA table_info(rooms)")
        room_cols = [col[1] for col in cur.fetchall()]
        print(f" Rooms columns: {', '.join(room_cols)}")
        
        # Check reservations table
        cur.execute("PRAGMA table_info(reservations)")
        res_cols = [col[1] for col in cur.fetchall()]
        print(f" Reservations columns: {', '.join(res_cols)}")
        
        # Check payments table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments'")
        if cur.fetchone():
            print(" Payments table exists")
        
        # Count records
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM rooms")
        room_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM reservations")
        res_count = cur.fetchone()[0]
        
        print(f"\n Database Statistics:")
        print(f"   Users: {user_count}")
        print(f"   Rooms: {room_count}")
        print(f"   Reservations: {res_count}")
        
        print("\n" + "="*60)
        print(" MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nNext steps:")
        print("1. Update Reservations.py with new features")
        print("2. Test the application")
        print("3. If issues occur, restore backup:")
        print("   cp reservation_system.db.backup reservation_system.db")
        
    except Exception as e:
        print(f"\n MIGRATION FAILED: {e}")
        print("\nRolling back changes...")
        conn.rollback()
        print("To restore backup manually:")
        print("cp reservation_system.db.backup reservation_system.db")
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

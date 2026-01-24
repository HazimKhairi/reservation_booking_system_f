"""
Database Setup Script for Library Room Reservation System
Run this script to set up or reset the database
"""

import mysql.connector
import bcrypt
import os
import sys

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Update with your MySQL password
    'port': 3306
}

DATABASE_NAME = 'library_reservation'

def get_connection(with_db=False):
    config = DB_CONFIG.copy()
    if with_db:
        config['database'] = DATABASE_NAME
    return mysql.connector.connect(**config)

def create_database():
    print("Creating database...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
    cursor.close()
    conn.close()
    print(f"Database '{DATABASE_NAME}' ready.")

def create_tables():
    print("Creating tables...")
    conn = get_connection(with_db=True)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin', 'patron') NOT NULL DEFAULT 'patron',
            bank_name VARCHAR(100),
            bank_account_number VARCHAR(50),
            bank_account_holder VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Rooms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            capacity INT NOT NULL,
            equipment VARCHAR(255),
            price_per_hour DECIMAL(10, 2) NOT NULL DEFAULT 10.00,
            status ENUM('available', 'maintenance') NOT NULL DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Reservations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            room_id INT NOT NULL,
            user_id INT NOT NULL,
            reservation_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            status ENUM('pending', 'confirmed', 'cancelled') NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reservation_id INT NOT NULL,
            user_id INT NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            bank_name VARCHAR(100),
            account_number VARCHAR(50),
            account_holder VARCHAR(100),
            transaction_id VARCHAR(100) UNIQUE,
            status ENUM('pending', 'completed', 'failed', 'refunded') NOT NULL DEFAULT 'pending',
            paid_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    
    # Fix existing tables if they have wrong structure
    # This ensures 'pending' is in the reservations status enum
    try:
        cursor.execute("""
            ALTER TABLE reservations 
            MODIFY COLUMN status ENUM('pending', 'confirmed', 'cancelled') 
            NOT NULL DEFAULT 'pending'
        """)
        conn.commit()
    except mysql.connector.Error:
        pass  # Already correct
    
    cursor.close()
    conn.close()
    print("Tables created.")

def create_admin():
    print("Creating admin user...")
    conn = get_connection(with_db=True)
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone():
        # Update password
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (password_hash,))
        print("Admin password updated.")
    else:
        # Create admin
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            ('admin', 'admin@library.com', password_hash, 'admin')
        )
        print("Admin user created.")
    
    conn.commit()
    cursor.close()
    conn.close()

def create_sample_rooms():
    print("Creating sample rooms...")
    conn = get_connection(with_db=True)
    cursor = conn.cursor()
    
    # Check if rooms exist
    cursor.execute("SELECT COUNT(*) FROM rooms")
    if cursor.fetchone()[0] > 0:
        print("Rooms already exist. Skipping.")
    else:
        rooms = [
            ('Study Room A', 4, 'Whiteboard, Power Outlets', 5.00, 'available'),
            ('Conference Room 1', 12, 'Projector, Whiteboard, Video Conference', 15.00, 'available'),
            ('Quiet Study Pod', 1, 'Desk Lamp, Power Outlet', 3.00, 'available'),
            ('Group Study Room B', 8, 'Large Display, Whiteboard', 10.00, 'available'),
            ('Media Room', 6, 'Projector, Sound System, Blu-ray Player', 20.00, 'maintenance'),
        ]
        cursor.executemany(
            "INSERT INTO rooms (name, capacity, equipment, price_per_hour, status) VALUES (%s, %s, %s, %s, %s)",
            rooms
        )
        print(f"Created {len(rooms)} sample rooms.")
    
    conn.commit()
    cursor.close()
    conn.close()

def cleanup_test_data():
    print("Cleaning up test data...")
    conn = get_connection(with_db=True)
    cursor = conn.cursor()
    
    # Get all test user ids first
    cursor.execute("SELECT id FROM users WHERE username LIKE 'test%' OR username LIKE 'debug%'")
    test_users = cursor.fetchall()
    
    for (user_id,) in test_users:
        # Delete payments for this user
        cursor.execute("DELETE FROM payments WHERE user_id = %s", (user_id,))
        # Delete reservations for this user
        cursor.execute("DELETE FROM reservations WHERE user_id = %s", (user_id,))
    
    # Delete all test users
    cursor.execute("DELETE FROM users WHERE username LIKE 'test%' OR username LIKE 'debug%'")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Test data cleaned.")

def main():
    print("="*50)
    print("Library Room Reservation - Database Setup")
    print("="*50)
    
    try:
        create_database()
        create_tables()
        create_admin()
        create_sample_rooms()
        cleanup_test_data()
        
        print("\n" + "="*50)
        print("Setup completed successfully!")
        print("="*50)
        print("\nAdmin credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nYou can now run the app: python app.py")
        
    except mysql.connector.Error as e:
        print(f"\nDatabase error: {e}")
        print("\nMake sure:")
        print("1. MySQL is running")
        print("2. Update DB_CONFIG in this script with your MySQL password")
        sys.exit(1)

if __name__ == "__main__":
    main()

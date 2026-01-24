"""Create the payments table if it doesn't exist"""
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='library_reservation'
)
cursor = conn.cursor()

# Create payments table
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

# Add price_per_hour to rooms if missing
try:
    cursor.execute("ALTER TABLE rooms ADD COLUMN price_per_hour DECIMAL(10, 2) NOT NULL DEFAULT 10.00 AFTER equipment")
    print("Added price_per_hour column to rooms")
except mysql.connector.Error as e:
    if "Duplicate column" in str(e):
        print("price_per_hour column already exists")
    else:
        print(f"Note: {e}")

# Update rooms with prices if they're default
cursor.execute("UPDATE rooms SET price_per_hour = 5.00 WHERE name LIKE '%Study%' AND price_per_hour = 10.00")
cursor.execute("UPDATE rooms SET price_per_hour = 15.00 WHERE name LIKE '%Conference%' AND price_per_hour = 10.00")
cursor.execute("UPDATE rooms SET price_per_hour = 3.00 WHERE name LIKE '%Pod%' AND price_per_hour = 10.00")
cursor.execute("UPDATE rooms SET price_per_hour = 20.00 WHERE name LIKE '%Media%' AND price_per_hour = 10.00")

conn.commit()
print("Payments table created/verified!")

# Verify
cursor.execute("SHOW TABLES")
print("\nTables in database:")
for (table,) in cursor.fetchall():
    print(f"  - {table}")

cursor.close()
conn.close()

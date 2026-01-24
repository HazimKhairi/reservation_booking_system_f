"""Fix the reservations table status column"""
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='library_reservation'
)
cursor = conn.cursor()

# Fix the status column to include 'pending'
cursor.execute("""
    ALTER TABLE reservations 
    MODIFY COLUMN status ENUM('pending', 'confirmed', 'cancelled') 
    NOT NULL DEFAULT 'pending'
""")

conn.commit()
print("Fixed reservations.status column!")

# Verify
cursor.execute("SHOW CREATE TABLE reservations")
print(cursor.fetchone()[1])

cursor.close()
conn.close()

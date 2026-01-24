"""Check the database state"""
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='library_reservation'
)
cursor = conn.cursor(dictionary=True)

print("="*60)
print("DATABASE STATE CHECK")
print("="*60)

# Check users
print("\n--- USERS ---")
cursor.execute("SELECT id, username, role FROM users ORDER BY id")
for row in cursor.fetchall():
    print(f"  ID: {row['id']}, Username: {row['username']}, Role: {row['role']}")

# Check reservations
print("\n--- RESERVATIONS (last 5) ---")
cursor.execute("""
    SELECT r.id, r.room_id, r.user_id, r.reservation_date, r.status, u.username
    FROM reservations r
    JOIN users u ON r.user_id = u.id
    ORDER BY r.id DESC LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  ID: {row['id']}, Room: {row['room_id']}, User ID: {row['user_id']} ({row['username']}), Date: {row['reservation_date']}, Status: {row['status']}")

# Check payments
print("\n--- PAYMENTS (last 5) ---")
cursor.execute("""
    SELECT p.id, p.reservation_id, p.user_id, p.transaction_id, p.status
    FROM payments p
    ORDER BY p.id DESC LIMIT 5
""")
results = cursor.fetchall()
if results:
    for row in results:
        print(f"  ID: {row['id']}, Res ID: {row['reservation_id']}, User ID: {row['user_id']}, TXN: {row['transaction_id']}, Status: {row['status']}")
else:
    print("  No payments found")

cursor.close()
conn.close()
print("\n" + "="*60)

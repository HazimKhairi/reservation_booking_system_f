"""Debug script with direct database check after each step"""
import requests
from datetime import date, timedelta
import mysql.connector

BASE_URL = 'http://localhost:5000'

def check_db(step):
    conn = mysql.connector.connect(host='localhost', user='root', password='', database='library_reservation')
    cursor = conn.cursor(dictionary=True)
    
    print(f"\n   [DB after {step}]")
    cursor.execute("SELECT id, username FROM users WHERE username = 'debugtest3'")
    user = cursor.fetchone()
    if user:
        print(f"   User: id={user['id']}, username={user['username']}")
        
        cursor.execute("SELECT id, user_id, status FROM reservations WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user['id'],))
        res = cursor.fetchone()
        if res:
            print(f"   Reservation: id={res['id']}, user_id={res['user_id']}, status={res['status']}")
        else:
            cursor.execute("SELECT id, user_id, status FROM reservations ORDER BY id DESC LIMIT 1")
            res = cursor.fetchone()
            if res:
                print(f"   Last reservation (not user's): id={res['id']}, user_id={res['user_id']}, status={res['status']}")
            else:
                print("   No reservations")
    else:
        print("   User not created yet")
    
    cursor.close()
    conn.close()

print("="*60)
print("FULL DEBUG WITH DB CHECK")
print("="*60)

session = requests.Session()

# 1. Register
print("\n1. Registering debugtest3...")
r = session.post(f'{BASE_URL}/register', data={
    'username': 'debugtest3',
    'email': 'debugtest3@test.com',
    'password': 'test123',
    'confirm_password': 'test123'
}, allow_redirects=False)
print(f"   Status: {r.status_code}")
check_db("register")

# 2. Login
print("\n2. Logging in...")
r = session.post(f'{BASE_URL}/login', data={
    'username': 'debugtest3',
    'password': 'test123'
}, allow_redirects=False)
print(f"   Status: {r.status_code}, Location: {r.headers.get('Location', '')}")
print(f"   Session cookie: {session.cookies.get('session', 'NONE')[:50]}...")

# 3. Check that we're logged in by accessing dashboard
print("\n3. Verify login via dashboard...")
r = session.get(f'{BASE_URL}/patron/dashboard')
print(f"   Status: {r.status_code}")
print(f"   Contains 'Welcome': {'Welcome' in r.text}")
print(f"   Contains 'debugtest3': {'debugtest3' in r.text}")

# 4. Book room
print("\n4. Booking room...")
future_date = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
r = session.post(f'{BASE_URL}/patron/book/1', data={
    'date': future_date,
    'start_time': '11:00',
    'end_time': '12:00'
}, allow_redirects=False)
checkout_loc = r.headers.get('Location', '')
print(f"   Status: {r.status_code}, Location: {checkout_loc}")
check_db("book")

# 5. Access checkout
print("\n5. Accessing checkout...")
if checkout_loc:
    full_url = f'{BASE_URL}{checkout_loc}'
    print(f"   URL: {full_url}")
    r = session.get(full_url)
    print(f"   Status: {r.status_code}")
    print(f"   Has 'Payment Details': {'Payment Details' in r.text}")
    print(f"   Has 'error': {'error' in r.text.lower()}")
    print(f"   Has 'not found': {'not found' in r.text.lower()}")
    check_db("checkout GET")
    
    # 6. Submit payment
    print("\n6. Submitting payment...")
    res_id = checkout_loc.split('/')[-1]
    r = session.post(f'{BASE_URL}/patron/checkout/{res_id}', data={
        'payment_method': 'Online Banking',
        'bank_name': 'Maybank',
        'account_number': '1234567890',
        'account_holder': 'Debug Test'
    }, allow_redirects=False)
    receipt_loc = r.headers.get('Location', '')
    print(f"   Status: {r.status_code}, Location: {receipt_loc}")
    check_db("checkout POST")
    
    if 'receipt' in receipt_loc:
        print("\n7. SUCCESS! Receipt page would load")
    else:
        print(f"\n7. FAILED - Redirected to: {receipt_loc}")

print("\n" + "="*60)

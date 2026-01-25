"""
Library Room Reservation System - Route Testing Script
Tests all routes for Admin and Patron roles programmatically
"""

import requests
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:5000"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add(self, test_name, passed, details=""):
        status = "PASS" if passed else "FAIL"
        self.results.append((test_name, status, details))
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print(f"[{status}] {test_name}" + (f" - {details}" if details else ""))
    
    def summary(self):
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {self.passed} passed, {self.failed} failed")
        print("="*60)


def test_public_routes(results):
    """Test public routes (no login required)"""
    print("\n--- Testing Public Routes ---")
    
    # Test index redirect to login
    r = requests.get(f"{BASE_URL}/", allow_redirects=False)
    results.add("Index redirects to login", r.status_code == 302)
    
    # Test login page
    r = requests.get(f"{BASE_URL}/login")
    results.add("Login page loads", r.status_code == 200 and "Sign in" in r.text)
    
    # Test register page
    r = requests.get(f"{BASE_URL}/register")
    results.add("Register page loads", r.status_code == 200 and "Create a new account" in r.text)


def test_admin_login(session, results):
    """Test admin login"""
    print("\n--- Testing Admin Login ---")
    
    # Login as admin
    r = session.post(f"{BASE_URL}/login", data={
        "username": "admin",
        "password": "admin123"
    }, allow_redirects=False)
    results.add("Admin login redirects", r.status_code == 302)
    
    # Check dashboard access
    r = session.get(f"{BASE_URL}/admin/dashboard")
    results.add("Admin dashboard loads", r.status_code == 200 and "Admin Dashboard" in r.text)
    
    return "Admin Dashboard" in r.text


def test_admin_routes(session, results):
    """Test admin-only routes"""
    print("\n--- Testing Admin Routes ---")
    
    # Dashboard
    r = session.get(f"{BASE_URL}/admin/dashboard")
    results.add("Admin dashboard accessible", r.status_code == 200)
    
    # Rooms list
    r = session.get(f"{BASE_URL}/admin/rooms")
    results.add("Admin rooms list loads", r.status_code == 200 and "Manage Rooms" in r.text)
    
    # Add room page
    r = session.get(f"{BASE_URL}/admin/rooms/add")
    results.add("Add room page loads", r.status_code == 200 and "Add New Room" in r.text)
    
    # Add a test room
    r = session.post(f"{BASE_URL}/admin/rooms/add", data={
        "name": "Test Room",
        "capacity": 5,
        "equipment": "Test Equipment",
        "price_per_hour": 15.00,
        "status": "available"
    }, allow_redirects=False)
    results.add("Add room form submits", r.status_code == 302)
    
    # Check room was added
    r = session.get(f"{BASE_URL}/admin/rooms")
    results.add("New room appears in list", "Test Room" in r.text)
    
    # All bookings page
    r = session.get(f"{BASE_URL}/admin/bookings")
    results.add("Admin bookings page loads", r.status_code == 200 and "All Bookings" in r.text)
    
    # Payments page
    r = session.get(f"{BASE_URL}/admin/payments")
    results.add("Admin payments page loads", r.status_code == 200 and "Payment Records" in r.text)


def test_patron_registration(session, results):
    """Test patron registration"""
    print("\n--- Testing Patron Registration ---")
    
    # Register new patron
    r = session.post(f"{BASE_URL}/register", data={
        "username": "testpatron",
        "email": "testpatron@test.com",
        "password": "test123",
        "confirm_password": "test123"
    }, allow_redirects=False)
    results.add("Patron registration submits", r.status_code == 302)


def test_patron_login(session, results):
    """Test patron login"""
    print("\n--- Testing Patron Login ---")
    
    # Login as patron
    r = session.post(f"{BASE_URL}/login", data={
        "username": "testpatron",
        "password": "test123"
    }, allow_redirects=False)
    results.add("Patron login redirects", r.status_code == 302)
    
    # Check dashboard access
    r = session.get(f"{BASE_URL}/patron/dashboard")
    results.add("Patron dashboard loads", r.status_code == 200 and "Welcome" in r.text)
    
    return "Welcome" in r.text


def test_patron_routes(session, results):
    """Test patron routes"""
    print("\n--- Testing Patron Routes ---")
    
    # Dashboard
    r = session.get(f"{BASE_URL}/patron/dashboard")
    results.add("Patron dashboard accessible", r.status_code == 200)
    
    # Browse rooms
    r = session.get(f"{BASE_URL}/patron/rooms")
    results.add("Browse rooms page loads", r.status_code == 200 and "Available Rooms" in r.text)
    
    # My bookings
    r = session.get(f"{BASE_URL}/patron/my-bookings")
    results.add("My bookings page loads", r.status_code == 200 and "My Bookings" in r.text)


def test_booking_flow(session, results):
    """Test the complete booking flow with payment"""
    print("\n--- Testing Booking Flow ---")
    
    # Get room to book (first available)
    r = session.get(f"{BASE_URL}/patron/rooms")
    if "Book This Room" not in r.text:
        results.add("Rooms available for booking", False, "No rooms available")
        return
    results.add("Rooms available for booking", True)
    
    # Book room ID 1 with a unique time slot (using timestamp to avoid conflicts)
    import random
    import time
    future_date = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
    # Use minutes from timestamp to get unique slot
    unique_slot = int(time.time()) % 9 + 8  # 8-16
    
    r = session.post(f"{BASE_URL}/patron/book/1", data={
        "date": future_date,
        "start_time": f"{unique_slot:02d}:00",
        "end_time": f"{unique_slot+1:02d}:00"
    }, allow_redirects=False)
    
    location = r.headers.get("Location", "")
    
    if r.status_code == 302 and "checkout" in location:
        results.add("Booking redirects to checkout", True)
        
        # Build full URL
        if location.startswith("/"):
            checkout_url = f"{BASE_URL}{location}"
        else:
            checkout_url = location
            
        r = session.get(checkout_url)
        # Check for checkout page content
        has_checkout = "Payment Details" in r.text or "Booking Summary" in r.text or "pay" in r.text.lower()
        
        if not has_checkout:
            if "Reservation not found" in r.text or "already processed" in r.text:
                results.add("Checkout page loads", False, "Reservation already processed")
            else:
                # Print first 200 chars for debug
                print(f"    Debug: page content snippet: {r.text[:200]}...")
                results.add("Checkout page loads", False, "Content mismatch")
        else:
            results.add("Checkout page loads", True)
        
        # Get reservation ID from URL
        if "/checkout/" in location:
            reservation_id = location.split("/checkout/")[-1]
            
            # Submit payment
            r = session.post(f"{BASE_URL}/patron/checkout/{reservation_id}", data={
                "payment_method": "Online Banking",
                "bank_name": "Maybank",
                "account_number": "1234567890",
                "account_holder": "Test Patron"
            }, allow_redirects=False)
            
            post_location = r.headers.get("Location", "")
            is_receipt = "receipt" in post_location
            results.add("Payment submission redirects", r.status_code == 302 and is_receipt, 
                       f"Status: {r.status_code}, To: {post_location}")
            
            # Check receipt
            if r.status_code == 302 and is_receipt:
                if post_location.startswith("/"):
                    receipt_url = f"{BASE_URL}{post_location}"
                else:
                    receipt_url = post_location
                    
                r = session.get(receipt_url)
                has_receipt = "Payment Successful" in r.text or "Receipt" in r.text or "Transaction" in r.text
                has_txn = "TXN-" in r.text
                results.add("Receipt page loads", r.status_code == 200 and has_receipt, 
                           f"Status: {r.status_code}")
                results.add("Transaction ID shown", has_txn)
            else:
                results.add("Receipt page loads", False, f"Redirected to: {post_location}")
                results.add("Transaction ID shown", False)
    elif r.status_code == 302 and "my-bookings" in location:
        # Time slot conflict - try again with different slot
        results.add("Booking redirects to checkout", False, "Time slot conflict - try running setup_db.py first")
    else:
        results.add("Booking redirects to checkout", False, f"Status: {r.status_code}, Location: {location}")


def test_authorization(results):
    """Test that unauthorized access is blocked"""
    print("\n--- Testing Authorization ---")
    
    # Unauthenticated user trying admin routes
    r = requests.get(f"{BASE_URL}/admin/dashboard", allow_redirects=False)
    results.add("Admin dashboard requires login", r.status_code == 302)
    
    r = requests.get(f"{BASE_URL}/patron/dashboard", allow_redirects=False)
    results.add("Patron dashboard requires login", r.status_code == 302)
    
    # Patron trying to access admin routes
    patron_session = requests.Session()
    patron_session.post(f"{BASE_URL}/login", data={
        "username": "testpatron",
        "password": "test123"
    })
    
    r = patron_session.get(f"{BASE_URL}/admin/dashboard", allow_redirects=False)
    results.add("Patron blocked from admin dashboard", r.status_code == 302 or "Access denied" in r.text)


def main():
    print("="*60)
    print("LIBRARY ROOM RESERVATION SYSTEM - ROUTE TESTS")
    print("="*60)
    print(f"Testing against: {BASE_URL}")
    
    results = TestResult()
    
    try:
        # Test connection
        r = requests.get(f"{BASE_URL}/login", timeout=5)
        if r.status_code != 200:
            print(f"\nERROR: Cannot connect to {BASE_URL}")
            print("Make sure the Flask app is running: python app.py")
            return
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Cannot connect to {BASE_URL}")
        print("Make sure the Flask app is running: python app.py")
        return
    
    # Run tests
    test_public_routes(results)
    
    # Admin tests
    admin_session = requests.Session()
    if test_admin_login(admin_session, results):
        test_admin_routes(admin_session, results)
    
    # Logout admin
    admin_session.get(f"{BASE_URL}/logout")
    
    # Patron tests
    patron_session = requests.Session()
    test_patron_registration(patron_session, results)
    
    # New session for patron login
    patron_session = requests.Session()
    if test_patron_login(patron_session, results):
        test_patron_routes(patron_session, results)
        test_booking_flow(patron_session, results)
    
    # Authorization tests
    test_authorization(results)
    
    # Summary
    results.summary()
    
    if results.failed == 0:
        print("\nAll tests passed! The system is working correctly.")
    else:
        print(f"\n{results.failed} test(s) failed. Please review the results above.")


if __name__ == "__main__":
    main()

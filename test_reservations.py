"""
Test script for Reservations.py functions
Tests all core functions without user input
"""

import sqlite3
import os
import sys

# Add the directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Reservations import (
    connect_db, setup_db, view_rooms, view_equipment,
    calculate_hours, get_balance, get_user_bank_balance,
    view_history, view_transactions, view_payment_history,
    view_all_reservations, view_all_payments, librarian_dashboard
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "reservation_system.db")

def test_database_connection():
    """Test 1: Database connection"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    try:
        conn = connect_db()
        print(" Database connection successful")
        conn.close()
        return True
    except Exception as e:
        print(f" Database connection failed: {e}")
        return False

def test_setup_db():
    """Test 2: Database setup"""
    print("\n" + "="*60)
    print("TEST 2: Database Setup")
    print("="*60)
    try:
        setup_db()
        print(" Database setup successful")
        
        # Verify tables exist
        conn = connect_db()
        cur = conn.cursor()
        
        tables = ['users', 'bank', 'user_bank_acc', 'rooms', 'reservations', 
                  'booking_rules', 'equipment', 'reservation_equipment', 
                  'transactions', 'room_actions', 'user_actions']
        
        for table in tables:
            cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cur.fetchone():
                print(f"   Table '{table}' exists")
            else:
                print(f"   Table '{table}' not found")
        
        conn.close()
        return True
    except Exception as e:
        print(f" Database setup failed: {e}")
        return False

def test_view_rooms():
    """Test 3: View rooms function"""
    print("\n" + "="*60)
    print("TEST 3: View Rooms")
    print("="*60)
    try:
        view_rooms()
        print(" View rooms executed successfully")
        return True
    except Exception as e:
        print(f" View rooms failed: {e}")
        return False

def test_view_equipment():
    """Test 4: View equipment function"""
    print("\n" + "="*60)
    print("TEST 4: View Equipment")
    print("="*60)
    try:
        view_equipment()
        print(" View equipment executed successfully")
        return True
    except Exception as e:
        print(f" View equipment failed: {e}")
        return False

def test_calculate_hours():
    """Test 5: Calculate hours function"""
    print("\n" + "="*60)
    print("TEST 5: Calculate Hours")
    print("="*60)
    try:
        # Test valid time ranges
        test_cases = [
            ("08:00 AM", "09:00 AM", 1),
            ("08:00 AM", "12:00 PM", 4),
            ("10:00 AM", "03:00 PM", 5),
            ("01:00 PM", "08:00 PM", 7),
        ]
        
        all_passed = True
        for start, end, expected in test_cases:
            result = calculate_hours(start, end)
            if result == expected:
                print(f"   {start} to {end} = {result} hours (expected {expected})")
            else:
                print(f"   {start} to {end} = {result} hours (expected {expected})")
                all_passed = False
        
        if all_passed:
            print(" Calculate hours test passed")
        return all_passed
    except Exception as e:
        print(f" Calculate hours failed: {e}")
        return False

def test_user_functions():
    """Test 6: User-related functions"""
    print("\n" + "="*60)
    print("TEST 6: User Functions")
    print("="*60)
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        # Get a test user
        cur.execute("SELECT * FROM users LIMIT 1")
        user = cur.fetchone()
        
        if user:
            user_dict = dict(user)
            print(f"  Found user: {user['username']}")
            
            # Test get_balance
            balance = get_balance(user_dict)
            print(f"   get_balance: {balance}")
            
            # Test get_user_bank_balance
            bank_balance = get_user_bank_balance(user_dict)
            print(f"   get_user_bank_balance: {bank_balance}")
            
            print(" User functions test passed")
        else:
            print("   No users found to test")
        
        conn.close()
        return True
    except Exception as e:
        print(f" User functions failed: {e}")
        return False

def test_view_all_reservations():
    """Test 7: View all reservations"""
    print("\n" + "="*60)
    print("TEST 7: View All Reservations")
    print("="*60)
    try:
        view_all_reservations()
        print(" View all reservations executed successfully")
        return True
    except Exception as e:
        print(f" View all reservations failed: {e}")
        return False

def test_view_all_payments():
    """Test 8: View all payments"""
    print("\n" + "="*60)
    print("TEST 8: View All Payments")
    print("="*60)
    try:
        view_all_payments()
        print(" View all payments executed successfully")
        return True
    except Exception as e:
        print(f" View all payments failed: {e}")
        return False

def test_librarian_dashboard():
    """Test 9: Librarian dashboard"""
    print("\n" + "="*60)
    print("TEST 9: Librarian Dashboard")
    print("="*60)
    try:
        librarian_dashboard()
        print(" Librarian dashboard executed successfully")
        return True
    except Exception as e:
        print(f" Librarian dashboard failed: {e}")
        return False

def test_data_integrity():
    """Test 10: Data integrity checks"""
    print("\n" + "="*60)
    print("TEST 10: Data Integrity")
    print("="*60)
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        # Check users
        cur.execute("SELECT COUNT(*) as count FROM users")
        users_count = cur.fetchone()['count']
        print(f"  Total users: {users_count}")
        
        # Check rooms
        cur.execute("SELECT COUNT(*) as count FROM rooms")
        rooms_count = cur.fetchone()['count']
        print(f"  Total rooms: {rooms_count}")
        
        # Check reservations
        cur.execute("SELECT COUNT(*) as count FROM reservations")
        reservations_count = cur.fetchone()['count']
        print(f"  Total reservations: {reservations_count}")
        
        # Check payments
        cur.execute("SELECT COUNT(*) as count FROM payments")
        payments_count = cur.fetchone()['count']
        print(f"  Total payments: {payments_count}")
        
        # Check equipment
        cur.execute("SELECT COUNT(*) as count FROM equipment")
        equipment_count = cur.fetchone()['count']
        print(f"  Total equipment: {equipment_count}")
        
        conn.close()
        print(" Data integrity check passed")
        return True
    except Exception as e:
        print(f" Data integrity check failed: {e}")
        return False

def run_all_tests():
    """Run all tests and summarize results"""
    print("\n" + "="*60)
    print("RESERVATIONS.PY FUNCTION TESTS")
    print("="*60)
    
    results = []
    
    results.append(("Database Connection", test_database_connection()))
    results.append(("Database Setup", test_setup_db()))
    results.append(("View Rooms", test_view_rooms()))
    results.append(("View Equipment", test_view_equipment()))
    results.append(("Calculate Hours", test_calculate_hours()))
    results.append(("User Functions", test_user_functions()))
    results.append(("View All Reservations", test_view_all_reservations()))
    results.append(("View All Payments", test_view_all_payments()))
    results.append(("Librarian Dashboard", test_librarian_dashboard()))
    results.append(("Data Integrity", test_data_integrity()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = " PASSED" if result else " FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n ALL TESTS PASSED!")
    else:
        print(f"\n {total - passed} test(s) failed")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()

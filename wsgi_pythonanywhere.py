"""
WSGI Configuration File for PythonAnywhere
===========================================

This file should be used as the WSGI configuration in PythonAnywhere.

IMPORTANT: Replace 'yourusername' with your actual PythonAnywhere username!

To use this:
1. Go to PythonAnywhere Web tab
2. Click on WSGI configuration file
3. Replace ALL content with this file's content
4. Update 'yourusername' to your actual username
5. Save the file
6. Reload your web app
"""

import sys
import os

# ============================================
# CONFIGURATION - UPDATE THIS!
# ============================================
# Replace 'yourusername' with your PythonAnywhere username
PYTHONANYWHERE_USERNAME = 'yourusername'

# ============================================
# PATH CONFIGURATION
# ============================================
# Add your project directory to the sys.path
project_home = f'/home/{PYTHONANYWHERE_USERNAME}/reservation-system'

if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# ============================================
# ENVIRONMENT VARIABLES
# ============================================
os.environ['FLASK_ENV'] = 'production'

# Optional: Set custom database path if needed
# os.environ['DATABASE_PATH'] = f'/home/{PYTHONANYWHERE_USERNAME}/reservation-system/reservation_system.db'

# ============================================
# IMPORT FLASK APPLICATION
# ============================================
# Import your Flask app from app.py
# The variable must be named 'application' for PythonAnywhere
from app import app as application

# ============================================
# OPTIONAL: Application startup checks
# ============================================
# You can add startup checks here if needed
# For example, verify database exists:

# import sqlite3
# db_path = f'/home/{PYTHONANYWHERE_USERNAME}/reservation-system/reservation_system.db'
# if not os.path.exists(db_path):
#     print(f"WARNING: Database not found at {db_path}")
#     print("Run: python setup_db.py to create the database")

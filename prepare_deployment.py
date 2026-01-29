#!/usr/bin/env python3
"""
Pre-Deployment Preparation Script
==================================

This script helps you prepare your Flask application for PythonAnywhere deployment.

Run this script BEFORE uploading to PythonAnywhere to:
- Generate a secure secret key
- Check for required files
- Validate configuration
- Create a deployment summary

Usage:
    python prepare_deployment.py
"""

import os
import secrets
import sys
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_success(f"Found: {filepath}")
        return True
    else:
        if required:
            print_error(f"Missing (required): {filepath}")
        else:
            print_warning(f"Missing (optional): {filepath}")
        return False

def check_required_files():
    """Check if all required files exist"""
    print_header("Checking Required Files")
    
    required_files = [
        'app.py',
        'Reservations.py',
        'requirements.txt',
        'setup_db.py',
    ]
    
    optional_files = [
        'reservation_system.db',
        'PYTHONANYWHERE_DEPLOYMENT_GUIDE.md',
        'DEPLOYMENT_CHECKLIST.md',
    ]
    
    directories = [
        'templates',
        'static',
    ]
    
    all_good = True
    
    print("Required Files:")
    for file in required_files:
        if not check_file_exists(file):
            all_good = False
    
    print("\nRequired Directories:")
    for directory in directories:
        if not check_file_exists(directory):
            all_good = False
    
    print("\nOptional Files:")
    for file in optional_files:
        check_file_exists(file, required=False)
    
    return all_good

def generate_secret_key():
    """Generate a secure secret key"""
    print_header("Generating Secure Secret Key")
    
    secret_key = secrets.token_hex(32)
    
    print_info("Your new secure secret key:")
    print(f"\n{Colors.BOLD}{secret_key}{Colors.END}\n")
    
    print_warning("IMPORTANT: Copy this key and update it in app.py (line 16)")
    print_info("Replace: app.secret_key = 'your-secret-key-change-this-in-production'")
    print_info(f"With:    app.secret_key = '{secret_key}'")
    
    return secret_key

def check_app_configuration():
    """Check app.py configuration"""
    print_header("Checking app.py Configuration")
    
    issues = []
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            
            # Check secret key
            if 'your-secret-key-change-this-in-production' in content:
                print_warning("Secret key still using default value")
                issues.append("Update secret key in app.py")
            else:
                print_success("Secret key has been changed")
            
            # Check debug mode
            if 'debug=True' in content:
                print_warning("Debug mode is enabled (should be False for production)")
                issues.append("Set debug=False in app.py")
            else:
                print_success("Debug mode is disabled")
            
            # Check host binding
            if "host='0.0.0.0'" in content:
                print_success("Host binding configured")
            
    except FileNotFoundError:
        print_error("app.py not found!")
        issues.append("app.py is missing")
    
    return issues

def check_requirements():
    """Check requirements.txt"""
    print_header("Checking requirements.txt")
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            
            required_packages = ['Flask', 'bcrypt', 'pytz']
            
            for package in required_packages:
                if package.lower() in content.lower():
                    print_success(f"{package} is listed")
                else:
                    print_warning(f"{package} is not listed")
            
            # Check for unnecessary packages
            if 'mysql' in content.lower():
                print_warning("MySQL connector found (not needed for SQLite)")
                print_info("Consider removing mysql-connector-python")
            
    except FileNotFoundError:
        print_error("requirements.txt not found!")

def count_templates():
    """Count template files"""
    print_header("Checking Templates")
    
    if not os.path.exists('templates'):
        print_error("templates/ directory not found!")
        return
    
    html_files = list(Path('templates').rglob('*.html'))
    
    print_info(f"Found {len(html_files)} HTML template files:")
    
    for template in sorted(html_files):
        print(f"  • {template}")
    
    if len(html_files) == 0:
        print_warning("No HTML templates found!")

def count_static_files():
    """Count static files"""
    print_header("Checking Static Files")
    
    if not os.path.exists('static'):
        print_warning("static/ directory not found!")
        return
    
    css_files = list(Path('static').rglob('*.css'))
    js_files = list(Path('static').rglob('*.js'))
    img_files = list(Path('static').rglob('*.png')) + \
                list(Path('static').rglob('*.jpg')) + \
                list(Path('static').rglob('*.jpeg')) + \
                list(Path('static').rglob('*.gif'))
    
    print_info(f"CSS files: {len(css_files)}")
    print_info(f"JavaScript files: {len(js_files)}")
    print_info(f"Image files: {len(img_files)}")

def create_deployment_summary(secret_key, issues):
    """Create a deployment summary file"""
    print_header("Creating Deployment Summary")
    
    summary = f"""# Deployment Summary
Generated: {os.popen('date').read().strip()}

## Generated Secret Key
```
{secret_key}
```

## Pre-Deployment Checklist

### Files Ready
- [{'x' if os.path.exists('app.py') else ' '}] app.py
- [{'x' if os.path.exists('Reservations.py') else ' '}] Reservations.py
- [{'x' if os.path.exists('requirements.txt') else ' '}] requirements.txt
- [{'x' if os.path.exists('setup_db.py') else ' '}] setup_db.py
- [{'x' if os.path.exists('templates') else ' '}] templates/
- [{'x' if os.path.exists('static') else ' '}] static/

### Configuration Issues
"""
    
    if issues:
        for issue in issues:
            summary += f"- [ ] {issue}\n"
    else:
        summary += "- [x] No issues found!\n"
    
    summary += """
## Next Steps

1. Update secret key in app.py
2. Set debug=False in app.py
3. Upload to PythonAnywhere (via Git or Files tab)
4. Follow PYTHONANYWHERE_DEPLOYMENT_GUIDE.md

## PythonAnywhere Commands

```bash
# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 reservation-env

# Install dependencies
pip install -r requirements.txt

# Initialize database
python setup_db.py
```

## Your App URL
After deployment: https://YOUR_USERNAME.pythonanywhere.com

Good luck! 🚀
"""
    
    with open('DEPLOYMENT_SUMMARY.md', 'w') as f:
        f.write(summary)
    
    print_success("Created DEPLOYMENT_SUMMARY.md")

def main():
    """Main function"""
    print_header("PythonAnywhere Deployment Preparation")
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print_error("app.py not found!")
        print_info("Please run this script from your project root directory")
        sys.exit(1)
    
    # Run all checks
    files_ok = check_required_files()
    secret_key = generate_secret_key()
    issues = check_app_configuration()
    check_requirements()
    count_templates()
    count_static_files()
    
    # Create summary
    create_deployment_summary(secret_key, issues)
    
    # Final summary
    print_header("Summary")
    
    if files_ok and not issues:
        print_success("Your project is ready for deployment!")
        print_info("Next steps:")
        print("  1. Update the secret key in app.py")
        print("  2. Review DEPLOYMENT_SUMMARY.md")
        print("  3. Follow PYTHONANYWHERE_DEPLOYMENT_GUIDE.md")
    else:
        print_warning("Please fix the issues above before deploying")
        print_info("Check DEPLOYMENT_SUMMARY.md for details")
    
    print()

if __name__ == '__main__':
    main()

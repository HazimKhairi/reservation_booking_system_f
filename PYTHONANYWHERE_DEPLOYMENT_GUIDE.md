# PythonAnywhere Deployment Guide
## Library Room Reservation System

This guide will walk you through deploying your Flask reservation booking system to PythonAnywhere.

---

## Prerequisites

1. **PythonAnywhere Account**: Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
   - Free tier supports one web app
   - Recommended: Beginner ($5/month) or Hacker ($12/month) for custom domains

2. **Project Files Ready**: Ensure your project is complete and tested locally

---

## Step 1: Prepare Your Project

### 1.1 Update `requirements.txt`

Your current `requirements.txt` needs to be updated. Create a complete version:

```txt
Flask==3.0.0
bcrypt==4.1.2
pytz==2024.1
```

> [!NOTE]
> Remove `mysql-connector-python` since you're using SQLite, not MySQL.

### 1.2 Update Secret Key in `app.py`

Before deploying, change the secret key in `app.py` (line 16):

```python
# Change from:
app.secret_key = 'your-secret-key-change-this-in-production'

# To something secure (generate a random string):
app.secret_key = 'your-secure-random-key-here-make-it-long-and-complex'
```

You can generate a secure key using Python:
```python
import secrets
print(secrets.token_hex(32))
```

---

## Step 2: Upload Your Project to PythonAnywhere

### Option A: Using Git (Recommended)

1. **Initialize Git repository locally** (if not already done):
   ```bash
   cd /Applications/XAMPP/xamppfiles/htdocs/CLIENT_PROJECT/reservation_booking_system_f
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Push to GitHub/GitLab**:
   - Create a repository on GitHub
   - Push your code:
   ```bash
   git remote add origin https://github.com/yourusername/reservation-system.git
   git push -u origin main
   ```

3. **Clone on PythonAnywhere**:
   - Log into PythonAnywhere
   - Open a Bash console
   - Clone your repository:
   ```bash
   git clone https://github.com/yourusername/reservation-system.git
   cd reservation-system
   ```

### Option B: Direct Upload

1. Log into PythonAnywhere
2. Go to **Files** tab
3. Navigate to `/home/yourusername/`
4. Create a new directory: `reservation-system`
5. Upload all your project files using the upload button

---

## Step 3: Set Up Virtual Environment

In the PythonAnywhere **Bash console**:

```bash
# Navigate to your project directory
cd ~/reservation-system

# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 reservation-env

# Activate it (should auto-activate after creation)
workon reservation-env

# Install dependencies
pip install -r requirements.txt
```

---

## Step 4: Initialize Database

In the same Bash console:

```bash
# Make sure you're in the project directory
cd ~/reservation-system

# Run the database setup script
python setup_db.py
```

This will create `reservation_system.db` with all necessary tables and default data.

---

## Step 5: Configure Web App

1. Go to the **Web** tab in PythonAnywhere
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"** (not Flask wizard)
4. Select **Python 3.10**

### 5.1 Configure WSGI File

1. Click on the **WSGI configuration file** link
2. Delete all existing content
3. Add this configuration:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/reservation-system'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables (optional)
os.environ['FLASK_ENV'] = 'production'

# Import the Flask app
from app import app as application
```

> [!IMPORTANT]
> Replace `yourusername` with your actual PythonAnywhere username!

4. Click **Save**

### 5.2 Configure Virtual Environment

1. In the **Web** tab, scroll to **"Virtualenv"** section
2. Enter the path to your virtual environment:
   ```
   /home/yourusername/.virtualenvs/reservation-env
   ```

### 5.3 Configure Static Files

In the **Web** tab, scroll to **"Static files"** section:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/reservation-system/static/` |

---

## Step 6: Update Application Settings

### 6.1 Modify `app.py` for Production

Update the last line in `app.py`:

```python
# Change from:
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)

# To:
if __name__ == '__main__':
    app.run(debug=False)  # Set debug=False for production
```

> [!WARNING]
> Never run with `debug=True` in production - it's a security risk!

### 6.2 Database Path (Optional)

Your current code uses:
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "reservation_system.db")
```

This should work fine on PythonAnywhere. The database will be created in your project directory.

---

## Step 7: Reload and Test

1. In the **Web** tab, click the big green **"Reload"** button
2. Visit your site: `https://yourusername.pythonanywhere.com`
3. Test the login with default credentials:
   - **Username**: `admin`
   - **Password**: `admin123`

---

## Step 8: Troubleshooting

### Check Error Logs

If your site doesn't load:

1. Go to **Web** tab
2. Scroll to **"Log files"** section
3. Check:
   - **Error log**: Shows Python errors
   - **Server log**: Shows web server errors
   - **Access log**: Shows HTTP requests

### Common Issues

#### Issue: "ImportError: No module named flask"

**Solution**: Virtual environment not configured correctly
```bash
workon reservation-env
pip install -r requirements.txt
```
Then update the virtualenv path in the Web tab.

#### Issue: "Database is locked"

**Solution**: SQLite can have issues with concurrent access. For production, consider:
- Upgrading to a paid PythonAnywhere account with MySQL
- Or keep SQLite but limit concurrent users

#### Issue: "Template not found"

**Solution**: Check that `templates/` directory is uploaded and in the correct location:
```bash
cd ~/reservation-system
ls -la templates/
```

#### Issue: Static files (CSS/JS) not loading

**Solution**: Verify static files configuration in Web tab matches your directory structure.

---

## Step 9: Post-Deployment Tasks

### 9.1 Create Admin Account

If you need to create additional admin accounts:

```bash
cd ~/reservation-system
workon reservation-env
python
```

Then in Python shell:
```python
from Reservations import connect_db
import bcrypt

conn = connect_db()
cur = conn.cursor()

# Create new admin
hashed_pw = bcrypt.hashpw('newpassword'.encode('utf-8'), bcrypt.gensalt())
cur.execute("""
    INSERT INTO users (name, student_id, faculty, username, password, role)
    VALUES (?, ?, ?, ?, ?, ?)
""", ('Admin Name', '-', 'Library', 'newadmin', hashed_pw.decode('utf-8'), 'librarian'))

conn.commit()
conn.close()
```

### 9.2 Regular Backups

Download your database regularly:

1. Go to **Files** tab
2. Navigate to `/home/yourusername/reservation-system/`
3. Download `reservation_system.db`

Or use the Bash console:
```bash
# Create backup
cp ~/reservation-system/reservation_system.db ~/reservation_system_backup_$(date +%Y%m%d).db
```

### 9.3 Update Code

When you make changes:

**If using Git:**
```bash
cd ~/reservation-system
git pull origin main
workon reservation-env
pip install -r requirements.txt  # If dependencies changed
```

**Then reload** the web app from the Web tab.

---

## Step 10: Custom Domain (Optional)

If you have a custom domain:

1. Upgrade to a paid PythonAnywhere account
2. Go to **Web** tab
3. Add your domain in the **"Domain name"** section
4. Update your domain's DNS settings:
   - Add a CNAME record pointing to `yourusername.pythonanywhere.com`

---

## Security Checklist

- [ ] Changed `app.secret_key` to a secure random value
- [ ] Set `debug=False` in production
- [ ] Changed default admin password
- [ ] Database file permissions are correct
- [ ] HTTPS is enabled (automatic on PythonAnywhere)
- [ ] Regular database backups scheduled

---

## Performance Tips

1. **Enable HTTPS**: PythonAnywhere provides free HTTPS
2. **Monitor Usage**: Check the Web tab for daily CPU usage
3. **Optimize Queries**: Add indexes to frequently queried columns
4. **Consider Upgrading**: If you get high traffic, upgrade your account

---

## Support Resources

- **PythonAnywhere Help**: [help.pythonanywhere.com](https://help.pythonanywhere.com)
- **Forums**: [pythonanywhere.com/forums](https://www.pythonanywhere.com/forums/)
- **Flask Documentation**: [flask.palletsprojects.com](https://flask.palletsprojects.com)

---

## Quick Reference Commands

```bash
# Activate virtual environment
workon reservation-env

# Update code from Git
cd ~/reservation-system && git pull

# Restart web app (alternative to Web tab)
touch /var/www/yourusername_pythonanywhere_com_wsgi.py

# View logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# Backup database
cp ~/reservation-system/reservation_system.db ~/backups/db_$(date +%Y%m%d).db
```

---

## Next Steps

After successful deployment:

1. Test all features thoroughly
2. Create test bookings
3. Verify payment flow
4. Check admin dashboard
5. Share the URL with stakeholders

Your app will be live at: `https://yourusername.pythonanywhere.com`

Good luck with your deployment! 🚀

# 🚀 Quick Start: Deploy to PythonAnywhere

## ⚡ 5-Minute Quick Guide

### Step 1: Sign Up (2 min)
1. Go to **https://www.pythonanywhere.com**
2. Click **"Pricing & signup"**
3. Choose **Free** or **Beginner** ($5/month)
4. Complete registration

### Step 2: Upload Files (3 min)

**Option A: Using Git** (Recommended)
```bash
# On PythonAnywhere Bash Console
git clone https://github.com/YOUR_USERNAME/reservation-system.git
cd reservation-system
```

**Option B: Manual Upload**
1. Go to **Files** tab
2. Upload all project files to `/home/YOUR_USERNAME/reservation-system/`

### Step 3: Setup Environment (5 min)
```bash
# In PythonAnywhere Bash Console
cd ~/reservation-system

# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 reservation-env

# Install dependencies
pip install -r requirements.txt

# Setup database
python setup_db.py
```

### Step 4: Configure Web App (5 min)

1. **Web Tab** → **Add a new web app**
2. Choose **Manual configuration** → **Python 3.10**
3. **WSGI file** → Replace content with:

```python
import sys
import os

# CHANGE 'yourusername' to your actual username!
project_home = '/home/yourusername/reservation-system'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

os.environ['FLASK_ENV'] = 'production'

from app import app as application
```

4. **Virtualenv** → Enter: `/home/yourusername/.virtualenvs/reservation-env`

5. **Static files** → Add:
   - URL: `/static/`
   - Directory: `/home/yourusername/reservation-system/static/`

### Step 5: Reload & Test (1 min)
1. Click **Reload** button (green, top right)
2. Visit: `https://yourusername.pythonanywhere.com`
3. Login: **admin** / **admin123**

---

## 📋 Before Deployment Checklist

- [ ] Update secret key in `app.py` (line 16)
- [ ] Set `debug=False` in `app.py` (line 637)
- [ ] Test locally one more time
- [ ] Have PythonAnywhere account ready

**Your generated secret key:**
```
06f3d1accb4d9f72ff397679f3dd8ce38a3e0201366c457ba6ac674d0a8ec34d
```

---

## 🔧 Common Issues & Fixes

### "ImportError: No module named flask"
```bash
workon reservation-env
pip install -r requirements.txt
```

### "Template not found"
Check files uploaded correctly:
```bash
cd ~/reservation-system
ls -la templates/
```

### "Database is locked"
SQLite limitation - consider upgrading to paid plan with MySQL

### Static files not loading
Verify in Web tab:
- URL: `/static/`
- Directory: `/home/yourusername/reservation-system/static/`

---

## 🎯 Important URLs

| What | URL |
|------|-----|
| **Your App** | `https://yourusername.pythonanywhere.com` |
| **Dashboard** | `https://www.pythonanywhere.com/dashboard` |
| **Web Config** | `https://www.pythonanywhere.com/user/yourusername/webapps/` |
| **Files** | `https://www.pythonanywhere.com/user/yourusername/files/` |
| **Consoles** | `https://www.pythonanywhere.com/user/yourusername/consoles/` |

---

## 📝 Quick Commands

```bash
# Activate environment
workon reservation-env

# Update code (if using Git)
cd ~/reservation-system && git pull

# View error logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# Reload app
touch /var/www/yourusername_pythonanywhere_com_wsgi.py

# Backup database
cp ~/reservation-system/reservation_system.db ~/backup_$(date +%Y%m%d).db
```

---

## 🔐 Default Login

After deployment, login with:
- **Username:** `admin`
- **Password:** `admin123`

**⚠️ IMPORTANT:** Change this password immediately after first login!

---

## 📚 Full Documentation

For detailed instructions, see:
- **[PYTHONANYWHERE_DEPLOYMENT_GUIDE.md](PYTHONANYWHERE_DEPLOYMENT_GUIDE.md)** - Complete guide
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Step-by-step checklist
- **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)** - Visual diagrams
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Your deployment summary

---

## 💡 Pro Tips

1. **Use Git** - Makes updates much easier
2. **Regular Backups** - Download database weekly
3. **Monitor Logs** - Check error logs regularly
4. **Test First** - Always test locally before deploying
5. **Upgrade Plan** - Consider paid plan for better performance

---

## 🆘 Need Help?

- **PythonAnywhere Help:** https://help.pythonanywhere.com
- **Forums:** https://www.pythonanywhere.com/forums/
- **Support:** help@pythonanywhere.com

---

**Total Time:** ~20 minutes for first deployment
**Updates:** ~5 minutes after initial setup

Good luck! 🎉

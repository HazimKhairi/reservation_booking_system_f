# Pre-Deployment Checklist for PythonAnywhere

## Before You Start

- [ ] **Sign up for PythonAnywhere account** at https://www.pythonanywhere.com
  - Free tier is fine for testing
  - Consider paid tier ($5/month) for better performance

## Files to Prepare

- [x] `requirements.txt` - Updated ✓
- [ ] `app.py` - Update secret key (line 16)
- [ ] `app.py` - Set debug=False (line 637)
- [ ] Test locally one more time

## Generate Secure Secret Key

Run this in your terminal:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and replace the secret key in `app.py` line 16.

## Files to Upload

Make sure these are ready:
- [ ] `app.py` (main Flask application)
- [ ] `Reservations.py` (database functions)
- [ ] `requirements.txt` (dependencies)
- [ ] `setup_db.py` (database initialization)
- [ ] `templates/` folder (all HTML templates)
- [ ] `static/` folder (CSS, JS, images)
- [ ] `reservation_system.db` (optional - can create fresh on server)

## Deployment Steps Summary

1. **Upload Code** (via Git or Files tab)
2. **Create Virtual Environment**
3. **Install Dependencies** (`pip install -r requirements.txt`)
4. **Initialize Database** (`python setup_db.py`)
5. **Configure Web App** (WSGI file, virtualenv path)
6. **Reload Web App**
7. **Test!**

## After Deployment

- [ ] Test login with admin/admin123
- [ ] Change admin password
- [ ] Test booking flow
- [ ] Test payment flow
- [ ] Test admin dashboard
- [ ] Set up regular database backups

## Your PythonAnywhere URL

After deployment, your app will be at:
```
https://YOUR_USERNAME.pythonanywhere.com
```

Replace `YOUR_USERNAME` with your PythonAnywhere username.

## Need Help?

Refer to: `PYTHONANYWHERE_DEPLOYMENT_GUIDE.md` for detailed instructions.

## Estimated Time

- First-time deployment: 30-45 minutes
- Updates after initial setup: 5-10 minutes

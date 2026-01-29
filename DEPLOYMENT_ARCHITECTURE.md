# PythonAnywhere Deployment Architecture

## System Overview

```mermaid
graph TB
    A[Your Local Project] -->|Upload via Git/Files| B[PythonAnywhere Server]
    B --> C[Virtual Environment]
    C --> D[Flask Application]
    D --> E[SQLite Database]
    D --> F[Templates]
    D --> G[Static Files]
    
    H[Users] -->|HTTPS| I[PythonAnywhere Web Server]
    I --> J[WSGI Interface]
    J --> D
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style D fill:#e8f5e9
    style H fill:#f3e5f5
```

## Deployment Flow

```mermaid
flowchart LR
    A[1. Sign Up<br/>PythonAnywhere] --> B[2. Upload<br/>Project Files]
    B --> C[3. Create<br/>Virtual Env]
    C --> D[4. Install<br/>Dependencies]
    D --> E[5. Setup<br/>Database]
    E --> F[6. Configure<br/>WSGI]
    F --> G[7. Configure<br/>Web App]
    G --> H[8. Reload &<br/>Test]
    
    style A fill:#ffebee
    style B fill:#fff3e0
    style C fill:#e8f5e9
    style D fill:#e3f2fd
    style E fill:#f3e5f5
    style F fill:#fce4ec
    style G fill:#e0f2f1
    style H fill:#c8e6c9
```

## File Structure on PythonAnywhere

```
/home/yourusername/
├── .virtualenvs/
│   └── reservation-env/          # Virtual environment
│       └── lib/
│           └── python3.10/
│               └── site-packages/ # Installed packages
│
└── reservation-system/            # Your project
    ├── app.py                     # Main Flask app
    ├── Reservations.py            # Database functions
    ├── requirements.txt           # Dependencies
    ├── setup_db.py                # DB initialization
    ├── reservation_system.db      # SQLite database
    │
    ├── templates/                 # HTML templates
    │   ├── login.html
    │   ├── register.html
    │   ├── patron/
    │   │   ├── dashboard.html
    │   │   ├── booking.html
    │   │   └── ...
    │   └── admin/
    │       ├── dashboard.html
    │       └── ...
    │
    └── static/                    # Static files
        ├── css/
        ├── js/
        └── images/
```

## Request Flow

```mermaid
sequenceDiagram
    participant U as User Browser
    participant PA as PythonAnywhere
    participant WSGI as WSGI Handler
    participant Flask as Flask App
    participant DB as SQLite DB
    
    U->>PA: HTTPS Request
    PA->>WSGI: Forward Request
    WSGI->>Flask: Route to Handler
    Flask->>DB: Query Data
    DB-->>Flask: Return Data
    Flask-->>WSGI: Render Template
    WSGI-->>PA: HTML Response
    PA-->>U: HTTPS Response
```

## Web App Configuration

```mermaid
graph LR
    A[Web Tab Settings] --> B[Source Code Path]
    A --> C[WSGI File]
    A --> D[Virtual Env Path]
    A --> E[Static Files]
    
    B -.->|/home/user/reservation-system| F[Project Directory]
    C -.->|Custom WSGI config| G[wsgi.py]
    D -.->|/home/user/.virtualenvs/reservation-env| H[Python Packages]
    E -.->|/static/ → /home/user/.../static/| I[CSS/JS/Images]
    
    style A fill:#e3f2fd
    style F fill:#e8f5e9
    style G fill:#fff3e0
    style H fill:#f3e5f5
    style I fill:#fce4ec
```

## Database Setup Process

```mermaid
flowchart TD
    A[Run setup_db.py] --> B{Database Exists?}
    B -->|No| C[Create Database File]
    B -->|Yes| D[Connect to Existing]
    C --> E[Create Tables]
    D --> E
    E --> F[Create users table]
    E --> G[Create rooms table]
    E --> H[Create reservations table]
    E --> I[Create payments table]
    E --> J[Create other tables]
    
    F --> K[Insert Default Admin]
    G --> L[Ready to Use]
    H --> L
    I --> L
    J --> L
    K --> L
    
    style A fill:#e3f2fd
    style C fill:#e8f5e9
    style L fill:#c8e6c9
```

## Security Layers

```mermaid
graph TB
    A[User Request] --> B[HTTPS Encryption]
    B --> C[PythonAnywhere Firewall]
    C --> D[Flask Session Management]
    D --> E[Password Hashing bcrypt]
    E --> F[Database Access Control]
    
    style B fill:#ffebee
    style C fill:#fff3e0
    style D fill:#e8f5e9
    style E fill:#e3f2fd
    style F fill:#f3e5f5
```

## Monitoring & Maintenance

```mermaid
graph LR
    A[Your Web App] --> B[Error Logs]
    A --> C[Server Logs]
    A --> D[Access Logs]
    
    B --> E[Debug Issues]
    C --> E
    D --> F[Monitor Traffic]
    
    A --> G[Database Backups]
    G --> H[Regular Downloads]
    
    A --> I[Code Updates]
    I --> J[Git Pull]
    J --> K[Reload App]
    
    style A fill:#e3f2fd
    style E fill:#ffebee
    style F fill:#e8f5e9
    style H fill:#fff3e0
    style K fill:#c8e6c9
```

## Troubleshooting Decision Tree

```mermaid
flowchart TD
    A[App Not Loading?] --> B{Check Error Log}
    B -->|Import Error| C[Check Virtual Env]
    B -->|Template Error| D[Check Templates Path]
    B -->|Database Error| E[Check DB File Exists]
    B -->|500 Error| F[Check WSGI Config]
    
    C --> G[Reinstall Dependencies]
    D --> H[Verify Upload Complete]
    E --> I[Run setup_db.py]
    F --> J[Update WSGI File]
    
    G --> K[Reload App]
    H --> K
    I --> K
    J --> K
    
    K --> L{Working?}
    L -->|Yes| M[Success!]
    L -->|No| N[Check Forums/Support]
    
    style A fill:#ffebee
    style M fill:#c8e6c9
    style N fill:#fff3e0
```

---

## Key URLs After Deployment

| Resource | URL Pattern |
|----------|-------------|
| **Your Web App** | `https://yourusername.pythonanywhere.com` |
| **Admin Login** | `https://yourusername.pythonanywhere.com/login` |
| **Files Manager** | `https://www.pythonanywhere.com/user/yourusername/files/` |
| **Web Config** | `https://www.pythonanywhere.com/user/yourusername/webapps/` |
| **Consoles** | `https://www.pythonanywhere.com/user/yourusername/consoles/` |

---

## Quick Commands Reference

### On PythonAnywhere Bash Console

```bash
# Navigate to project
cd ~/reservation-system

# Activate virtual environment
workon reservation-env

# Install/Update dependencies
pip install -r requirements.txt

# Initialize database
python setup_db.py

# Check database
python check_db.py

# View error logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# Reload web app (alternative to Web tab)
touch /var/www/yourusername_pythonanywhere_com_wsgi.py
```

### Local Development

```bash
# Test locally before deploying
cd /Applications/XAMPP/xamppfiles/htdocs/CLIENT_PROJECT/reservation_booking_system_f
python app.py

# Access at: http://localhost:5002
```

---

This visual guide complements the detailed deployment guide in `PYTHONANYWHERE_DEPLOYMENT_GUIDE.md`.

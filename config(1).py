"""
Cityscope Accounts — Configuration
MySQL connection settings and Flask config.
"""

import os
from pathlib import Path
from datetime import timedelta

# Auto-load .env file if it exists
env_path = Path(__file__).resolve().parent / '.env'
if env_path.is_file():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and (k not in os.environ or not os.environ[k]):
                    os.environ[k] = v

# MySQL Database Configuration
MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'root'
MYSQL_DB = os.environ.get('MYSQL_DB') or 'cityscope_accounts'

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    import secrets
    SECRET_KEY = secrets.token_hex(32)
    if os.environ.get('FLASK_ENV') == 'production':
        raise ValueError("SECRET_KEY must be set in production environment!")

PERMANENT_SESSION_LIFETIME = timedelta(days=7)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF Configuration
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = 3600
WTF_CSRF_SSL_STRICT = os.environ.get('FLASK_ENV') == 'production'

# Security Headers
TALISMAN_ENABLED = os.environ.get('FLASK_ENV') == 'production'

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
SECRET_KEY = os.environ.get('SECRET_KEY') or 'cityscope-secret-key-change-in-production-2024'
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
SESSION_COOKIE_HTTPONLY = True

"""
Cityscope Accounts — Configuration
MySQL connection settings and Flask config.
"""

import os
from datetime import timedelta

# MySQL Database Configuration
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root')
MYSQL_DB = os.environ.get('MYSQL_DB', 'cityscope_accounts')

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'cityscope-secret-key-change-in-production-2024')
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
SESSION_COOKIE_HTTPONLY = True

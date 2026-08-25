"""
Cityscope Accounts — Authentication Helpers
Password hashing, session management, and route-protection decorators.
"""

from functools import wraps
from flask import session, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plaintext password using werkzeug (pbkdf2:sha256)."""
    return generate_password_hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against its hash."""
    return check_password_hash(hashed, password)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def get_current_user():
    """Read user_id from session and fetch the full user record.

    Returns a dict with user fields or None if not authenticated.
    Uses Flask's `g` object to cache within a request.
    """
    if hasattr(g, '_current_user'):
        return g._current_user

    user_id = session.get('user_id')
    if not user_id:
        g._current_user = None
        return None

    # Import here to avoid circular imports
    from models import get_user_by_id
    user = get_user_by_id(user_id)
    g._current_user = user
    return user


# ---------------------------------------------------------------------------
# Route-protection decorators
# ---------------------------------------------------------------------------

def login_required(f):
    """Decorator: redirect to /login if the user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: require ADMIN role. Redirects employees to /employee."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return redirect(url_for('login'))
        if user['role'] != 'ADMIN':
            return redirect(url_for('employee_dashboard'))
        return f(*args, **kwargs)
    return decorated

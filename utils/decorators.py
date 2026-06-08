"""
EventEase — Auth & Role Decorators
"""

from functools import wraps
from flask import session, redirect, url_for, flash, abort


def login_required(f):
    """Redirect to login if user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(role):
    """Restrict access to a specific role. Returns 403 if mismatch."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

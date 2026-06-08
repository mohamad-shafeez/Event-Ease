"""
EventEase — Authentication Routes
Handles register, login, logout for all three roles.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import bcrypt
from models.user_model import create_user, get_user_by_email

auth_bp = Blueprint('auth', __name__)


# ── Register ────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return _redirect_by_role(session.get('role'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        role = request.form.get('role', 'user')

        # ── Validation ──
        if not all([name, email, password, confirm]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        if role not in ('user', 'creator'):
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        if get_user_by_email(email):
            flash('An account with this email already exists.', 'danger')
            return redirect(url_for('auth.register'))

        # ── Create user ──
        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        create_user(name, email, pw_hash, role)

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# ── Login ───────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return _redirect_by_role(session.get('role'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not all([email, password]):
            flash('Please enter both email and password.', 'danger')
            return redirect(url_for('auth.login'))

        user = get_user_by_email(email)

        if not user or not bcrypt.check_password_hash(user['password_hash'], password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        if user['is_banned']:
            flash('Your account has been suspended. Contact support.', 'danger')
            return redirect(url_for('auth.login'))

        # ── Set session ──
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['user_name'] = user['name']
        session['user_email'] = user['email']

        flash(f'Welcome back, {user["name"]}!', 'success')
        return _redirect_by_role(user['role'])

    return render_template('auth/login.html')


# ── Logout ──────────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ── Helper ──────────────────────────────────────────────
def _redirect_by_role(role):
    """Redirect to the appropriate dashboard based on role."""
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'creator':
        return redirect(url_for('creator.dashboard'))
    return redirect(url_for('user.dashboard'))

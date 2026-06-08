"""
EventEase — Password Reset Routes
Handles forgot password and token-based reset flow.
"""
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query
from extensions import bcrypt
from utils.email_sender import send_password_reset_email

password_reset_bp = Blueprint('password_reset', __name__)

@password_reset_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = query("SELECT id, name FROM users WHERE email=%s", (email,), fetchone=True)
        
        if user:
            token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(hours=1)
            
            query(
                "INSERT INTO password_resets (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user['id'], token, expires)
            )
            
            reset_url = url_for('password_reset.reset_password', token=token, _external=True)
            send_password_reset_email(email, user['name'], reset_url)
            
        # Always show success flash to prevent email enumeration
        flash('If that email exists in our system, a password reset link has been sent.', 'success')
        return render_template('auth/forgot_password.html', success=True)
        
    return render_template('auth/forgot_password.html', success=False)

@password_reset_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Validate token
    reset_record = query(
        "SELECT * FROM password_resets WHERE token=%s", (token,), fetchone=True
    )
    
    if not reset_record:
        flash('Invalid reset link.', 'danger')
        return redirect(url_for('password_reset.forgot_password'))
        
    if reset_record['used']:
        flash('This link has already been used.', 'warning')
        return redirect(url_for('password_reset.forgot_password'))
        
    if reset_record['expires_at'] < datetime.now():
        flash('This link has expired. Please request a new one.', 'warning')
        return redirect(url_for('password_reset.forgot_password'))

    if request.method == 'POST':
        new_pw = request.form.get('password')
        confirm_pw = request.form.get('confirm_password')
        
        if not new_pw or new_pw != confirm_pw:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)
            
        if len(new_pw) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/reset_password.html', token=token)
            
        pw_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        
        # Update user
        query("UPDATE users SET password_hash=%s WHERE id=%s", (pw_hash, reset_record['user_id']))
        # Mark token as used
        query("UPDATE password_resets SET used=1 WHERE id=%s", (reset_record['id'],))
        
        flash('Password reset successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', token=token)

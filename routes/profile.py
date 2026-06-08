"""
EventEase — Profile Routes
Handles profile editing and public creator profiles.
"""
import os
import time
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, abort
from werkzeug.utils import secure_filename
from utils.decorators import login_required
from db import query
from extensions import bcrypt

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')
ALLOWED_EXT = {'jpg', 'jpeg', 'png', 'webp'}

def _allowed(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def _save_avatar(file, user_id):
    if not file or not file.filename or not _allowed(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    fname = f"avatar_{user_id}_{int(time.time())}.{ext}"
    folder = os.path.join(current_app.static_folder, 'uploads', 'avatars')
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, fname))
    return f"uploads/avatars/{fname}"

@profile_bp.route('/', methods=['GET'])
@login_required
def index():
    return redirect(url_for('profile.edit'))

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    user_id = session['user_id']
    user = query("SELECT * FROM users WHERE id=%s", (user_id,), fetchone=True)
    if not user:
        abort(404)

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            bio = request.form.get('bio', '').strip()
            
            update_fields = ["name=%s", "phone=%s", "bio=%s"]
            params = [name, phone, bio]

            if user['role'] == 'creator':
                org = request.form.get('organization_name', '').strip()
                web = request.form.get('website_url', '').strip()
                prefs = ",".join(request.form.getlist('preferences'))
                update_fields.extend(["organization_name=%s", "website_url=%s", "preferences=%s"])
                params.extend([org, web, prefs])
            elif user['role'] == 'user':
                city = request.form.get('city', '').strip()
                prefs = ",".join(request.form.getlist('preferences'))
                update_fields.extend(["city=%s", "preferences=%s"])
                params.extend([city, prefs])

            avatar = request.files.get('avatar')
            if avatar and avatar.filename:
                path = _save_avatar(avatar, user_id)
                if path:
                    update_fields.append("avatar=%s")
                    params.append(path)

            params.append(user_id)
            sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id=%s"
            
            try:
                query(sql, tuple(params))
                session['user_name'] = name # Update session name
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                flash(f'Error updating profile: {e}', 'danger')
                
            return redirect(url_for('profile.edit'))
            
        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')
            
            if not bcrypt.check_password_hash(user['password_hash'], current_pw):
                flash('Incorrect current password.', 'danger')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
            elif len(new_pw) < 6:
                flash('Password must be at least 6 characters.', 'danger')
            else:
                pw_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
                query("UPDATE users SET password_hash=%s WHERE id=%s", (pw_hash, user_id))
                flash('Password changed successfully!', 'success')
                
            return redirect(url_for('profile.edit'))
            
        elif action == 'delete_account':
            # Soft delete by banning or setting inactive flag
            query("UPDATE users SET is_banned=TRUE WHERE id=%s", (user_id,))
            session.clear()
            flash('Your account has been deleted.', 'info')
            return redirect(url_for('index'))

    return render_template('profile/edit.html', user=user)

@profile_bp.route('/creator/<int:creator_id>')
def public_creator(creator_id):
    creator = query("SELECT id, name, email, created_at, bio, avatar, organization_name, website_url, preferences FROM users WHERE id=%s AND role='creator'", (creator_id,), fetchone=True)
    if not creator:
        abort(404)
        
    events = query("SELECT * FROM events WHERE creator_id=%s AND status='published' ORDER BY date_start ASC", (creator_id,))
    
    # Calculate stats
    total_events = query("SELECT COUNT(*) as c FROM events WHERE creator_id=%s AND status IN ('published', 'ended')", (creator_id,), fetchone=True)['c']
    total_regs = query("SELECT COUNT(r.id) as s FROM registrations r JOIN events e ON r.event_id = e.id WHERE e.creator_id=%s AND r.status != 'cancelled'", (creator_id,), fetchone=True)['s'] or 0
    
    # Follow count
    followers_count = query("SELECT COUNT(*) as c FROM creator_follows WHERE creator_id=%s", (creator_id,), fetchone=True)['c']
    
    stats = {
        'total_events': total_events,
        'total_attendees': total_regs,
        'member_since': creator['created_at'].strftime('%B %Y'),
        'followers': followers_count
    }
    
    is_following = False
    if 'user_id' in session:
        is_following = bool(query("SELECT id FROM creator_follows WHERE follower_id=%s AND creator_id=%s", (session['user_id'], creator_id), fetchone=True))
    
    return render_template('profile/public_creator.html', creator=creator, events=events, stats=stats, is_following=is_following)

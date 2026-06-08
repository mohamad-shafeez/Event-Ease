"""
EventEase — Notifications & Follows
"""
from flask import Blueprint, jsonify, session, request
from utils.decorators import login_required
from db import query

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/unread-count')
@login_required
def unread_count():
    user_id = session.get('user_id')
    count = query("SELECT COUNT(*) as c FROM notifications WHERE user_id=%s AND is_read=0", (user_id,), fetchone=True)['c']
    return jsonify({'count': count})

@notifications_bp.route('/')
@login_required
def get_notifications():
    user_id = session.get('user_id')
    notifs = query("SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 10", (user_id,))
    
    # Mark as read
    if notifs:
        query("UPDATE notifications SET is_read=1 WHERE user_id=%s", (user_id,))
        
    # Format dates
    for n in notifs:
        n['date_str'] = n['created_at'].strftime('%b %d, %H:%M')
        
    return jsonify({'notifications': notifs})

@notifications_bp.route('/follow/<int:creator_id>', methods=['POST'])
@login_required
def toggle_follow(creator_id):
    user_id = session.get('user_id')
    
    if user_id == creator_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400
        
    existing = query("SELECT id FROM creator_follows WHERE follower_id=%s AND creator_id=%s", (user_id, creator_id), fetchone=True)
    
    if existing:
        query("DELETE FROM creator_follows WHERE id=%s", (existing['id'],))
        return jsonify({'following': False})
    else:
        query("INSERT INTO creator_follows (follower_id, creator_id) VALUES (%s, %s)", (user_id, creator_id))
        
        # Add a notification to creator
        user_name = session.get('user_name')
        msg = f"{user_name} started following you!"
        query("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (creator_id, msg))
        
        return jsonify({'following': True})

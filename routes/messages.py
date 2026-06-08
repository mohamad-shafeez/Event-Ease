"""
EventEase — Messages Blueprint
"""
from flask import Blueprint, render_template, request, jsonify, session, abort, redirect, url_for, flash
from models.message_model import (
    get_or_create_conversation, send_message, get_conversations, 
    get_messages, get_conversation_by_id, get_unread_count, delete_message
)
from utils.decorators import login_required
from db import query

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

def _check_access(conversation, user_id):
    if not conversation:
        abort(404)
    if conversation['user_id'] != user_id and conversation['creator_id'] != user_id:
        abort(403)

@messages_bp.route('/')
@login_required
def inbox():
    user_id = session.get('user_id')
    role = session.get('role')
    # If admin, messages might not make sense, but allow if they have conversations
    if role not in ['user', 'creator']:
        role = 'user'
        
    conversations = get_conversations(user_id, role)
    return render_template('messages/inbox.html', conversations=conversations, active_conv=None)

@messages_bp.route('/<int:conversation_id>')
@login_required
def open_conversation(conversation_id):
    user_id = session.get('user_id')
    role = session.get('role')
    if role not in ['user', 'creator']:
        role = 'user'
        
    conv = get_conversation_by_id(conversation_id)
    _check_access(conv, user_id)
    
    # Get all conversations for sidebar
    conversations = get_conversations(user_id, role)
    
    # Get messages
    messages = get_messages(conversation_id, user_id)
    
    # Find other person's details
    other_id = conv['creator_id'] if user_id == conv['user_id'] else conv['user_id']
    other_user = query("SELECT id, name, role, avatar FROM users WHERE id=%s", (other_id,), fetchone=True)
    
    # Find event details if any
    event = None
    if conv['event_id']:
        event = query("SELECT id, title FROM events WHERE id=%s", (conv['event_id'],), fetchone=True)
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Check if polling (we just want new messages)
        last_id = request.args.get('last_id', type=int, default=0)
        new_msgs = [m for m in messages if m['id'] > last_id]
        
        # Return partial HTML for the new messages
        html = render_template('messages/_message_list.html', messages=new_msgs, current_user_id=user_id)
        return jsonify({'html': html, 'last_id': messages[-1]['id'] if messages else last_id})
        
    return render_template('messages/conversation.html', 
                           conversations=conversations, 
                           active_conv=conv, 
                           messages=messages,
                           other_user=other_user,
                           event=event)

@messages_bp.route('/send', methods=['POST'])
@login_required
def send():
    user_id = session.get('user_id')
    data = request.get_json()
    conv_id = data.get('conversation_id')
    text = data.get('message', '').strip()
    
    if not conv_id or not text:
        return jsonify({'status': 'error', 'msg': 'Invalid data'}), 400
        
    conv = get_conversation_by_id(conv_id)
    _check_access(conv, user_id)
    
    msg = send_message(conv_id, user_id, text)

    if not msg:
        return jsonify({'status': 'error', 'msg': 'Failed to send message'}), 500

    # Format time
    sent_at = msg['sent_at']
    if isinstance(sent_at, str):
        from datetime import datetime
        sent_at = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
    time_str = sent_at.strftime('%H:%M') if hasattr(sent_at, 'strftime') else str(sent_at)[:5]

    return jsonify({
        'status': 'ok',
        'message_id': msg['id'],
        'time': time_str,
        'text': msg['message_text']
    })

@messages_bp.route('/new/<int:creator_id>')
@login_required
def new_conversation(creator_id):
    user_id = session.get('user_id')
    if user_id == creator_id:
        flash("You can't message yourself.", "warning")
        return redirect(url_for('messages.inbox'))
        
    # Get optional event context
    event_id = request.args.get('event_id', type=int)
    
    conv_id = get_or_create_conversation(user_id, creator_id, event_id)
    return redirect(url_for('messages.open_conversation', conversation_id=conv_id))

@messages_bp.route('/unread-count')
@login_required
def unread_count():
    count = get_unread_count(session.get('user_id'))
    return jsonify({'count': count})

@messages_bp.route('/delete/<int:message_id>', methods=['POST'])
@login_required
def delete(message_id):
    user_id = session.get('user_id')
    delete_message(message_id, user_id)
    return jsonify({'status': 'ok'})

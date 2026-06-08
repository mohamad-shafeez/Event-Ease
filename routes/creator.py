"""
EventEase — Creator Routes
Analytics and Management Dashboard
"""
from flask import Blueprint, render_template, jsonify, session, abort
from utils.decorators import role_required
from models.analytics_model import (
    get_creator_summary, get_creator_revenue_by_event,
    get_creator_registrations_trend, get_creator_events_performance,
    get_creator_top_event
)

creator_bp = Blueprint('creator', __name__, url_prefix='/creator')

@creator_bp.route('/dashboard')
@role_required('creator')
def dashboard():
    creator_id = session['user_id']
    summary = get_creator_summary(creator_id)
    
    # Preload chart data for Jinja injection
    charts = {
        'revenue_by_event': get_creator_revenue_by_event(creator_id),
        'registration_trend': get_creator_registrations_trend(creator_id)
    }
    
    performance = get_creator_events_performance(creator_id)
    top_event = get_creator_top_event(creator_id)
    
    return render_template('creator/dashboard.html', 
                           summary=summary, charts=charts, 
                           performance=performance, top_event=top_event)

@creator_bp.route('/api/chart/<chart_name>')
@role_required('creator')
def api_chart(chart_name):
    creator_id = session['user_id']
    if chart_name == 'revenue_by_event':
        return jsonify(get_creator_revenue_by_event(creator_id))
    elif chart_name == 'registration_trend':
        return jsonify(get_creator_registrations_trend(creator_id))
        
    return jsonify({'error': 'Invalid chart name'}), 400

@creator_bp.route('/checkin/<int:event_id>')
@role_required('creator')
def checkin(event_id):
    from models.event_model import get_event_by_id
    from db import query
    creator_id = session['user_id']
    
    event = get_event_by_id(event_id)
    if not event or event['creator_id'] != creator_id:
        abort(403)
        
    # Get recent check-ins
    recent = query("""
        SELECT r.ticket_code, r.checked_in_at, u.name 
        FROM registrations r
        JOIN users u ON r.user_id = u.id
        WHERE r.event_id = %s AND r.checked_in = 1
        ORDER BY r.checked_in_at DESC
        LIMIT 10
    """, (event_id,))
    
    return render_template('creator/checkin.html', event=event, recent=recent)

@creator_bp.route('/api/checkin', methods=['POST'])
@role_required('creator')
def api_checkin():
    from db import query
    creator_id = session['user_id']
    data = request.get_json()
    ticket_code = data.get('ticket_code')
    event_id = data.get('event_id')
    
    if not ticket_code or not event_id:
        return jsonify({'status': 'error', 'msg': 'Missing data'}), 400
        
    # Verify event belongs to creator
    from models.event_model import get_event_by_id
    event = get_event_by_id(event_id)
    if not event or event['creator_id'] != creator_id:
        return jsonify({'status': 'error', 'msg': 'Unauthorized'}), 403
        
    # Find ticket
    reg = query("""
        SELECT r.id, r.status, r.checked_in, u.name
        FROM registrations r
        JOIN users u ON r.user_id = u.id
        WHERE r.ticket_code = %s AND r.event_id = %s
    """, (ticket_code, event_id), fetchone=True)
    
    if not reg:
        return jsonify({'status': 'error', 'msg': 'Invalid Ticket Code for this event.'}), 404
        
    if reg['status'] != 'confirmed':
        return jsonify({'status': 'error', 'msg': f"Ticket status is {reg['status'].upper()}."}), 400
        
    if reg['checked_in']:
        return jsonify({'status': 'error', 'msg': 'Ticket already checked in.'}), 400
        
    # Mark as checked in
    query("UPDATE registrations SET checked_in = 1, checked_in_at = CURRENT_TIMESTAMP WHERE id = %s", (reg['id'],))
    
    return jsonify({
        'status': 'success',
        'msg': 'Check-in successful!',
        'attendee_name': reg['name'],
        'ticket_code': ticket_code
    })

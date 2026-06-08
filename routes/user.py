"""
EventEase — User Routes
Personal Dashboard and Profile
"""
from flask import Blueprint, render_template, session
from utils.decorators import role_required
from models.analytics_model import (
    get_user_summary, get_user_spending_by_month,
    get_user_event_type_history, get_user_upcoming_events,
    get_recommended_events
)

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@role_required('user')
def dashboard():
    user_id = session['user_id']
    
    summary = get_user_summary(user_id)
    upcoming = get_user_upcoming_events(user_id, limit=3)
    
    charts = {
        'spending': get_user_spending_by_month(user_id),
        'history': get_user_event_type_history(user_id)
    }
    
    top_type = charts['history'].get('top_type')
    recommended = get_recommended_events(user_id, preferred_type=top_type, limit=6)
    
    from db import query
    saved_events = query("""
        SELECT e.id, e.title, e.date_start, e.city, e.type, e.price, e.banner
        FROM saved_events s
        JOIN events e ON s.event_id = e.id
        WHERE s.user_id = %s
        ORDER BY s.saved_at DESC
        LIMIT 4
    """, (user_id,))
    
    return render_template('user/dashboard.html', 
                           summary=summary, upcoming=upcoming, 
                           charts=charts, recommended=recommended,
                           saved_events=saved_events)

@user_bp.route('/profile')
@role_required('user')
def profile():
    from flask import redirect, url_for
    return redirect(url_for('profile.edit'))

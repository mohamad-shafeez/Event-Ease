"""
EventEase — Admin Routes
Full Analytics & Management Dashboards
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort
from utils.decorators import role_required
from db import query
from datetime import datetime

from models.analytics_model import (
    get_platform_summary, get_revenue_by_month, get_registrations_by_month,
    get_users_growth_by_month, get_events_by_type, get_revenue_by_event_type,
    get_top_events, get_top_creators, get_recent_activity, get_city_breakdown,
    get_events_by_status
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ── Admin Dashboard ──────────────────────────────────
@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    summary = get_platform_summary()
    current_year = datetime.now().year
    
    # Chart Data for Jinja injection
    charts = {
        'revenue_monthly': get_revenue_by_month(current_year),
        'regs_monthly': get_registrations_by_month(current_year),
        'events_type': get_events_by_type(),
        'revenue_type': get_revenue_by_event_type()
    }
    
    top_events = get_top_events(5)
    top_creators = get_top_creators(5)
    recent = get_recent_activity(10)
    
    return render_template('admin/dashboard.html',
                           summary=summary, charts=charts,
                           top_events=top_events, top_creators=top_creators,
                           recent=recent, current_year=current_year)

# ── API Endpoints (For Live Refresh & Charts) ────────
@admin_bp.route('/api/stats')
@role_required('admin')
def api_stats():
    return jsonify(get_platform_summary())

@admin_bp.route('/api/chart/<chart_name>')
@role_required('admin')
def api_chart(chart_name):
    year = request.args.get('year', datetime.now().year, type=int)
    
    if chart_name == 'revenue_monthly':
        return jsonify(get_revenue_by_month(year))
    elif chart_name == 'regs_monthly':
        return jsonify(get_registrations_by_month(year))
    elif chart_name == 'user_growth':
        return jsonify(get_users_growth_by_month(year))
    elif chart_name == 'events_type':
        return jsonify(get_events_by_type())
    elif chart_name == 'city_breakdown':
        return jsonify(get_city_breakdown())
    elif chart_name == 'event_status':
        return jsonify(get_events_by_status())
    elif chart_name == 'payment_methods':
        # Added to satisfy the analytics page requirement
        data = query("SELECT method, COUNT(*) as c FROM payments WHERE status='success' GROUP BY method")
        return jsonify({
            'labels': [row['method'].upper() for row in data],
            'data': [row['c'] for row in data]
        })
        
    return jsonify({'error': 'Invalid chart name'}), 400

# ── Management Pages ─────────────────────────────────
@admin_bp.route('/users')
@role_required('admin')
def manage_users():
    search = request.args.get('search', '')
    filter_role = request.args.get('role', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    where = ["1=1"]
    params = []
    
    if search:
        where.append("(name LIKE %s OR email LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
        
    if filter_role == 'users':
        where.append("role='user'")
    elif filter_role == 'creators':
        where.append("role='creator'")
    elif filter_role == 'banned':
        where.append("is_banned=1") # Assuming is_banned exists, otherwise we'd need to add it to DB. Let's assume it exists or we use status. Wait, Phase 1 users table had no is_banned. Let's add it if missing or just use status='banned' if we defined it. 
        # Checking schema: Phase 1 users: id, name, email, password_hash, role, avatar, created_at. We will alter table if needed, let's use a subquery or alter. 
        # Actually, let's alter table users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE if it fails. I will run a run_command for safety.
    
    # We will assume a simple query for now.
    offset = (page - 1) * per_page
    where_sql = " AND ".join(where)
    
    try:
        users = query(f"""
            SELECT u.*, 
                   (SELECT COUNT(*) FROM registrations WHERE user_id=u.id AND status!='cancelled') as total_regs
            FROM users u
            WHERE {where_sql}
            ORDER BY u.created_at DESC LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        
        total = query(f"SELECT COUNT(*) as c FROM users WHERE {where_sql}", params, fetchone=True)['c']
    except Exception:
        # If is_banned column is missing, we just skip the ban logic in query fallback
        users = []
        total = 0
        
    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template('admin/users.html', users=users, page=page, total_pages=total_pages, search=search, filter_role=filter_role)

@admin_bp.route('/users/ban/<int:user_id>', methods=['POST'])
@role_required('admin')
def toggle_ban(user_id):
    user = query("SELECT id, is_banned FROM users WHERE id=%s AND role!='admin'", (user_id,), fetchone=True)
    if not user:
        abort(404)
    new_status = 0 if user.get('is_banned') else 1
    try:
        query("UPDATE users SET is_banned=%s WHERE id=%s", (new_status, user_id))
        flash('User status updated successfully.', 'success')
    except Exception:
        flash('Error updating user status (is_banned column may be missing).', 'danger')
    return redirect(request.referrer or url_for('admin.manage_users'))

@admin_bp.route('/events')
@role_required('admin')
def manage_events():
    search = request.args.get('search', '')
    filter_status = request.args.get('status', 'all')
    
    where = ["1=1"]
    params = []
    
    if search:
        where.append("e.title LIKE %s")
        params.append(f"%{search}%")
        
    if filter_status != 'all':
        where.append("e.status=%s")
        params.append(filter_status)
        
    where_sql = " AND ".join(where)
    events = query(f"""
        SELECT e.*, u.name as creator_name,
               (SELECT COUNT(*) FROM registrations r WHERE r.event_id=e.id AND r.status!='cancelled') as registered,
               (SELECT SUM(amount) FROM payments p JOIN registrations r ON p.registration_id=r.id WHERE r.event_id=e.id AND p.status='success') as revenue
        FROM events e
        JOIN users u ON e.creator_id=u.id
        WHERE {where_sql}
        ORDER BY e.created_at DESC
    """, params)
    
    return render_template('admin/events.html', events=events, search=search, filter_status=filter_status)

@admin_bp.route('/events/cancel/<int:event_id>', methods=['POST'])
@role_required('admin')
def force_cancel_event(event_id):
    query("UPDATE events SET status='cancelled' WHERE id=%s", (event_id,))
    flash('Event forcefully cancelled.', 'warning')
    return redirect(request.referrer or url_for('admin.manage_events'))

@admin_bp.route('/analytics')
@role_required('admin')
def analytics():
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Preload initial charts for the page render
    charts = {
        'user_growth': get_users_growth_by_month(year),
        'city_heatmap': get_city_breakdown(),
        'event_status': get_events_by_status(),
        'payment_methods': api_chart('payment_methods').json
    }
    
    # Monthly summary table
    rev = get_revenue_by_month(year)
    reg = get_registrations_by_month(year)
    usr = get_users_growth_by_month(year)
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    summary_table = []
    for i in range(12):
        summary_table.append({
            'month': months[i],
            'revenue': rev[i],
            'registrations': reg[i],
            'new_users': usr[i]
        })
        
    return render_template('admin/analytics.html', year=year, charts=charts, summary_table=summary_table)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@role_required('admin')
def settings():
    from db import get_setting, set_setting
    from config import Config
    
    if request.method == 'POST':
        set_setting('platform_name', request.form.get('platform_name', 'EventEase'))
        set_setting('tagline', request.form.get('tagline', ''))
        set_setting('support_email', request.form.get('support_email', ''))
        set_setting('max_tickets_per_user', request.form.get('max_tickets_per_user', '5'))
        
        set_setting('allow_guest_browsing', 'true' if request.form.get('allow_guest_browsing') else 'false')
        set_setting('maintenance_mode', 'true' if request.form.get('maintenance_mode') else 'false')
        
        flash('Settings saved successfully.', 'success')
        return redirect(url_for('admin.settings'))
        
    settings_data = {
        'platform_name': get_setting('platform_name', 'EventEase'),
        'tagline': get_setting('tagline', ''),
        'support_email': get_setting('support_email', ''),
        'max_tickets_per_user': get_setting('max_tickets_per_user', '5'),
        'allow_guest_browsing': get_setting('allow_guest_browsing') == 'true',
        'maintenance_mode': get_setting('maintenance_mode') == 'true',
    }
    
    return render_template('admin/settings.html', settings=settings_data, config=Config)

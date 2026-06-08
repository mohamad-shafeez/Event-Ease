"""
EventEase — Analytics Model
All stat queries for Admin, Creator, and User dashboards.
"""
from db import query
from datetime import datetime, timedelta

# ── Admin Stats ──────────────────────────────────

def get_platform_summary():
    """Returns top-level KPIs for the platform."""
    total_users = query("SELECT COUNT(*) as c FROM users WHERE role='user'", fetchone=True)['c']
    total_creators = query("SELECT COUNT(*) as c FROM users WHERE role='creator'", fetchone=True)['c']
    total_events = query("SELECT COUNT(*) as c FROM events WHERE status='published'", fetchone=True)['c']
    total_registrations = query("SELECT COUNT(*) as c FROM registrations WHERE status!='cancelled'", fetchone=True)['c']
    total_revenue = query("SELECT SUM(amount) as s FROM payments WHERE status='success'", fetchone=True)['s'] or 0
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    events_today = query("SELECT COUNT(*) as c FROM events WHERE DATE(date_start)=%s AND status='published'", (today_str,), fetchone=True)['c']
    
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    new_users_week = query("SELECT COUNT(*) as c FROM users WHERE role='user' AND created_at >= %s", (week_ago,), fetchone=True)['c']
    
    return {
        'total_users': total_users,
        'total_creators': total_creators,
        'total_events': total_events,
        'total_registrations': total_registrations,
        'total_revenue': float(total_revenue),
        'events_today': events_today,
        'new_users_this_week': new_users_week
    }

def get_revenue_by_month(year):
    """Returns 12 data points for revenue by month for a given year."""
    data = query("""
        SELECT MONTH(created_at) as month, SUM(amount) as total
        FROM payments
        WHERE status='success' AND YEAR(created_at) = %s
        GROUP BY MONTH(created_at)
        ORDER BY month
    """, (year,))
    
    # Fill missing months with 0
    result = [0] * 12
    for row in data:
        if row['month']:
            result[row['month'] - 1] = float(row['total'] or 0)
    return result

def get_registrations_by_month(year):
    """Returns 12 data points for registrations by month for a given year."""
    data = query("""
        SELECT MONTH(created_at) as month, COUNT(*) as total
        FROM registrations
        WHERE status!='cancelled' AND YEAR(created_at) = %s
        GROUP BY MONTH(created_at)
        ORDER BY month
    """, (year,))
    
    result = [0] * 12
    for row in data:
        if row['month']:
            result[row['month'] - 1] = row['total']
    return result

def get_users_growth_by_month(year):
    """Returns 12 data points for user signups by month for a given year."""
    data = query("""
        SELECT MONTH(created_at) as month, COUNT(*) as total
        FROM users
        WHERE role='user' AND YEAR(created_at) = %s
        GROUP BY MONTH(created_at)
        ORDER BY month
    """, (year,))
    
    result = [0] * 12
    for row in data:
        if row['month']:
            result[row['month'] - 1] = row['total']
    return result

def get_events_by_type():
    """Returns count of events per type."""
    from models.event_model import EVENT_TYPES
    type_labels = [t[1] for t in EVENT_TYPES]
    type_keys = [t[0] for t in EVENT_TYPES]
    
    counts = query("SELECT type, COUNT(*) as c FROM events GROUP BY type")
    count_dict = {row['type']: row['c'] for row in counts}
    
    return {
        'labels': type_labels,
        'data': [count_dict.get(k, 0) for k in type_keys]
    }

def get_events_by_status():
    """Returns count of events per status."""
    counts = query("SELECT status, COUNT(*) as c FROM events GROUP BY status")
    count_dict = {row['status']: row['c'] for row in counts}
    statuses = ['published', 'draft', 'cancelled', 'ended']
    return {
        'labels': [s.capitalize() for s in statuses],
        'data': [count_dict.get(s, 0) for s in statuses]
    }

def get_revenue_by_event_type():
    """Returns revenue grouped by event type."""
    data = query("""
        SELECT e.type, SUM(p.amount) as total
        FROM payments p
        JOIN registrations r ON p.registration_id = r.id
        JOIN events e ON r.event_id = e.id
        WHERE p.status='success'
        GROUP BY e.type
        ORDER BY total DESC
    """)
    return {
        'labels': [row['type'].replace('_', ' ').title() for row in data],
        'data': [float(row['total']) for row in data]
    }

def get_top_events(limit=5):
    return query("""
        SELECT e.id, e.title, COUNT(r.id) as registrations, SUM(p.amount) as revenue, e.capacity
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id AND r.status!='cancelled'
        LEFT JOIN payments p ON r.id = p.registration_id AND p.status='success'
        WHERE e.status='published'
        GROUP BY e.id
        ORDER BY registrations DESC
        LIMIT %s
    """, (limit,))

def get_top_creators(limit=5):
    return query("""
        SELECT u.name, COUNT(DISTINCT e.id) as events, COUNT(r.id) as attendees, SUM(p.amount) as revenue
        FROM users u
        JOIN events e ON u.id = e.creator_id
        LEFT JOIN registrations r ON e.id = r.event_id AND r.status!='cancelled'
        LEFT JOIN payments p ON r.id = p.registration_id AND p.status='success'
        WHERE u.role='creator'
        GROUP BY u.id
        ORDER BY revenue DESC
        LIMIT %s
    """, (limit,))

def get_recent_activity(limit=10):
    return query("""
        SELECT r.created_at, u.name as user_name, e.title as event_title
        FROM registrations r
        JOIN users u ON r.user_id = u.id
        JOIN events e ON r.event_id = e.id
        ORDER BY r.created_at DESC
        LIMIT %s
    """, (limit,))

def get_city_breakdown():
    data = query("SELECT city, COUNT(*) as c FROM events WHERE city IS NOT NULL AND city != '' GROUP BY city ORDER BY c DESC LIMIT 10")
    return {
        'labels': [row['city'] for row in data],
        'data': [row['c'] for row in data]
    }


# ── Creator Stats ────────────────────────────────

def get_creator_summary(creator_id):
    events = query("SELECT COUNT(*) as c, SUM(capacity) as cap FROM events WHERE creator_id=%s AND status!='cancelled'", (creator_id,), fetchone=True)
    attendees = query("""
        SELECT COUNT(*) as c FROM registrations r 
        JOIN events e ON r.event_id = e.id 
        WHERE e.creator_id=%s AND r.status!='cancelled'
    """, (creator_id,), fetchone=True)['c']
    revenue = query("""
        SELECT SUM(p.amount) as s FROM payments p 
        JOIN registrations r ON p.registration_id = r.id 
        JOIN events e ON r.event_id = e.id 
        WHERE e.creator_id=%s AND p.status='success'
    """, (creator_id,), fetchone=True)['s'] or 0
    
    total_cap = events['cap'] or 0
    avg_fill = (attendees / total_cap * 100) if total_cap > 0 else 0
    
    return {
        'total_events': events['c'],
        'total_attendees': attendees,
        'total_revenue': float(revenue),
        'avg_fill_rate': avg_fill
    }

def get_creator_revenue_by_event(creator_id, limit=8):
    data = query("""
        SELECT e.title, SUM(p.amount) as total
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id AND r.status!='cancelled'
        LEFT JOIN payments p ON r.id = p.registration_id AND p.status='success'
        WHERE e.creator_id=%s AND e.status!='cancelled'
        GROUP BY e.id
        ORDER BY total DESC
        LIMIT %s
    """, (creator_id, limit))
    return {
        'labels': [row['title'][:15] + '...' if len(row['title'])>15 else row['title'] for row in data],
        'data': [float(row['total'] or 0) for row in data]
    }

def get_creator_registrations_trend(creator_id, days=30):
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    data = query("""
        SELECT DATE(r.created_at) as date, COUNT(*) as c
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE e.creator_id=%s AND r.status!='cancelled' AND r.created_at >= %s
        GROUP BY DATE(r.created_at)
        ORDER BY date
    """, (creator_id, start_date))
    
    # Generate full date range
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
    count_map = {str(row['date']): row['c'] for row in data}
    
    return {
        'labels': [d[-5:] for d in dates], # MM-DD
        'data': [count_map.get(d, 0) for d in dates]
    }

def get_creator_events_performance(creator_id):
    return query("""
        SELECT e.id, e.title, e.capacity, e.status, e.type,
               COUNT(r.id) as registered, SUM(p.amount) as revenue
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id AND r.status!='cancelled'
        LEFT JOIN payments p ON r.id = p.registration_id AND p.status='success'
        WHERE e.creator_id=%s AND e.status!='cancelled'
        GROUP BY e.id
        ORDER BY registered DESC
    """, (creator_id,))

def get_creator_top_event(creator_id):
    return query("""
        SELECT e.*, COUNT(r.id) as registered, SUM(p.amount) as revenue
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id AND r.status!='cancelled'
        LEFT JOIN payments p ON r.id = p.registration_id AND p.status='success'
        WHERE e.creator_id=%s AND e.status!='cancelled'
        GROUP BY e.id
        ORDER BY registered DESC
        LIMIT 1
    """, (creator_id,), fetchone=True)


# ── User Stats ───────────────────────────────────

def get_user_summary(user_id):
    now = datetime.now()
    tickets = query("SELECT e.date_start FROM registrations r JOIN events e ON r.event_id = e.id WHERE r.user_id=%s AND r.status!='cancelled'", (user_id,))
    
    total = len(tickets)
    upcoming = sum(1 for t in tickets if t['date_start'] and t['date_start'] > now)
    past = total - upcoming
    
    spent = query("""
        SELECT SUM(p.amount) as s FROM payments p
        JOIN registrations r ON p.registration_id = r.id
        WHERE r.user_id=%s AND p.status='success'
    """, (user_id,), fetchone=True)['s'] or 0
    
    return {
        'tickets_total': total,
        'upcoming_events': upcoming,
        'past_events': past,
        'total_spent': float(spent)
    }

def get_user_spending_by_month(user_id):
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-01')
    data = query("""
        SELECT DATE_FORMAT(p.created_at, '%Y-%m') as month, SUM(p.amount) as total
        FROM payments p
        JOIN registrations r ON p.registration_id = r.id
        WHERE r.user_id=%s AND p.status='success' AND p.created_at >= %s
        GROUP BY month
        ORDER BY month
    """, (user_id, six_months_ago))
    
    months = [(datetime.now() - timedelta(days=30*i)).strftime('%Y-%m') for i in range(5, -1, -1)]
    spend_map = {row['month']: float(row['total']) for row in data}
    
    return {
        'labels': [datetime.strptime(m, '%Y-%m').strftime('%b') for m in months],
        'data': [spend_map.get(m, 0) for m in months]
    }

def get_user_event_type_history(user_id):
    data = query("""
        SELECT e.type, COUNT(*) as c
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.user_id=%s AND r.status!='cancelled'
        GROUP BY e.type
        ORDER BY c DESC
    """, (user_id,))
    
    if not data:
        return {'labels': ['No Events'], 'data': [1]}
        
    return {
        'labels': [row['type'].replace('_', ' ').title() for row in data],
        'data': [row['c'] for row in data],
        'top_type': data[0]['type'] if data else None
    }

def get_user_upcoming_events(user_id, limit=3):
    return query("""
        SELECT e.id, e.title, e.type, e.date_start, e.city, e.venue, r.ticket_code
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.user_id=%s AND r.status!='cancelled' AND e.date_start > NOW()
        ORDER BY e.date_start ASC
        LIMIT %s
    """, (user_id, limit))

def get_recommended_events(user_id, preferred_type=None, limit=6):
    where_clause = "e.status='published' AND e.date_start > NOW() AND e.id NOT IN (SELECT event_id FROM registrations WHERE user_id=%s AND status!='cancelled')"
    params = [user_id]
    
    if preferred_type:
        where_clause += " AND e.type=%s"
        params.append(preferred_type)
        
    events = query(f"""
        SELECT e.id, e.title, e.type, e.banner, e.date_start, e.city, e.price
        FROM events e
        WHERE {where_clause}
        ORDER BY e.created_at DESC
        LIMIT %s
    """, params + [limit])
    
    # Fallback if no preferred types found
    if not events and preferred_type:
        events = query(f"""
            SELECT e.id, e.title, e.type, e.banner, e.date_start, e.city, e.price
            FROM events e
            WHERE e.status='published' AND e.date_start > NOW() AND e.id NOT IN (SELECT event_id FROM registrations WHERE user_id=%s AND status!='cancelled')
            ORDER BY RAND()
            LIMIT %s
        """, [user_id, limit])
        
    return events

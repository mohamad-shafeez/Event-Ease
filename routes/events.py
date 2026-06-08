"""
EventEase — Event Routes
Public browsing + Creator CRUD
"""
import os, time
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app, abort, jsonify)
from werkzeug.utils import secure_filename
from utils.decorators import login_required, role_required
from models.event_model import (
    create_event, get_event_by_id, get_all_events,
    get_events_by_creator, update_event, set_event_status,
    get_similar_events, increment_view, EVENT_TYPES, EVENT_TYPE_MAP
)
from db import query

events_bp = Blueprint('events', __name__, url_prefix='/events')
ALLOWED_EXT = {'jpg', 'jpeg', 'png', 'webp'}


def _allowed(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def _save_banner(file, event_id):
    if not file or not file.filename or not _allowed(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    fname = f"event_{event_id}_{int(time.time())}.{ext}"
    folder = os.path.join(current_app.static_folder, 'uploads', 'banners')
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, fname))
    return f"uploads/banners/{fname}"


def _extract_details(form):
    return {k[7:]: v.strip() for k, v in form.items()
            if k.startswith('detail_') and v.strip()}


# ── Public: Browse Events ────────────────────────
@events_bp.route('/')
def browse():
    page = request.args.get('page', 1, type=int)
    filters = {
        'type': request.args.getlist('type') or request.args.get('type'),
        'city': request.args.get('city'),
        'search': request.args.get('search'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to'),
        'price': request.args.get('price'),
        'sort': request.args.get('sort', 'newest'),
    }
    # Clean empty filters
    filters = {k: v for k, v in filters.items() if v}
    events, total = get_all_events(filters, page, 12)
    
    # Get user's saved events
    saved_ids = []
    if 'user_id' in session:
        saved = query("SELECT event_id FROM saved_events WHERE user_id=%s", (session['user_id'],))
        saved_ids = [s['event_id'] for s in saved]
        
    total_pages = max(1, (total + 11) // 12)
    return render_template('events/browse.html',
                           events=events, page=page, total_pages=total_pages,
                           total=total, filters=filters, event_types=EVENT_TYPES,
                           saved_ids=saved_ids)


# ── Public: Event Detail ─────────────────────────
@events_bp.route('/<int:event_id>')
def detail(event_id):
    event = get_event_by_id(event_id)
    if not event:
        abort(404)
    increment_view(event_id)
    similar = get_similar_events(event['type'], event_id)
    type_info = EVENT_TYPE_MAP.get(event['type'], (event['type'], ''))
    
    # Saved status
    is_saved = False
    if 'user_id' in session:
        is_saved = bool(query("SELECT id FROM saved_events WHERE user_id=%s AND event_id=%s", (session['user_id'], event_id), fetchone=True))
        
    # Reviews
    reviews = query("""
        SELECT r.*, u.name, u.avatar 
        FROM reviews r 
        JOIN users u ON r.user_id = u.id 
        WHERE r.event_id = %s 
        ORDER BY r.created_at DESC
    """, (event_id,))
    
    avg_rating = 0
    if reviews:
        avg_rating = round(sum(r['rating'] for r in reviews) / len(reviews), 1)
        
    from datetime import datetime
    return render_template('events/detail.html', event=event,
                           similar=similar, type_label=type_info[0], type_emoji=type_info[1],
                           is_saved=is_saved, reviews=reviews, avg_rating=avg_rating, now=datetime.now())


# ── Creator: Create Event ────────────────────────
@events_bp.route('/create', methods=['GET', 'POST'])
@role_required('creator')
def create():
    if request.method == 'POST':
        data = {
            'creator_id': session['user_id'],
            'title': request.form.get('title', '').strip(),
            'type': request.form.get('type', ''),
            'description': request.form.get('description', '').strip(),
            'date_start': request.form.get('date_start'),
            'date_end': request.form.get('date_end') or None,
            'venue': request.form.get('venue', '').strip(),
            'city': request.form.get('city', '').strip(),
            'capacity': request.form.get('capacity', 0, type=int),
            'price': request.form.get('price', 0, type=float),
            'status': request.form.get('status', 'draft'),
            'details': _extract_details(request.form),
        }
        if not all([data['title'], data['type'], data['date_start']]):
            flash('Title, type, and start date are required.', 'danger')
            return redirect(url_for('events.create'))

        event_id = create_event(data)

        # Handle banner upload
        banner = request.files.get('banner')
        if banner and banner.filename:
            path = _save_banner(banner, event_id)
            if path:
                query("UPDATE events SET banner=%s WHERE id=%s", (path, event_id))

        if data['status'] == 'published':
            from utils.email_sender import send_event_created
            # date format handling just in case
            date_str = data['date_start'].replace('T', ' ') if 'T' in data['date_start'] else data['date_start']
            send_event_created(session['user_email'], session['user_name'], data['title'], date_str)

        flash('Event created successfully!', 'success')
        return redirect(url_for('events.manage'))

    return render_template('events/create.html', event_types=EVENT_TYPES)


# ── Creator: Manage My Events ────────────────────
@events_bp.route('/manage')
@role_required('creator')
def manage():
    events = get_events_by_creator(session['user_id'])
    return render_template('events/manage.html', events=events, event_types=EVENT_TYPES)


# ── Creator: Edit Event ──────────────────────────
@events_bp.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@role_required('creator')
def edit(event_id):
    event = get_event_by_id(event_id)
    if not event:
        abort(404)
    if event['creator_id'] != session['user_id']:
        abort(403)

    if request.method == 'POST':
        data = {
            'title': request.form.get('title', '').strip(),
            'type': request.form.get('type', ''),
            'description': request.form.get('description', '').strip(),
            'date_start': request.form.get('date_start'),
            'date_end': request.form.get('date_end') or None,
            'venue': request.form.get('venue', '').strip(),
            'city': request.form.get('city', '').strip(),
            'capacity': request.form.get('capacity', 0, type=int),
            'price': request.form.get('price', 0, type=float),
            'details': _extract_details(request.form),
        }
        banner = request.files.get('banner')
        if banner and banner.filename:
            data['banner'] = _save_banner(banner, event_id)
        else:
            data['banner'] = None  # keep existing

        update_event(event_id, data)
        flash('Event updated!', 'success')
        return redirect(url_for('events.manage'))

    return render_template('events/edit.html', event=event, event_types=EVENT_TYPES)


# ── Creator: Publish Event ───────────────────────
@events_bp.route('/publish/<int:event_id>', methods=['POST'])
@role_required('creator')
def publish(event_id):
    event = get_event_by_id(event_id)
    if not event:
        abort(404)
    if event['creator_id'] != session['user_id']:
        abort(403)
    set_event_status(event_id, 'published')
    
    from utils.email_sender import send_event_created
    send_event_created(session['user_email'], session['user_name'], event['title'], event['date_start'].strftime('%b %d, %Y') if event['date_start'] else 'TBD')
    
    # Notify followers
    followers = query("SELECT follower_id FROM creator_follows WHERE creator_id=%s", (session['user_id'],))
    if followers:
        link = url_for('events.detail', event_id=event_id)
        msg = f"{session['user_name']} has published a new event: {event['title']}"
        for f in followers:
            query("INSERT INTO notifications (user_id, message, link) VALUES (%s, %s, %s)", (f['follower_id'], msg, link))
            
    flash('Event published!', 'success')
    return redirect(url_for('events.manage'))


# ── Creator: Cancel Event ────────────────────────
@events_bp.route('/delete/<int:event_id>', methods=['POST'])
@role_required('creator')
def delete(event_id):
    event = get_event_by_id(event_id)
    if not event:
        abort(404)
    if event['creator_id'] != session['user_id']:
        abort(403)
    set_event_status(event_id, 'cancelled')
    flash('Event cancelled.', 'info')
    return redirect(url_for('events.manage'))


# ── Feature: Save/Bookmark Event ─────────────────
@events_bp.route('/save/<int:event_id>', methods=['POST'])
@login_required
def toggle_save(event_id):
    user_id = session.get('user_id')
    existing = query("SELECT id FROM saved_events WHERE user_id=%s AND event_id=%s", (user_id, event_id), fetchone=True)
    
    if existing:
        query("DELETE FROM saved_events WHERE id=%s", (existing['id'],))
        return jsonify({'saved': False})
    else:
        query("INSERT INTO saved_events (user_id, event_id) VALUES (%s, %s)", (user_id, event_id))
        return jsonify({'saved': True})


# ── Feature: Review Event ────────────────────────
@events_bp.route('/review/<int:event_id>', methods=['POST'])
@role_required('user')
def review_event(event_id):
    rating = request.form.get('rating', type=int)
    review_text = request.form.get('review_text', '').strip()
    
    if not rating or rating < 1 or rating > 5:
        flash("Invalid rating.", "danger")
        return redirect(url_for('tickets.my_tickets'))
        
    query(
        "INSERT INTO reviews (event_id, user_id, rating, review_text) VALUES (%s, %s, %s, %s)",
        (event_id, session['user_id'], rating, review_text)
    )
    flash("Thank you for reviewing!", "success")
    return redirect(url_for('events.detail', event_id=event_id))

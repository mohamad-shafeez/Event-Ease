"""
EventEase — Event Model (Data Access Layer)
"""
from db import query

EVENT_TYPES = [
    ('concert', 'Concert / Music Show', '🎵'),
    ('tech_conference', 'Tech Conference', '💻'),
    ('workshop', 'Workshop / Bootcamp', '🛠️'),
    ('sports', 'Sports Tournament', '⚽'),
    ('wedding', 'Wedding / Private Event', '💒'),
    ('exhibition', 'Exhibition / Expo', '🖼️'),
    ('webinar', 'Online Webinar', '🌐'),
    ('food_festival', 'Food Festival', '🍔'),
    ('charity', 'Charity / NGO Event', '💝'),
    ('comedy', 'Comedy / Theatre Show', '🎭'),
]

EVENT_TYPE_MAP = {k: (l, e) for k, l, e in EVENT_TYPES}


def create_event(data):
    event_id = query(
        """INSERT INTO events
           (creator_id, title, type, description, date_start, date_end,
            venue, city, capacity, price, banner, status)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (data['creator_id'], data['title'], data['type'], data.get('description', ''),
         data['date_start'], data.get('date_end'), data.get('venue', ''),
         data.get('city', ''), data.get('capacity', 0), data.get('price', 0),
         data.get('banner'), data.get('status', 'draft'))
    )
    if 'details' in data:
        for key, val in data['details'].items():
            if val and str(val).strip():
                query("INSERT INTO event_details (event_id, field_key, field_value) VALUES (%s,%s,%s)",
                      (event_id, key, str(val).strip()))
    return event_id


def get_event_by_id(event_id):
    event = query(
        """SELECT e.*, u.name as creator_name, u.avatar as creator_avatar,
           (SELECT COUNT(*) FROM registrations r WHERE r.event_id=e.id AND r.status!='cancelled') as registered
           FROM events e JOIN users u ON e.creator_id=u.id WHERE e.id=%s""",
        (event_id,), fetchone=True
    )
    if event:
        details = query("SELECT field_key, field_value FROM event_details WHERE event_id=%s", (event_id,))
        event['details'] = {d['field_key']: d['field_value'] for d in details}
    return event


def get_all_events(filters=None, page=1, per_page=12):
    where = ["e.status='published'"]
    params = []
    if filters:
        if filters.get('type'):
            types = filters['type'] if isinstance(filters['type'], list) else [filters['type']]
            where.append(f"e.type IN ({','.join(['%s']*len(types))})")
            params.extend(types)
        if filters.get('city'):
            where.append("e.city LIKE %s")
            params.append(f"%{filters['city']}%")
        if filters.get('search'):
            where.append("(e.title LIKE %s OR e.city LIKE %s OR e.description LIKE %s)")
            s = f"%{filters['search']}%"
            params.extend([s, s, s])
        if filters.get('date_from'):
            where.append("e.date_start >= %s")
            params.append(filters['date_from'])
        if filters.get('date_to'):
            where.append("e.date_start <= %s")
            params.append(filters['date_to'])
        if filters.get('price') == 'free':
            where.append("e.price = 0")
        elif filters.get('price') == 'paid':
            where.append("e.price > 0")

    where_sql = " AND ".join(where)
    sort_map = {'newest': 'e.created_at DESC', 'soonest': 'e.date_start ASC',
                'price_low': 'e.price ASC', 'price_high': 'e.price DESC'}
    order = sort_map.get(filters.get('sort', 'newest') if filters else 'newest', 'e.created_at DESC')

    total_row = query(f"SELECT COUNT(*) as total FROM events e WHERE {where_sql}", params, fetchone=True)
    total = total_row['total'] if total_row else 0

    offset = (page - 1) * per_page
    events = query(
        f"""SELECT e.*, u.name as creator_name,
            (SELECT COUNT(*) FROM registrations r WHERE r.event_id=e.id AND r.status!='cancelled') as registered
            FROM events e JOIN users u ON e.creator_id=u.id
            WHERE {where_sql} ORDER BY {order} LIMIT %s OFFSET %s""",
        params + [per_page, offset]
    )
    return events, total


def get_events_by_creator(creator_id):
    return query(
        """SELECT e.*,
           (SELECT COUNT(*) FROM registrations r WHERE r.event_id=e.id AND r.status!='cancelled') as registered
           FROM events e WHERE e.creator_id=%s ORDER BY e.created_at DESC""",
        (creator_id,)
    )


def update_event(event_id, data):
    query(
        """UPDATE events SET title=%s, type=%s, description=%s, date_start=%s, date_end=%s,
           venue=%s, city=%s, capacity=%s, price=%s, banner=COALESCE(%s, banner)
           WHERE id=%s""",
        (data['title'], data['type'], data.get('description', ''),
         data['date_start'], data.get('date_end'), data.get('venue', ''),
         data.get('city', ''), data.get('capacity', 0), data.get('price', 0),
         data.get('banner'), event_id)
    )
    query("DELETE FROM event_details WHERE event_id=%s", (event_id,))
    if 'details' in data:
        for key, val in data['details'].items():
            if val and str(val).strip():
                query("INSERT INTO event_details (event_id, field_key, field_value) VALUES (%s,%s,%s)",
                      (event_id, key, str(val).strip()))


def set_event_status(event_id, status):
    query("UPDATE events SET status=%s WHERE id=%s", (status, event_id))


def get_similar_events(event_type, exclude_id, limit=3):
    return query(
        """SELECT e.*, u.name as creator_name FROM events e
           JOIN users u ON e.creator_id=u.id
           WHERE e.type=%s AND e.id!=%s AND e.status='published'
           ORDER BY e.date_start ASC LIMIT %s""",
        (event_type, exclude_id, limit)
    )


def increment_view(event_id):
    from datetime import date
    today = date.today().isoformat()
    existing = query("SELECT id FROM analytics WHERE event_id=%s AND date=%s", (event_id, today), fetchone=True)
    if existing:
        query("UPDATE analytics SET views=views+1 WHERE id=%s", (existing['id'],))
    else:
        query("INSERT INTO analytics (event_id, views, date) VALUES (%s, 1, %s)", (event_id, today))

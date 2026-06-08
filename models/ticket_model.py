"""
EventEase — Ticket & Registration Model
"""
import uuid
import random
import string
from db import query

def generate_ticket_code(event_id):
    """Generate EE-{EVENTID}-{6CHAR_RANDOM}"""
    rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"EE-{event_id}-{rand_str}"

def create_registration(user_id, event_id):
    ticket_code = generate_ticket_code(event_id)
    reg_id = query(
        "INSERT INTO registrations (user_id, event_id, ticket_code, status) VALUES (%s, %s, %s, 'pending')",
        (user_id, event_id, ticket_code)
    )
    return reg_id, ticket_code

def save_answers(registration_id, answers_dict):
    if not answers_dict:
        return
    data_list = [(registration_id, k, str(v)) for k, v in answers_dict.items() if v]
    if data_list:
        from db import execute_many
        execute_many(
            "INSERT INTO registration_answers (registration_id, question_key, answer) VALUES (%s, %s, %s)",
            data_list
        )

def create_payment(registration_id, amount, method, txn_id):
    return query(
        "INSERT INTO payments (registration_id, amount, method, txn_id, status) VALUES (%s, %s, %s, %s, 'success')",
        (registration_id, amount, method, txn_id)
    )

def confirm_registration(registration_id, qr_path):
    query(
        "UPDATE registrations SET status='confirmed', paid_at=CURRENT_TIMESTAMP, qr_path=%s WHERE id=%s",
        (qr_path, registration_id)
    )

def get_tickets_by_user(user_id):
    return query(
        """SELECT r.*, e.title as event_title, e.type as event_type, e.date_start, e.banner, e.city, e.venue
           FROM registrations r
           JOIN events e ON r.event_id = e.id
           WHERE r.user_id = %s
           ORDER BY e.date_start DESC""",
        (user_id,)
    )

def get_ticket_detail(ticket_code):
    reg = query(
        """SELECT r.*, e.title as event_title, e.date_start, e.date_end, e.venue, e.city, e.type as event_type, 
                  u.name as user_name, u.email as user_email
           FROM registrations r
           JOIN events e ON r.event_id = e.id
           JOIN users u ON r.user_id = u.id
           WHERE r.ticket_code = %s""",
        (ticket_code,), fetchone=True
    )
    if reg:
        answers = query("SELECT question_key, answer FROM registration_answers WHERE registration_id=%s", (reg['id'],))
        reg['answers'] = {a['question_key']: a['answer'] for a in answers}
        pay = query("SELECT amount FROM payments WHERE registration_id=%s AND status='success'", (reg['id'],), fetchone=True)
        reg['paid_amount'] = pay['amount'] if pay else 0
    return reg

def get_attendees_by_event(event_id):
    regs = query(
        """SELECT r.id, r.ticket_code, r.status, r.created_at, u.name, u.email, u.id as user_id,
           (SELECT amount FROM payments p WHERE p.registration_id=r.id AND p.status='success' LIMIT 1) as paid_amount
           FROM registrations r
           JOIN users u ON r.user_id = u.id
           WHERE r.event_id = %s
           ORDER BY r.created_at DESC""",
        (event_id,)
    )
    for r in regs:
        answers = query("SELECT question_key, answer FROM registration_answers WHERE registration_id=%s", (r['id'],))
        r['answers'] = {a['question_key']: a['answer'] for a in answers}
    return regs

def get_all_registrations():
    return query(
        """SELECT r.ticket_code, r.status, r.created_at, e.title as event_title, u.name as user_name
           FROM registrations r
           JOIN events e ON r.event_id = e.id
           JOIN users u ON r.user_id = u.id
           ORDER BY r.created_at DESC"""
    )

def check_already_registered(user_id, event_id):
    return query(
        "SELECT id, ticket_code FROM registrations WHERE user_id=%s AND event_id=%s AND status!='cancelled'",
        (user_id, event_id), fetchone=True
    )

def get_registration_count(event_id):
    row = query(
        "SELECT COUNT(*) as cnt FROM registrations WHERE event_id=%s AND status!='cancelled'",
        (event_id,), fetchone=True
    )
    return row['cnt'] if row else 0

def get_registration_by_id(reg_id):
    return query("SELECT * FROM registrations WHERE id=%s", (reg_id,), fetchone=True)

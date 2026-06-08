"""
EventEase — Ticket Routes
Handles Registration Flow and Tickets
"""
import time
import random
import csv
from io import StringIO
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, Response
from utils.decorators import login_required, role_required
from models.event_model import get_event_by_id
from models.ticket_model import (
    create_registration, save_answers, create_payment, confirm_registration,
    get_tickets_by_user, get_ticket_detail, get_attendees_by_event,
    check_already_registered, get_registration_count, get_all_registrations,
    get_registration_by_id
)
from utils.qr_generator import generate_qr
from db import query

tickets_bp = Blueprint('tickets', __name__, url_prefix='/tickets')

# ── User: Register for Event ─────────────────────────
@tickets_bp.route('/register/<int:event_id>', methods=['GET', 'POST'])
@login_required
def register(event_id):
    if session.get('role') != 'user':
        flash('Only standard users can register for events.', 'warning')
        return redirect(url_for('events.detail', event_id=event_id))

    event = get_event_by_id(event_id)
    if not event or event['status'] != 'published':
        abort(404)

    # Check capacity
    if event['capacity'] > 0:
        current_count = get_registration_count(event_id)
        if current_count >= event['capacity']:
            return render_template('errors/sold_out.html', event=event)

    # Check duplicate
    existing = check_already_registered(session['user_id'], event_id)
    if existing:
        flash('You are already registered for this event.', 'info')
        return redirect(url_for('tickets.ticket_detail', ticket_code=existing['ticket_code']))

    if request.method == 'POST':
        qty = request.form.get('qty', 1, type=int)
        
        # Save standard fields to answers to keep it simple, or discard them, 
        # but let's save everything prefixed with `ans_` or standard fields
        answers = {
            'phone': request.form.get('phone', ''),
            'special_requirements': request.form.get('special_requirements', ''),
            'qty': qty
        }
        
        # Collect dynamic type-specific answers
        for k, v in request.form.items():
            if k.startswith('ans_') and v.strip():
                answers[k[4:]] = v.strip()

        reg_id, ticket_code = create_registration(session['user_id'], event_id)
        save_answers(reg_id, answers)
        
        if event['price'] == 0:
            qr_path = generate_qr(
                ticket_code, 
                event['title'], 
                session['user_name'], 
                event['date_start'].strftime('%Y-%m-%d') if event['date_start'] else 'TBD'
            )
            confirm_registration(reg_id, qr_path)
            
            from utils.email_sender import send_ticket_confirmation
            import os
            from flask import current_app
            full_qr = os.path.join(current_app.static_folder, qr_path.replace('/', os.sep))
            send_ticket_confirmation(session['user_email'], session['user_name'], event['title'], event['date_start'].strftime('%b %d, %Y'), event['venue'] or event['city'], ticket_code, full_qr)
            
            flash('Registration successful! Your free ticket is confirmed.', 'success')
            return redirect(url_for('tickets.confirmation', ticket_code=ticket_code))
            
        return redirect(url_for('tickets.payment', reg_id=reg_id))

    return render_template('tickets/register_form.html', event=event)

# ── User: Join Waitlist ──────────────────────────────
@tickets_bp.route('/waitlist/<int:event_id>', methods=['POST'])
@login_required
def waitlist(event_id):
    from db import query
    email = request.form.get('email', '').strip()
    if email:
        try:
            query("INSERT INTO waitlist (event_id, email) VALUES (%s, %s)", (event_id, email))
            flash("You've been added to the waitlist! We'll notify you if a spot opens up.", 'success')
        except Exception as e:
            flash("You are already on the waitlist or an error occurred.", 'warning')
    return redirect(url_for('events.detail', event_id=event_id))

# ── User: Payment Simulation ─────────────────────────
@tickets_bp.route('/payment/<int:reg_id>', methods=['GET', 'POST'])
@login_required
def payment(reg_id):
    if session.get('role') != 'user':
        abort(403)
        
    reg = get_registration_by_id(reg_id)
    if not reg:
        abort(404)
    if reg['user_id'] != session['user_id']:
        abort(403)
    if reg['status'] == 'confirmed':
        return redirect(url_for('tickets.confirmation', ticket_code=reg['ticket_code']))

    event = get_event_by_id(reg['event_id'])
    
    # Calculate price based on qty if saved in answers, otherwise assume 1
    # For phase 3 we just bill based on event.price for simplicity and 1 ticket per reg_id 
    # to avoid complex multi-ticket generation in this phase.
    
    subtotal = float(event['price'])
    fee = 10.0 if subtotal > 0 else 0.0
    total = subtotal + fee

    if request.method == 'POST':
        method = request.form.get('payment_method', 'free')
        txn_id = f"TXN{int(time.time())}{random.randint(1000,9999)}"
        
        if total > 0:
            create_payment(reg_id, total, method, txn_id)
            
        # Generate QR
        qr_path = generate_qr(
            reg['ticket_code'], 
            event['title'], 
            session['user_name'], 
            event['date_start'].strftime('%Y-%m-%d') if event['date_start'] else 'TBD'
        )
        
        confirm_registration(reg_id, qr_path)
        
        from utils.email_sender import send_ticket_confirmation
        import os
        from flask import current_app
        full_qr = os.path.join(current_app.static_folder, qr_path.replace('/', os.sep))
        send_ticket_confirmation(session['user_email'], session['user_name'], event['title'], event['date_start'].strftime('%b %d, %Y'), event['venue'] or event['city'], reg['ticket_code'], full_qr)
        
        flash('Payment successful! Your ticket is confirmed.', 'success')
        return redirect(url_for('tickets.confirmation', ticket_code=reg['ticket_code']))

    return render_template('tickets/payment.html', reg=reg, event=event, subtotal=subtotal, fee=fee, total=total)

# ── User: Confirmation ───────────────────────────────
@tickets_bp.route('/confirmation/<ticket_code>')
@login_required
def confirmation(ticket_code):
    ticket = get_ticket_detail(ticket_code)
    if not ticket or ticket['user_id'] != session['user_id']:
        abort(404)
    return render_template('tickets/confirmation.html', ticket=ticket)

# ── User: My Tickets List ────────────────────────────
@tickets_bp.route('/')
@login_required
def my_tickets():
    if session.get('role') != 'user':
        abort(403)
    tickets = get_tickets_by_user(session['user_id'])
    from datetime import datetime
    now = datetime.now()
    upcoming = [t for t in tickets if t['date_start'] and t['date_start'] > now and t['status'] != 'cancelled']
    past = [t for t in tickets if (t['date_start'] and t['date_start'] <= now) or t['status'] == 'cancelled']
    
    return render_template('tickets/my_tickets.html', upcoming=upcoming, past=past)

# ── User: Ticket Detail ──────────────────────────────
@tickets_bp.route('/<ticket_code>')
@login_required
def ticket_detail(ticket_code):
    ticket = get_ticket_detail(ticket_code)
    if not ticket or ticket['user_id'] != session['user_id']:
        abort(404)
    return render_template('tickets/ticket_detail.html', ticket=ticket)

# ── User: Download QR ────────────────────────────────
@tickets_bp.route('/download/<ticket_code>')
@login_required
def download_qr(ticket_code):
    ticket = get_ticket_detail(ticket_code)
    if not ticket or ticket['user_id'] != session['user_id']:
        abort(404)
    import os
    from flask import current_app, send_file
    path = os.path.join(current_app.static_folder, ticket['qr_path'].replace('/', os.sep))
    if not os.path.exists(path):
        flash('QR Code file missing.', 'danger')
        return redirect(url_for('tickets.ticket_detail', ticket_code=ticket_code))
    return send_file(path, as_attachment=True, download_name=f"{ticket_code}.png")

# ── Creator: View Attendees ──────────────────────────
@tickets_bp.route('/creator/attendees/<int:event_id>')
@role_required('creator')
def creator_attendees(event_id):
    event = get_event_by_id(event_id)
    if not event or event['creator_id'] != session['user_id']:
        abort(403)
    
    attendees = get_attendees_by_event(event_id)
    
    # CSV Export
    if request.args.get('export') == 'csv':
        def generate():
            data = StringIO()
            writer = csv.writer(data)
            writer.writerow(['Ticket Code', 'Name', 'Email', 'Status', 'Date', 'Amount Paid'])
            for a in attendees:
                writer.writerow([a['ticket_code'], a['name'], a['email'], a['status'], a['created_at'].strftime('%Y-%m-%d'), a['paid_amount']])
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)
        return Response(generate(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename=attendees_{event_id}.csv'})

    # Get events for dropdown
    from models.event_model import get_events_by_creator
    all_events = get_events_by_creator(session['user_id'])
    
    # Stats
    total_reg = len(attendees)
    confirmed = sum(1 for a in attendees if a['status'] == 'confirmed')
    revenue = sum(a['paid_amount'] or 0 for a in attendees)
    cap_pct = (confirmed / event['capacity'] * 100) if event['capacity'] > 0 else 0
    
    stats = {'total': total_reg, 'confirmed': confirmed, 'revenue': revenue, 'cap_pct': int(cap_pct)}
    
    return render_template('creator/attendees.html', event=event, attendees=attendees, all_events=all_events, stats=stats)

# ── Admin: All Registrations ─────────────────────────
@tickets_bp.route('/admin/registrations')
@role_required('admin')
def admin_registrations():
    search = request.args.get('search', '')
    filter_status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    where = ["1=1"]
    params = []

    if search:
        where.append("(r.ticket_code LIKE %s OR u.name LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    if filter_status != 'all':
        where.append("r.status=%s")
        params.append(filter_status)

    where_sql = " AND ".join(where)
    offset = (page - 1) * per_page

    regs = query(
        f"""SELECT r.ticket_code, r.status, r.created_at, e.title as event_title, u.name as user_name
           FROM registrations r
           JOIN events e ON r.event_id = e.id
           JOIN users u ON r.user_id = u.id
           WHERE {where_sql}
           ORDER BY r.created_at DESC LIMIT %s OFFSET %s""",
        params + [per_page, offset]
    )

    total = query(f"SELECT COUNT(*) as c FROM registrations r JOIN events e ON r.event_id = e.id JOIN users u ON r.user_id = u.id WHERE {where_sql}", params, fetchone=True)['c']
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template('admin/registrations.html', registrations=regs, page=page, total_pages=total_pages, search=search, filter_status=filter_status)

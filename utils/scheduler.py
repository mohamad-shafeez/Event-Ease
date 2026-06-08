"""
EventEase — APScheduler Background Jobs
Handles automating event statuses.
"""
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from db import query

def auto_end_expired_events():
    """Flips published events to 'ended' if their end date has passed."""
    try:
        res = query(
            "UPDATE events SET status='ended' WHERE date_end < NOW() AND status='published'"
        )
        if res:
            print(f"[SCHEDULER] Auto-ended {res} expired events.")
    except Exception as e:
        print(f"[SCHEDULER ERROR] auto_end_expired_events: {e}")

def auto_cancel_no_registrations():
    """Cancels draft events that never got published and are past their start date."""
    try:
        res = query(
            "UPDATE events SET status='cancelled' WHERE date_start < NOW() AND status='draft'"
        )
        if res:
            print(f"[SCHEDULER] Auto-cancelled {res} stale draft events.")
    except Exception as e:
        print(f"[SCHEDULER ERROR] auto_cancel_no_registrations: {e}")

def start_scheduler(app):
    """Initializes and starts the background scheduler."""
    scheduler = BackgroundScheduler()
    
    # Run every hour
    scheduler.add_job(func=auto_end_expired_events, trigger="interval", hours=1)
    scheduler.add_job(func=auto_cancel_no_registrations, trigger="interval", hours=1)
    
    scheduler.start()
    print("[SCHEDULER] Background jobs started.")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

"""
EventEase — Flask Application Entry Point
"""

import os
from flask import Flask, render_template, session
from extensions import bcrypt, sess
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Ensure directories exist ────────────────────────
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.QR_FOLDER, exist_ok=True)
    os.makedirs(Config.SESSION_FILE_DIR, exist_ok=True)

    # ── Init extensions ─────────────────────────────────
    bcrypt.init_app(app)
    sess.init_app(app)

    # ── Register blueprints ─────────────────────────────
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.creator import creator_bp
    from routes.user import user_bp
    from routes.events import events_bp
    from routes.tickets import tickets_bp
    from routes.ai import ai_bp
    from routes.profile import profile_bp

    from routes.password_reset import password_reset_bp
    from routes.messages import messages_bp
    from routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(creator_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(password_reset_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)

    # ── Landing page ────────────────────────────────────
    @app.route('/')
    def index():
        return render_template('index.html')

    # ── Context processor (inject role into all templates)
    @app.context_processor
    def inject_user():
        return {
            'current_user_id': session.get('user_id'),
            'current_role': session.get('role'),
            'current_name': session.get('user_name'),
        }

    # ── Error handlers ──────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # ── Seed default admin on first run ─────────────────
    with app.app_context():
        _seed_admin()
        
        # ── Start Background Scheduler ──────────────────────
        try:
            from utils.scheduler import start_scheduler
            start_scheduler(app)
        except Exception as e:
            print(f"[WARN] Scheduler failed to start: {e}")

    return app


def _seed_admin():
    """Create the default admin account if it doesn't exist."""
    try:
        from db import query
        admin = query(
            "SELECT id FROM users WHERE email = %s",
            ('admin@eventease.com',), fetchone=True
        )
        if not admin:
            pw_hash = bcrypt.generate_password_hash('Admin@123').decode('utf-8')
            query(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                ('Admin', 'admin@eventease.com', pw_hash, 'admin')
            )
            print("[OK] Default admin seeded: admin@eventease.com / Admin@123")
        else:
            print("[INFO] Admin account already exists.")
    except Exception as e:
        print(f"[WARN] Could not seed admin (is MySQL running?): {e}")


# ── Run ─────────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

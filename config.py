"""
EventEase — Application Configuration
"""

import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    # ── Flask Core ──────────────────────────────────────
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'eVeNtEaSe-s3cr3t-k3y-X9q2W7pL4mR8vB1n'
    )
    DEBUG = True

    # ── MySQL / XAMPP ───────────────────────────────────
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'eventease_db')

    # ── Flask-Session (filesystem-based) ────────────────
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(BASE_DIR, 'flask_session')
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    # ── File Upload Paths ───────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images')
    QR_FOLDER = os.path.join(BASE_DIR, 'static', 'qr_tickets')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # ── Gemini AI Settings ──────────────────────────────
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

    # ── Email / SMTP Settings ───────────────────────────
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USERNAME = ''        # creator fills their Gmail
    MAIL_PASSWORD = ''        # Gmail app password
    MAIL_FROM = 'EventEase <noreply@eventease.com>'
    MAIL_ENABLED = False      # set True only when credentials added

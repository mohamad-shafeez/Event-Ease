"""
EventEase — Shared Flask Extensions
Centralised here to avoid circular imports.
"""

from flask_bcrypt import Bcrypt
from flask_session import Session

bcrypt = Bcrypt()
sess = Session()

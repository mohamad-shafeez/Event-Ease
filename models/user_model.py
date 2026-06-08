"""
EventEase — User Model (Data Access Layer)
"""

from db import query


def create_user(name, email, password_hash, role='user'):
    """Insert a new user and return their id."""
    return query(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (name, email, password_hash, role)
    )


def get_user_by_email(email):
    """Fetch a single user by email."""
    return query(
        "SELECT * FROM users WHERE email = %s",
        (email,), fetchone=True
    )


def get_user_by_id(user_id):
    """Fetch a single user by ID."""
    return query(
        "SELECT id, name, email, role, avatar, created_at, is_banned FROM users WHERE id = %s",
        (user_id,), fetchone=True
    )


def get_all_users():
    """Return all users (admin use)."""
    return query(
        "SELECT id, name, email, role, avatar, created_at, is_banned FROM users ORDER BY created_at DESC"
    )


def ban_user(user_id):
    """Ban a user."""
    return query("UPDATE users SET is_banned = 1 WHERE id = %s", (user_id,))


def unban_user(user_id):
    """Unban a user."""
    return query("UPDATE users SET is_banned = 0 WHERE id = %s", (user_id,))


def update_avatar(user_id, avatar_path):
    """Update user avatar."""
    return query("UPDATE users SET avatar = %s WHERE id = %s", (avatar_path, user_id))


def count_users_by_role():
    """Return count of users grouped by role."""
    return query(
        "SELECT role, COUNT(*) as count FROM users GROUP BY role"
    )

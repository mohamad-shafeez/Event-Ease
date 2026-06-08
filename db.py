"""
EventEase — MySQL Connection Pool & Query Helper
Uses mysql-connector-python with pooling for XAMPP MySQL.
"""

import mysql.connector
from mysql.connector import pooling, Error
from config import Config

# ── Connection Pool ─────────────────────────────────────
_pool = None


def _get_pool():
    """Lazily create and return the connection pool."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="eventease_pool",
            pool_size=5,
            pool_reset_session=True,
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=False,
        )
    return _pool


def get_db():
    """Get a connection from the pool."""
    return _get_pool().get_connection()


def close_db(conn):
    """Return a connection to the pool."""
    if conn and conn.is_connected():
        conn.close()


# ── Query Helpers ───────────────────────────────────────

def query(sql, params=None, fetchone=False):
    """
    Execute a SQL query and return results as dict rows.
    For INSERT/UPDATE/DELETE, commits and returns lastrowid.
    For SELECT, returns list of dicts (or single dict if fetchone=True).
    """
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        verb = sql.strip().split()[0].upper()
        if verb in ('INSERT', 'UPDATE', 'DELETE', 'REPLACE'):
            conn.commit()
            return cursor.lastrowid
        if fetchone:
            return cursor.fetchone()
        return cursor.fetchall()
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        close_db(conn)


def execute_many(sql, data_list):
    """Execute a batch of statements (e.g. bulk inserts)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.executemany(sql, data_list)
        conn.commit()
        return cursor.rowcount
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        close_db(conn)

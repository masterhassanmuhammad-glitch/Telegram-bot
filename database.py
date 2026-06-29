import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from config import DATABASE_URL

# ============================================
# Database Connection
# ============================================

@contextmanager
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def execute(query, params=None, fetch=False, fetchone=False):
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cur.execute(query, params)

            result = None

            if fetch:
                result = cur.fetchall()

            elif fetchone:
                result = cur.fetchone()

            conn.commit()

            return result

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()


# ============================================
# Database Initialization
# ============================================

def init_db():

    execute("""
    CREATE TABLE IF NOT EXISTS menu_items(
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        type TEXT NOT NULL,
        parent_id INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        description TEXT DEFAULT ''
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS file_attachments(
        id SERIAL PRIMARY KEY,
        item_id INTEGER REFERENCES menu_items(id) ON DELETE CASCADE,
        file_id TEXT NOT NULL,
        file_type TEXT NOT NULL,
        caption TEXT DEFAULT ''
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS admins(
        user_id BIGINT PRIMARY KEY
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        username TEXT,
        message_text TEXT,
        status INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS bot_settings(
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)


# ============================================
# Default Data
# ============================================

def init_settings(owner_id):

    execute("""
    INSERT INTO admins(user_id)
    VALUES(%s)
    ON CONFLICT(user_id)
    DO NOTHING
    """, (owner_id,))

    execute("""
    INSERT INTO bot_settings(key,value)
    VALUES(
        'main_menu_text',
        'اختر القسم المناسب من الأسفل:'
    )
    ON CONFLICT(key)
    DO NOTHING
    """)


# ============================================
# Recursive Delete
# ============================================

def delete_item_recursive(item_id):

    with get_connection() as conn:

        cur = conn.cursor()

        try:

            _delete(cur, item_id)

            conn.commit()

        except Exception:

            conn.rollback()

            raise

        finally:

            cur.close()


def _delete(cur, item_id):

    cur.execute(
        "SELECT id FROM menu_items WHERE parent_id=%s",
        (item_id,)
    )

    children = cur.fetchall()

    for child in children:
        _delete(cur, child[0])

    cur.execute(
        "DELETE FROM file_attachments WHERE item_id=%s",
        (item_id,)
    )

    cur.execute(
        "DELETE FROM menu_items WHERE id=%s",
        (item_id,)
    )

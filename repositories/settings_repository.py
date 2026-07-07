from core.database import execute


def get(key):
    return execute(
        "SELECT value FROM settings WHERE key=%s",
        (key,),
        fetchone=True
    )


def set(key, value):
    execute("""
        INSERT INTO settings(key, value)
        VALUES(%s, %s)
        ON CONFLICT(key)
        DO UPDATE SET value=EXCLUDED.value
    """, (key, value), commit=True)


def delete(key):
    execute(
        "DELETE FROM settings WHERE key=%s",
        (key,),
        commit=True
    )


def all():
    return execute(
        "SELECT * FROM settings ORDER BY key",
        fetchall=True
    )

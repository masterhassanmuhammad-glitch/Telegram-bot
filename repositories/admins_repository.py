from core.database import execute


def add(telegram_id, role="admin"):
    execute("""
        INSERT INTO admins(telegram_id, role)
        VALUES(%s, %s)
        ON CONFLICT(telegram_id)
        DO UPDATE SET role=EXCLUDED.role
    """, (telegram_id, role), commit=True)


def get(telegram_id):
    return execute(
        "SELECT * FROM admins WHERE telegram_id=%s",
        (telegram_id,),
        fetchone=True
    )


def exists(telegram_id):
    return get(telegram_id) is not None


def role(telegram_id):
    admin = get(telegram_id)

    if admin:
        return admin["role"]

    return None


def remove(telegram_id):
    execute(
        "DELETE FROM admins WHERE telegram_id=%s",
        (telegram_id,),
        commit=True
    )


def count():
    row = execute(
        "SELECT COUNT(*) AS total FROM admins",
        fetchone=True
    )

    return row["total"]


def all():
    return execute("""
        SELECT *
        FROM admins
        ORDER BY created_at ASC
    """, fetchall=True)

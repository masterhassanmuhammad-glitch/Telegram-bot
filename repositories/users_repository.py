from core.database import execute


def create(
    telegram_id,
    username=None,
    first_name=None,
    last_name=None,
    language_code=None
):
    execute("""
        INSERT INTO users(
            telegram_id,
            username,
            first_name,
            last_name,
            language_code
        )
        VALUES(%s,%s,%s,%s,%s)
        ON CONFLICT(telegram_id)
        DO NOTHING
    """, (
        telegram_id,
        username,
        first_name,
        last_name,
        language_code
    ), commit=True)


def get(telegram_id):
    return execute(
        "SELECT * FROM users WHERE telegram_id=%s",
        (telegram_id,),
        fetchone=True
    )


def update_last_seen(telegram_id):
    execute("""
        UPDATE users
        SET last_seen=NOW()
        WHERE telegram_id=%s
    """, (telegram_id,), commit=True)


def update_profile(
    telegram_id,
    username,
    first_name,
    last_name,
    language_code
):
    execute("""
        UPDATE users
        SET
            username=%s,
            first_name=%s,
            last_name=%s,
            language_code=%s,
            last_seen=NOW()
        WHERE telegram_id=%s
    """, (
        username,
        first_name,
        last_name,
        language_code,
        telegram_id
    ), commit=True)


def ban(telegram_id):
    execute("""
        UPDATE users
        SET is_banned=TRUE
        WHERE telegram_id=%s
    """, (telegram_id,), commit=True)


def unban(telegram_id):
    execute("""
        UPDATE users
        SET is_banned=FALSE
        WHERE telegram_id=%s
    """, (telegram_id,), commit=True)


def delete(telegram_id):
    execute(
        "DELETE FROM users WHERE telegram_id=%s",
        (telegram_id,),
        commit=True
    )


def count():
    row = execute(
        "SELECT COUNT(*) AS total FROM users",
        fetchone=True
    )

    return row["total"]


def all():
    return execute("""
        SELECT *
        FROM users
        ORDER BY joined_at DESC
    """, fetchall=True)

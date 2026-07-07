from core.database import execute


def get(telegram_id):
    return execute(
        "SELECT * FROM sessions WHERE telegram_id=%s",
        (telegram_id,),
        fetchone=True
    )


def create(
    telegram_id,
    current_menu=0,
    current_state="",
    panel_message_id=None
):
    execute("""
        INSERT INTO sessions(
            telegram_id,
            current_menu,
            current_state,
            panel_message_id
        )
        VALUES(%s,%s,%s,%s)
        ON CONFLICT (telegram_id)
        DO NOTHING
    """, (
        telegram_id,
        current_menu,
        current_state,
        panel_message_id
    ), commit=True)


def save(
    telegram_id,
    current_menu,
    current_state,
    panel_message_id
):
    execute("""
        INSERT INTO sessions(
            telegram_id,
            current_menu,
            current_state,
            panel_message_id
        )
        VALUES(%s,%s,%s,%s)
        ON CONFLICT (telegram_id)
        DO UPDATE SET
            current_menu=EXCLUDED.current_menu,
            current_state=EXCLUDED.current_state,
            panel_message_id=EXCLUDED.panel_message_id,
            updated_at=NOW()
    """, (
        telegram_id,
        current_menu,
        current_state,
        panel_message_id
    ), commit=True)


def update_menu(telegram_id, menu_id):
    execute("""
        UPDATE sessions
        SET
            current_menu=%s,
            updated_at=NOW()
        WHERE telegram_id=%s
    """, (
        menu_id,
        telegram_id
    ), commit=True)


def update_state(telegram_id, state):
    execute("""
        UPDATE sessions
        SET
            current_state=%s,
            updated_at=NOW()
        WHERE telegram_id=%s
    """, (
        state,
        telegram_id
    ), commit=True)


def update_panel(telegram_id, message_id):
    execute("""
        UPDATE sessions
        SET
            panel_message_id=%s,
            updated_at=NOW()
        WHERE telegram_id=%s
    """, (
        message_id,
        telegram_id
    ), commit=True)


def delete(telegram_id):
    execute(
        "DELETE FROM sessions WHERE telegram_id=%s",
        (telegram_id,),
        commit=True
    )

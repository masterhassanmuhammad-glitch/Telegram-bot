from core.database import execute


def add(button_id, admin_id, action):

    execute("""
        INSERT INTO button_logs(
            button_id,
            admin_id,
            action
        )
        VALUES(%s,%s,%s)
    """, (
        button_id,
        admin_id,
        action
    ), commit=True)

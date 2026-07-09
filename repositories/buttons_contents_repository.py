from core.database import execute


def add(button_id, content_id, sort_order=0):
    execute("""
        INSERT INTO button_contents(
            button_id,
            content_id,
            sort_order
        )
        VALUES(%s,%s,%s)
    """, (
        button_id,
        content_id,
        sort_order
    ), commit=True)


def by_button(button_id):
    return execute("""
        SELECT c.*
        FROM button_contents bc
        JOIN contents c
        ON c.id=bc.content_id
        WHERE bc.button_id=%s
        ORDER BY bc.sort_order
    """, (
        button_id,
    ), fetchall=True)


def remove(button_id, content_id):
    execute("""
        DELETE FROM button_contents
        WHERE
        button_id=%s
        AND content_id=%s
    """, (
        button_id,
        content_id
    ), commit=True)

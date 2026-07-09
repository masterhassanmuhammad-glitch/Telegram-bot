from core.database import execute


def add(button_id, media_id, sort_order=0):
    execute("""
        INSERT INTO button_media(
            button_id,
            media_id,
            sort_order
        )
        VALUES(%s,%s,%s)
    """, (
        button_id,
        media_id,
        sort_order
    ), commit=True)


def by_button(button_id):
    return execute("""
        SELECT m.*
        FROM button_media bm
        JOIN media m
        ON bm.media_id=m.id
        WHERE bm.button_id=%s
        ORDER BY bm.sort_order
    """, (
        button_id,
    ), fetchall=True)


def remove(button_id, media_id):
    execute("""
        DELETE FROM button_media
        WHERE
            button_id=%s
            AND media_id=%s
    """, (
        button_id,
        media_id
    ), commit=True)

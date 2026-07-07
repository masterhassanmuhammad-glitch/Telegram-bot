from core.database import execute


def create(
    title="",
    content_type="TEXT",
    body="",
    sort_order=0
):
    return execute("""
        INSERT INTO contents(
            title,
            content_type,
            body,
            sort_order
        )
        VALUES(%s,%s,%s,%s)
        RETURNING *
    """, (
        title,
        content_type,
        body,
        sort_order
    ), fetchone=True, commit=True)


def get(content_id):
    return execute(
        "SELECT * FROM contents WHERE id=%s",
        (content_id,),
        fetchone=True
    )


def update(
    content_id,
    title,
    content_type,
    body,
    sort_order
):
    execute("""
        UPDATE contents
        SET
            title=%s,
            content_type=%s,
            body=%s,
            sort_order=%s
        WHERE id=%s
    """, (
        title,
        content_type,
        body,
        sort_order,
        content_id
    ), commit=True)


def delete(content_id):
    execute(
        "DELETE FROM contents WHERE id=%s",
        (content_id,),
        commit=True
    )


def search(keyword):
    return execute("""
        SELECT *
        FROM contents
        WHERE
            title ILIKE %s
            OR body ILIKE %s
        ORDER BY sort_order,id
    """, (
        f"%{keyword}%",
        f"%{keyword}%"
    ), fetchall=True)


def all():
    return execute("""
        SELECT *
        FROM contents
        ORDER BY sort_order,id
    """, fetchall=True)


def count():
    row = execute(
        "SELECT COUNT(*) AS total FROM contents",
        fetchone=True
    )

    return row["total"]

from core.database import execute


def create(
    file_id,
    file_unique_id,
    media_type,
    file_name="",
    caption="",
    file_size=0
):
    return execute("""
        INSERT INTO media(
            file_id,
            file_unique_id,
            media_type,
            file_name,
            caption,
            file_size
        )
        VALUES(%s,%s,%s,%s,%s,%s)
        RETURNING *
    """, (
        file_id,
        file_unique_id,
        media_type,
        file_name,
        caption,
        file_size
    ), fetchone=True, commit=True)


def get(media_id):
    return execute(
        "SELECT * FROM media WHERE id=%s",
        (media_id,),
        fetchone=True
    )


def get_by_file_unique_id(file_unique_id):
    return execute(
        "SELECT * FROM media WHERE file_unique_id=%s",
        (file_unique_id,),
        fetchone=True
    )


def update(
    media_id,
    file_name,
    caption
):
    execute("""
        UPDATE media
        SET
            file_name=%s,
            caption=%s
        WHERE id=%s
    """, (
        file_name,
        caption,
        media_id
    ), commit=True)


def delete(media_id):
    execute(
        "DELETE FROM media WHERE id=%s",
        (media_id,),
        commit=True
    )


def all():
    return execute("""
        SELECT *
        FROM media
        ORDER BY id DESC
    """, fetchall=True)


def count():
    row = execute(
        "SELECT COUNT(*) AS total FROM media",
        fetchone=True
    )

    return row["total"]

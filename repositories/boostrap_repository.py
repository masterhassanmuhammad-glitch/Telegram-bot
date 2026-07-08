from core.database import execute


def has_root():

    row = execute(
        "SELECT COUNT(*) AS total FROM menus",
        fetchone=True
    )

    return row["total"] > 0


def create_root():

    execute("""
        INSERT INTO menus(
            id,
            parent_id,
            title,
            description,
            sort_order
        )
        VALUES(
            0,
            0,
            'MedicalBot',
            'مرحباً بك',
            0
        )
        ON CONFLICT DO NOTHING
    """, commit=True)

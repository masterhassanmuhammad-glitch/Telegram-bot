from core.database import execute


def create(
    title,
    parent_id=0,
    description="",
    icon="",
    sort_order=0,
    visible=True
):
    return execute("""
        INSERT INTO menus(
            parent_id,
            title,
            description,
            icon,
            sort_order,
            visible
        )
        VALUES(%s,%s,%s,%s,%s,%s)
        RETURNING *
    """, (
        parent_id,
        title,
        description,
        icon,
        sort_order,
        visible
    ), fetchone=True, commit=True)


def get(menu_id):
    return execute(
        "SELECT * FROM menus WHERE id=%s",
        (menu_id,),
        fetchone=True
    )


def root():
    return execute("""
        SELECT *
        FROM menus
        WHERE parent_id=0
        AND visible=TRUE
        ORDER BY sort_order,id
    """, fetchall=True)


def children(parent_id):
    return execute("""
        SELECT *
        FROM menus
        WHERE parent_id=%s
        AND visible=TRUE
        ORDER BY sort_order,id
    """, (parent_id,), fetchall=True)


def update(
    menu_id,
    title,
    description,
    icon,
    sort_order,
    visible
):
    execute("""
        UPDATE menus
        SET
            title=%s,
            description=%s,
            icon=%s,
            sort_order=%s,
            visible=%s
        WHERE id=%s
    """, (
        title,
        description,
        icon,
        sort_order,
        visible,
        menu_id
    ), commit=True)


def delete(menu_id):
    execute(
        "DELETE FROM menus WHERE id=%s",
        (menu_id,),
        commit=True
    )


def count():
    row = execute(
        "SELECT COUNT(*) AS total FROM menus",
        fetchone=True
    )

    return row["total"]


def all():
    return execute("""
        SELECT *
        FROM menus
        ORDER BY parent_id,sort_order,id
    """, fetchall=True)

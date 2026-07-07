from core.database import execute


def create(
    menu_id,
    text,
    emoji="",
    action_type="MENU",
    action_value="",
    sort_order=0,
    visible=True,
    admin_only=False
):
    return execute("""
        INSERT INTO buttons(
            menu_id,
            text,
            emoji,
            action_type,
            action_value,
            sort_order,
            visible,
            admin_only
        )
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING *
    """, (
        menu_id,
        text,
        emoji,
        action_type,
        action_value,
        sort_order,
        visible,
        admin_only
    ), fetchone=True, commit=True)


def get(button_id):
    return execute(
        "SELECT * FROM buttons WHERE id=%s",
        (button_id,),
        fetchone=True
    )


def by_menu(menu_id, is_admin=False):
    if is_admin:
        return execute("""
            SELECT *
            FROM buttons
            WHERE menu_id=%s
            AND visible=TRUE
            ORDER BY sort_order,id
        """, (menu_id,), fetchall=True)

    return execute("""
        SELECT *
        FROM buttons
        WHERE menu_id=%s
        AND visible=TRUE
        AND admin_only=FALSE
        ORDER BY sort_order,id
    """, (menu_id,), fetchall=True)


def update(
    button_id,
    text,
    emoji,
    action_type,
    action_value,
    sort_order,
    visible,
    admin_only
):
    execute("""
        UPDATE buttons
        SET
            text=%s,
            emoji=%s,
            action_type=%s,
            action_value=%s,
            sort_order=%s,
            visible=%s,
            admin_only=%s
        WHERE id=%s
    """, (
        text,
        emoji,
        action_type,
        action_value,
        sort_order,
        visible,
        admin_only,
        button_id
    ), commit=True)


def delete(button_id):
    execute(
        "DELETE FROM buttons WHERE id=%s",
        (button_id,),
        commit=True
    )


def move(button_id, new_order):
    execute("""
        UPDATE buttons
        SET sort_order=%s
        WHERE id=%s
    """, (new_order, button_id), commit=True)


def count():
    row = execute(
        "SELECT COUNT(*) AS total FROM buttons",
        fetchone=True
    )

    return row["total"]


def all():
    return execute("""
        SELECT *
        FROM buttons
        ORDER BY menu_id,sort_order,id
    """, fetchall=True)

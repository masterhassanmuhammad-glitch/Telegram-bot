from repositories import buttons_repository


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
    return buttons_repository.create(
        menu_id=menu_id,
        text=text,
        emoji=emoji,
        action_type=action_type,
        action_value=action_value,
        sort_order=sort_order,
        visible=visible,
        admin_only=admin_only
    )


def get(button_id):
    return buttons_repository.get(button_id)


def by_menu(menu_id, is_admin=False):
    return buttons_repository.by_menu(menu_id, is_admin)


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
    buttons_repository.update(
        button_id,
        text,
        emoji,
        action_type,
        action_value,
        sort_order,
        visible,
        admin_only
    )


def delete(button_id):
    buttons_repository.delete(button_id)


def move(button_id, new_order):
    buttons_repository.move(button_id, new_order)


def count():
    return buttons_repository.count()


def all():
    return buttons_repository.all()

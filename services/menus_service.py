from repositories import menus_repository


def create(
    title,
    parent_id=0,
    description="",
    icon="",
    sort_order=0,
    visible=True
):
    return menus_repository.create(
        title=title,
        parent_id=parent_id,
        description=description,
        icon=icon,
        sort_order=sort_order,
        visible=visible
    )


def get(menu_id):
    return menus_repository.get(menu_id)


def root():
    return menus_repository.root()


def children(parent_id):
    return menus_repository.children(parent_id)


def update(
    menu_id,
    title,
    description,
    icon,
    sort_order,
    visible
):
    menus_repository.update(
        menu_id,
        title,
        description,
        icon,
        sort_order,
        visible
    )


def delete(menu_id):
    menus_repository.delete(menu_id)


def count():
    return menus_repository.count()


def all():
    return menus_repository.all()

from repositories import button_contents_repository


def add(button_id, content_id, sort_order=0):
    button_contents_repository.add(
        button_id,
        content_id,
        sort_order
    )


def by_button(button_id):
    return button_contents_repository.by_button(
        button_id
    )


def remove(button_id, content_id):
    button_contents_repository.remove(
        button_id,
        content_id
    )

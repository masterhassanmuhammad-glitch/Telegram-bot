from repositories import button_media_repository


def add(button_id, media_id, sort_order=0):
    button_media_repository.add(
        button_id,
        media_id,
        sort_order
    )


def by_button(button_id):
    return button_media_repository.by_button(
        button_id
    )


def remove(button_id, media_id):
    button_media_repository.remove(
        button_id,
        media_id
    )

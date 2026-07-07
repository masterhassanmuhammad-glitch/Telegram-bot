from repositories import media_repository


def create(
    file_id,
    file_unique_id,
    media_type,
    file_name="",
    caption="",
    file_size=0
):
    exists = media_repository.get_by_file_unique_id(file_unique_id)

    if exists:
        return exists

    return media_repository.create(
        file_id=file_id,
        file_unique_id=file_unique_id,
        media_type=media_type,
        file_name=file_name,
        caption=caption,
        file_size=file_size
    )


def get(media_id):
    return media_repository.get(media_id)


def update(
    media_id,
    file_name,
    caption
):
    media_repository.update(
        media_id,
        file_name,
        caption
    )


def delete(media_id):
    media_repository.delete(media_id)


def all():
    return media_repository.all()


def count():
    return media_repository.count()

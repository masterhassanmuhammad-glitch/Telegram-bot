from repositories import contents_repository


def create(
    title="",
    content_type="TEXT",
    body="",
    sort_order=0
):
    return contents_repository.create(
        title=title,
        content_type=content_type,
        body=body,
        sort_order=sort_order
    )


def get(content_id):
    return contents_repository.get(content_id)


def update(
    content_id,
    title,
    content_type,
    body,
    sort_order
):
    contents_repository.update(
        content_id,
        title,
        content_type,
        body,
        sort_order
    )


def delete(content_id):
    contents_repository.delete(content_id)


def search(keyword):
    return contents_repository.search(keyword)


def all():
    return contents_repository.all()


def count():
    return contents_repository.count()

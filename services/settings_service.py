from repositories import settings_repository


def get(key, default=None):
    row = settings_repository.get(key)

    if row:
        return row["value"]

    return default


def set(key, value):
    settings_repository.set(key, value)


def delete(key):
    settings_repository.delete(key)


def all():
    return settings_repository.all()

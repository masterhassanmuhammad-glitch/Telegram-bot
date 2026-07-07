from repositories import admins_repository


def add(telegram_id, role="admin"):
    admins_repository.add(telegram_id, role)


def remove(telegram_id):
    admins_repository.remove(telegram_id)


def is_admin(telegram_id):
    return admins_repository.exists(telegram_id)


def is_owner(telegram_id):
    admin = admins_repository.get(telegram_id)

    if not admin:
        return False

    return admin["role"] == "owner"


def role(telegram_id):
    return admins_repository.role(telegram_id)


def count():
    return admins_repository.count()


def all():
    return admins_repository.all()

from repositories import users_repository


def register(user):
    exists = users_repository.get(user.id)

    if exists:
        users_repository.update_profile(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code
        )
        return

    users_repository.create(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code
    )


def get(telegram_id):
    return users_repository.get(telegram_id)


def ban(telegram_id):
    users_repository.ban(telegram_id)


def unban(telegram_id):
    users_repository.unban(telegram_id)


def delete(telegram_id):
    users_repository.delete(telegram_id)


def count():
    return users_repository.count()


def all():
    return users_repository.all()

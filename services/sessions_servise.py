from repositories import sessions_repository


def get(telegram_id):
    session = sessions_repository.get(telegram_id)

    if session:
        return session

    sessions_repository.create(telegram_id)

    return sessions_repository.get(telegram_id)


def save(
    telegram_id,
    current_menu,
    current_state,
    panel_message_id
):
    sessions_repository.save(
        telegram_id,
        current_menu,
        current_state,
        panel_message_id
    )


def menu(telegram_id):
    return get(telegram_id)["current_menu"]


def state(telegram_id):
    return get(telegram_id)["current_state"]


def panel(telegram_id):
    return get(telegram_id)["panel_message_id"]


def set_menu(telegram_id, menu_id):
    sessions_repository.update_menu(
        telegram_id,
        menu_id
    )


def set_state(telegram_id, state):
    sessions_repository.update_state(
        telegram_id,
        state
    )


def set_panel(telegram_id, message_id):
    sessions_repository.update_panel(
        telegram_id,
        message_id
    )


def delete(telegram_id):
    sessions_repository.delete(telegram_id)

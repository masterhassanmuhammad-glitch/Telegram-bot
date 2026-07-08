from telegram import Update

from services import (
    menus_service,
    buttons_service,
    settings_service,
    admins_service,
    sessions_service
)

from ui.keyboards import build_keyboard


async def render_menu(update: Update, menu_id=0):

    user = update.effective_user
    chat = update.effective_chat

    is_admin = admins_service.is_admin(user.id)

    if menu_id == 0:
        menu = {
            "title": settings_service.get("bot_name", "MedicalBot"),
            "description": settings_service.get(
                "welcome_message",
                "مرحباً بك"
            )
        }
    else:
        menu = menus_service.get(menu_id)

    buttons = buttons_service.by_menu(menu_id, is_admin)

    keyboard = build_keyboard(
        buttons,
        int(settings_service.get("buttons_per_row", 2))
    )

    session = sessions_service.get(user.id)

    if session["panel_message_id"]:

        try:
            await chat.delete_message(
                session["panel_message_id"]
            )
        except:
            pass

    message = await chat.send_message(
        text=f"<b>{menu['title']}</b>\n\n{menu['description']}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    sessions_service.save(
        telegram_id=user.id,
        current_menu=menu_id,
        current_state="MENU",
        panel_message_id=message.message_id
    )

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes
)

from services.admins_service import is_admin
from services import menus_service


async def sort_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    menus = menus_service.all()

    keyboard = []

    for menu in menus:

        keyboard.append([
            InlineKeyboardButton(
                "⬆️",
                callback_data=f"menu_up:{menu['id']}"
            ),
            InlineKeyboardButton(
                f"{menu.get('icon') or '📁'} {menu['title']}",
                callback_data="ignore"
            ),
            InlineKeyboardButton(
                "⬇️",
                callback_data=f"menu_down:{menu['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 رجوع",
            callback_data="admin:menus"
        )
    ])

    await query.edit_message_text(
        "📂 ترتيب الأقسام",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def move_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    action, menu_id = query.data.split(":")

    menu_id = int(menu_id)

    menu = menus_service.get(menu_id)

    if not menu:
        return

    if action == "menu_up":
        new_order = max(menu["sort_order"] - 1, 0)

    else:
        new_order = menu["sort_order"] + 1

    menus_service.update(
        menu_id=menu["id"],
        title=menu["title"],
        description=menu["description"],
        icon=menu["icon"],
        sort_order=new_order,
        visible=menu["visible"]
    )

    await sort_menu(update, context)


def register(application):

    application.add_handler(
        CallbackQueryHandler(
            sort_menu,
            pattern="^admin:sort_menu$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            move_menu,
            pattern="^(menu_up|menu_down):"
        )
  )

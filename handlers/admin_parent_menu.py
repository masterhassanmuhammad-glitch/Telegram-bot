from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

from services.admins_service import is_admin
from services.admin_state import get as get_state, set as set_state
from services import menus_service


async def choose_parent(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    menus = menus_service.all()

    keyboard = [
        [
            InlineKeyboardButton(
                "🏠 قسم رئيسي",
                callback_data="parent:0"
            )
        ]
    ]

    for menu in menus:

        keyboard.append([
            InlineKeyboardButton(
                f"{menu.get('icon') or '📁'} {menu['title']}",
                callback_data=f"parent:{menu['id']}"
            )
        ])

    await query.edit_message_text(
        "اختر القسم الأب:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def parent_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    parent = int(query.data.split(":")[1])

    state = get_state(query.from_user.id)

    data = state["data"]

    data["parent_id"] = parent

    set_state(
        query.from_user.id,
        "MENU_SORT",
        data
    )

    await query.edit_message_text(
        "أرسل ترتيب القسم:"
    )


def register(application):

    application.add_handler(
        CallbackQueryHandler(
            choose_parent,
            pattern="^admin:parent$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            parent_selected,
            pattern="^parent:"
        )
    )

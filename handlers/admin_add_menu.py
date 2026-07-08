from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters

from services.admins_service import is_admin
from services.admin_state import (
    set as set_state,
    get as get_state,
    clear as clear_state
)
from services import menus_service


async def start_add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    set_state(
        query.from_user.id,
        "MENU_TITLE"
    )

    await query.edit_message_text(
        "📝 أرسل اسم القسم:"
    )


async def receive_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    state = get_state(user.id)

    if not state:
        return

    action = state["action"]

    # ==========================
    # TITLE
    # ==========================

    if action == "MENU_TITLE":

        state["data"]["title"] = update.message.text

        set_state(
            user.id,
            "MENU_DESCRIPTION",
            state["data"]
        )

        await update.message.reply_text(
            "📄 أرسل وصف القسم:"
        )

        return

    # ==========================
    # DESCRIPTION
    # ==========================

    if action == "MENU_DESCRIPTION":

        state["data"]["description"] = update.message.text

        set_state(
            user.id,
            "MENU_ICON",
            state["data"]
        )

        await update.message.reply_text(
            "😀 أرسل الإيموجي:"
        )

        return

    # ==========================
    # ICON
    # ==========================

    if action == "MENU_ICON":

        data = state["data"]

        data["icon"] = update.message.text

set_state(
    user.id,
    "MENU_PARENT",
    data
)
if action == "MENU_SORT":

    data = state["data"]

    menus_service.create(
        title=data["title"],
        description=data["description"],
        icon=data["icon"],
        parent_id=data["parent_id"],
        sort_order=int(update.message.text),
        visible=True
    )

    clear_state(user.id)

    await update.message.reply_text(
        "✅ تم إنشاء القسم بنجاح."
    )

    return

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

keyboard = [
    [
        InlineKeyboardButton(
            "➡️ اختيار القسم الأب",
            callback_data="admin:parent"
        )
    ]
]

await update.message.reply_text(
    "اضغط لاختيار القسم الأب.",
    reply_markup=InlineKeyboardMarkup(keyboard)
)

return
        )

        clear_state(user.id)

        await update.message.reply_text(
            "✅ تم إنشاء القسم."
        )


def register(application):

    application.add_handler(
        CallbackQueryHandler(
            start_add_menu,
            pattern="^admin:add_menu$"
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_menu
        )
      )

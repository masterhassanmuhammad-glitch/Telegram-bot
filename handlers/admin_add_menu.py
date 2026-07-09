from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters

from services.admins_service import is_admin
from services.admin_state import (
    set as set_state,
    get as get_state,
    clear_state
)
from services import menus_service


async def start_add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    # تهيئة الحالة وإضافة هيكل البيانات الأساسي
    set_state(
        query.from_user.id,
        {"action": "MENU_TITLE", "data": {}}
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
            {"action": "MENU_DESCRIPTION", "data": state["data"]}
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
            {"action": "MENU_ICON", "data": state["data"]}
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
            {"action": "MENU_PARENT", "data": data}
        )

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

    # ==========================
    # SORT
    # ==========================
    if action == "MENU_SORT":
        data = state["data"]

        try:
            sort_order = int(update.message.text)
        except ValueError:
            await update.message.reply_text("⚠️ يرجى إدخال رقم صحيح للترتيب:")
            return

        menus_service.create(
            title=data["title"],
            description=data["description"],
            icon=data["icon"],
            parent_id=data.get("parent_id"),  # تأكد من استقبال الـ parent_id في مكان آخر عبر الـ Callback
            sort_order=sort_order,
            visible=True
        )

        clear_state(user.id)

        await update.message.reply_text(
            "✅ تم إنشاء القسم بنجاح."
        )
        return


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
    

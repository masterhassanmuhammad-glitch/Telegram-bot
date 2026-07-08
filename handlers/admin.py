from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from services.admins_service import is_admin
from ui.admin_panel import render_admin_panel


async def admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if not query.data.startswith("admin:"):
        return

    if not is_admin(query.from_user.id):
        await query.answer("غير مصرح", show_alert=True)
        return

    await query.answer()

    action = query.data.split(":")[1]

    if action == "panel":
        await render_admin_panel(update)


def register(application):
    application.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern=r"^admin:"
        )
    )

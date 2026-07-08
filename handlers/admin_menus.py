from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from services.admins_service import is_admin
from services import menus_service


async def admin_menus(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    menus = menus_service.all()

    text = "📂 إدارة الأقسام\n\n"

    if not menus:
        text += "لا توجد أقسام."
    else:
        for menu in menus:
            icon = menu["icon"] or "📁"
            text += f"{icon} {menu['id']} - {menu['title']}\n"

    keyboard = [
        [
            {
                "text": "➕ إضافة قسم",
                "callback_data": "admin:add_menu"
            }
        ],
        [
            {
                "text": "✏️ تعديل قسم",
                "callback_data": "admin:edit_menu"
            },
            {
                "text": "🗑 حذف قسم",
                "callback_data": "admin:delete_menu"
            }
        ],
        [
            {
                "text": "⬆️ ترتيب الأقسام",
                "callback_data": "admin:sort_menu"
            }
        ],
        [
            {
                "text": "🔙 رجوع",
                "callback_data": "admin:panel"
            }
        ]
    ]

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    markup = []

    for row in keyboard:
        r = []
        for btn in row:
            r.append(
                InlineKeyboardButton(
                    btn["text"],
                    callback_data=btn["callback_data"]
                )
            )
        markup.append(r)

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(markup)
    )


def register(application):
    application.add_handler(
        CallbackQueryHandler(
            admin_menus,
            pattern=r"^admin:menus$"
        )
  )

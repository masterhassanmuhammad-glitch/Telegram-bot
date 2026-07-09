from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ContextTypes

from services.admins_service import is_admin
from services import buttons_service


async def buttons_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    buttons = buttons_service.all()

    text = "🔘 إدارة الأزرار\n\n"

    if not buttons:
        text += "لا توجد أزرار."
    else:
        for button in buttons:
            text += f"#{button['id']} - {button['text']}\n"

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ إضافة زر",
                callback_data="button:add"
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ تعديل زر",
                callback_data="button:edit"
            ),
            InlineKeyboardButton(
                "🗑 حذف زر",
                callback_data="button:delete"
            )
        ],
        [
            InlineKeyboardButton(
                "⬆️ ترتيب الأزرار",
                callback_data="button:sort"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 رجوع",
                callback_data="admin:panel"
            )
        ]
    ]

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def register(application):

    application.add_handler(
        CallbackQueryHandler(
            buttons_panel,
            pattern="^admin:buttons$"
        )
)

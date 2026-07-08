from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup


async def render_admin_panel(update):

    query = update.callback_query

    keyboard = [

        [
            InlineKeyboardButton(
                "📂 الأقسام",
                callback_data="admin:menus"
            ),
            InlineKeyboardButton(
                "🔘 الأزرار",
                callback_data="admin:buttons"
            )
        ],

        [
            InlineKeyboardButton(
                "📝 المحتويات",
                callback_data="admin:contents"
            ),
            InlineKeyboardButton(
                "🖼 الوسائط",
                callback_data="admin:media"
            )
        ],

        [
            InlineKeyboardButton(
                "⚙️ الإعدادات",
                callback_data="admin:settings"
            ),
            InlineKeyboardButton(
                "👥 المستخدمون",
                callback_data="admin:users"
            )
        ],

        [
            InlineKeyboardButton(
                "📢 الإذاعة",
                callback_data="admin:broadcast"
            ),
            InlineKeyboardButton(
                "💾 النسخ الاحتياطي",
                callback_data="admin:backup"
            )
        ],

        [
            InlineKeyboardButton(
                "❌ إغلاق",
                callback_data="admin:close"
            )
        ]

    ]

    await query.edit_message_text(
        "⚙ لوحة الإدارة",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

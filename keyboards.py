import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ============================================
# MAIN MENU KEYBOARD
# ============================================

def main_menu_keyboard(items):
    """
    items: list of dicts -> [{"id":1, "title":"..."}]
    """
    markup = InlineKeyboardMarkup()

    for item in items:
        markup.add(
            InlineKeyboardButton(
                text=item["title"],
                callback_data=f"open_{item['id']}"
            )
        )

    return markup


# ============================================
# BACK BUTTON
# ============================================

def back_keyboard(parent_id):
    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton(
            text="🔙 رجوع",
            callback_data=f"back_{parent_id}"
        )
    )

    return markup


# ============================================
# ADMIN MENU
# ============================================

def admin_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton("➕ إضافة قسم", callback_data="admin_add_item"),
        InlineKeyboardButton("🗑 حذف قسم", callback_data="admin_delete_item"),
    )

    markup.add(
        InlineKeyboardButton("📂 إضافة ملف", callback_data="admin_add_file"),
        InlineKeyboardButton("📢 إرسال رسالة", callback_data="admin_broadcast"),
    )

    markup.add(
        InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users"),
        InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings"),
    )

    return markup


# ============================================
# ITEM ACTIONS (FILES / CONTENT)
# ============================================

def item_actions_keyboard(item_id, has_children=False):
    markup = InlineKeyboardMarkup()

    if has_children:
        markup.add(
            InlineKeyboardButton(
                "📂 فتح",
                callback_data=f"open_{item_id}"
            )
        )

    markup.add(
        InlineKeyboardButton(
            "📄 عرض الملفات",
            callback_data=f"files_{item_id}"
        )
    )

    markup.add(
        InlineKeyboardButton(
            "🔙 رجوع",
            callback_data="back_0"
        )
    )

    return markup


# ============================================
# FILE ACTIONS
# ============================================

def file_keyboard(file_id):
    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton(
            "⬇️ تحميل / عرض",
            callback_data=f"showfile_{file_id}"
        )
    )

    markup.add(
        InlineKeyboardButton(
            "🔙 رجوع",
            callback_data="back_0"
        )
    )

    return markup


# ============================================
# CONFIRMATION KEYBOARD
# ============================================

def confirm_keyboard(action, target_id):
    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton(
            "✅ تأكيد",
            callback_data=f"confirm_{action}_{target_id}"
        ),
        InlineKeyboardButton(
            "❌ إلغاء",
            callback_data="cancel_action"
        )
    )

    return markup


# ============================================
# SIMPLE CANCEL
# ============================================

def cancel_keyboard():
    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton(
            "❌ إلغاء",
            callback_data="cancel_action"
        )
    )

    return markup

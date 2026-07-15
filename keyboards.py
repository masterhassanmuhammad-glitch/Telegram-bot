from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =================================
# القائمة الرئيسية للمستخدمين
# =================================

def main_menu():
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "📚 المحاضرات",
            callback_data="lectures"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "📄 الشيتات",
            callback_data="sheets"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🎥 الفيديوهات",
            callback_data="videos"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "📢 الإعلانات",
            callback_data="announcements"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "💬 تواصل مع الإدارة",
            callback_data="contact_admin"
        )
    )

    return keyboard



# =================================
# لوحة تحكم الأدمن
# =================================

def admin_menu():

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "👥 عدد المستخدمين",
            callback_data="users_count"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "📢 إرسال رسالة للجميع",
            callback_data="broadcast"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "📬 رسائل المستخدمين",
            callback_data="user_messages"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "➕ إضافة زر",
            callback_data="add_button"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "✏️ تعديل الأزرار",
            callback_data="edit_buttons"
        )
    )

    keyboard.add(
        InlineKeyboardButton(
            "🗑 حذف زر",
            callback_data="delete_button"
        )
    )

    return keyboard



# =================================
# زر الرجوع
# =================================

def back_button():

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "⬅️ رجوع",
            callback_data="back"
        )
    )

    return keyboard

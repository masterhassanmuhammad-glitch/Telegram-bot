from telebot.types import Message, CallbackQuery

from database import execute
from keyboards import cancel_keyboard


# ============================================
# GET USERS LIST (ADMIN FUNCTION)
# ============================================

def get_users(limit=50):
    return execute("""
        SELECT user_id, username, first_name, created_at, is_blocked
        FROM users
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,), fetch=True)


# ============================================
# COUNT USERS
# ============================================

def count_users():
    result = execute("""
        SELECT COUNT(*) as total FROM users
    """, fetchone=True)

    return result["total"] if result else 0


# ============================================
# BLOCK USER
# ============================================

def block_user(user_id):
    execute("""
        UPDATE users
        SET is_blocked = TRUE
        WHERE user_id = %s
    """, (user_id,))


# ============================================
# UNBLOCK USER
# ============================================

def unblock_user(user_id):
    execute("""
        UPDATE users
        SET is_blocked = FALSE
        WHERE user_id = %s
    """, (user_id,))


# ============================================
# GET SINGLE USER
# ============================================

def get_user(user_id):
    return execute("""
        SELECT * FROM users
        WHERE user_id = %s
    """, (user_id,), fetchone=True)


# ============================================
# REGISTER HANDLERS
# ============================================

def register_user_handlers(bot):

    # ========================================
    # SHOW USERS LIST
    # ========================================

    @bot.message_handler(commands=['users'])
    def show_users(message: Message):

        users = get_users()

        if not users:
            bot.send_message(message.chat.id, "❌ لا يوجد مستخدمين")
            return

        text = "👥 آخر المستخدمين:\n\n"

        for u in users:
            status = "🚫 محظور" if u["is_blocked"] else "✅ نشط"

            text += f"""
ID: {u['user_id']}
Name: {u['first_name'] or ''}
Username: @{u['username'] if u['username'] else '---'}
Status: {status}
----------------------
"""

        bot.send_message(message.chat.id, text, reply_markup=cancel_keyboard())


    # ========================================
    # GET USER DETAILS
    # ========================================

    @bot.message_handler(commands=['user'])
    def user_details(message: Message):

        try:
            user_id = int(message.text.split()[1])
        except:
            bot.reply_to(message, "❌ استخدم: /user <id>")
            return

        user = get_user(user_id)

        if not user:
            bot.reply_to(message, "❌ المستخدم غير موجود")
            return

        text = f"""
👤 User Info

ID: {user['user_id']}
Name: {user['first_name']}
Username: @{user['username']}
Phone: {user['phone']}
Created: {user['created_at']}
Status: {"🚫 محظور" if user['is_blocked'] else "✅ نشط"}
"""

        markup = cancel_keyboard()

        bot.send_message(message.chat.id, text, reply_markup=markup)


    # ========================================
    # BLOCK USER
    # ========================================

    @bot.message_handler(commands=['block'])
    def block(message: Message):

        try:
            user_id = int(message.text.split()[1])
        except:
            bot.reply_to(message, "❌ استخدم: /block <id>")
            return

        block_user(user_id)

        bot.send_message(message.chat.id, f"🚫 تم حظر {user_id}")


    # ========================================
    # UNBLOCK USER
    # ========================================

    @bot.message_handler(commands=['unblock'])
    def unblock(message: Message):

        try:
            user_id = int(message.text.split()[1])
        except:
            bot.reply_to(message, "❌ استخدم: /unblock <id>")
            return

        unblock_user(user_id)

        bot.send_message(message.chat.id, f"✅ تم إلغاء الحظر عن {user_id}")


    # ========================================
    # USER COUNT
    # ========================================

    @bot.message_handler(commands=['count'])
    def users_count(message: Message):

        total = count_users()

        bot.send_message(
            message.chat.id,
            f"👥 عدد المستخدمين: {total}"
        )

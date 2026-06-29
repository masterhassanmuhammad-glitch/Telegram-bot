import time
from telebot.types import Message

from database import execute
from users import get_users


# ============================================
# BROADCAST TEXT MESSAGE
# ============================================

def broadcast_text(bot, text):
    users = get_users(limit=10000)

    success = 0
    failed = 0

    for user in users:

        # تجاهل المحظورين
        if user.get("is_blocked"):
            continue

        try:
            bot.send_message(
                user["user_id"],
                text
            )
            success += 1

        except Exception:
            failed += 1

        time.sleep(0.05)  # حماية ضد Flood

    return success, failed


# ============================================
# BROADCAST PHOTO
# ============================================

def broadcast_photo(bot, file_id, caption=""):
    users = get_users(limit=10000)

    success = 0
    failed = 0

    for user in users:

        if user.get("is_blocked"):
            continue

        try:
            bot.send_photo(
                user["user_id"],
                file_id,
                caption=caption
            )
            success += 1

        except Exception:
            failed += 1

        time.sleep(0.05)

    return success, failed


# ============================================
# BROADCAST DOCUMENT
# ============================================

def broadcast_document(bot, file_id, caption=""):
    users = get_users(limit=10000)

    success = 0
    failed = 0

    for user in users:

        if user.get("is_blocked"):
            continue

        try:
            bot.send_document(
                user["user_id"],
                file_id,
                caption=caption
            )
            success += 1

        except Exception:
            failed += 1

        time.sleep(0.05)

    return success, failed


# ============================================
# ADMIN HANDLER FOR BROADCAST
# ============================================

def register_broadcast_handlers(bot):

    state = {}

    # ========================================
    # START BROADCAST
    # ========================================

    @bot.message_handler(commands=['broadcast'])
    def start_broadcast(message: Message):

        state[message.from_user.id] = "waiting_text"

        bot.send_message(
            message.chat.id,
            "📢 أرسل الرسالة التي تريد إرسالها للجميع:"
        )


    # ========================================
    # HANDLE BROADCAST TEXT
    # ========================================

    @bot.message_handler(func=lambda m: m.from_user.id in state)
    def handle_broadcast(message: Message):

        user_id = message.from_user.id
        mode = state.get(user_id)

        # ====================================
        # TEXT BROADCAST
        # ====================================

        if mode == "waiting_text":

            text = message.text

            bot.send_message(message.chat.id, "⏳ جاري الإرسال...")

            success, failed = broadcast_text(bot, text)

            bot.send_message(
                message.chat.id,
                f"""
📊 تم الإرسال:
✅ نجاح: {success}
❌ فشل: {failed}
"""
            )

            state.pop(user_id, None)

        # ====================================
        # PHOTO BROADCAST
        # ====================================

        elif mode == "waiting_photo":

            if not message.photo:
                bot.send_message(message.chat.id, "❌ أرسل صورة")
                return

            file_id = message.photo[-1].file_id

            bot.send_message(message.chat.id, "⏳ جاري الإرسال...")

            success, failed = broadcast_photo(bot, file_id)

            bot.send_message(
                message.chat.id,
                f"""
📊 تم الإرسال:
✅ نجاح: {success}
❌ فشل: {failed}
"""
            )

            state.pop(user_id, None)

        # ====================================
        # DOCUMENT BROADCAST
        # ====================================

        elif mode == "waiting_doc":

            if not message.document:
                bot.send_message(message.chat.id, "❌ أرسل ملف")
                return

            file_id = message.document.file_id

            bot.send_message(message.chat.id, "⏳ جاري الإرسال...")

            success, failed = broadcast_document(bot, file_id)

            bot.send_message(
                message.chat.id,
                f"""
📊 تم الإرسال:
✅ نجاح: {success}
❌ فشل: {failed}
"""
            )

            state.pop(user_id, None)

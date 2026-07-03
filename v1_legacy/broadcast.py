import time
import threading  # تم إضافة المكتبة لتشغيل البث في الخلفية
from telebot.types import Message

from database import execute
from users import get_users


# ============================================
# BACKGROUND WORKERS (الدوال التي تعمل في الخلفية)
# ============================================

def run_text_broadcast_task(bot, chat_id, text):
    users = get_users(limit=10000)
    success, failed = 0, 0

    for user in users:
        if user.get("is_blocked"):
            continue
        try:
            bot.send_message(user["user_id"], text)
            success += 1
        except Exception:
            failed += 1
        time.sleep(0.05)  # حماية ضد Flood

    # إرسال التقرير للأدمن بعد انتهاء الخلفية تماماً
    try:
        bot.send_message(chat_id, f"📊 **اكتمل بث الرسالة النصية:**\n\n✅ نجاح: {success}\n❌ فشل: {failed}", parse_mode="Markdown")
    except Exception:
        pass


def run_photo_broadcast_task(bot, chat_id, file_id, caption=""):
    users = get_users(limit=10000)
    success, failed = 0, 0

    for user in users:
        if user.get("is_blocked"):
            continue
        try:
            bot.send_photo(user["user_id"], file_id, caption=caption)
            success += 1
        except Exception:
            failed += 1
        time.sleep(0.05)

    try:
        bot.send_message(chat_id, f"📊 **اكتمل بث الصورة:**\n\n✅ نجاح: {success}\n❌ فشل: {failed}", parse_mode="Markdown")
    except Exception:
        pass


def run_document_broadcast_task(bot, chat_id, file_id, caption=""):
    users = get_users(limit=10000)
    success, failed = 0, 0

    for user in users:
        if user.get("is_blocked"):
            continue
        try:
            bot.send_document(user["user_id"], file_id, caption=caption)
            success += 1
        except Exception:
            failed += 1
        time.sleep(0.05)

    try:
        bot.send_message(chat_id, f"📊 **اكتمل بث الملف:**\n\n✅ نجاح: {success}\n❌ فشل: {failed}", parse_mode="Markdown")
    except Exception:
        pass


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
            "📢 أرسل الرسالة التي تريد إرسالها للجميع:\n*(يمكنك أيضاً إرسال صورة أو ملف وسيتعرف عليها البوت تلقائياً)*",
            parse_mode="Markdown"
        )

    # ========================================
    # HANDLE BROADCAST TEXT & MEDIA
    # ========================================

    @bot.message_handler(func=lambda m: m.from_user.id in state, content_types=['text', 'photo', 'document'])
    def handle_broadcast(message: Message):
        user_id = message.from_user.id
        
        # ذكاء اصطناعي مصغر: إذا غير الأدمن رأيه وأرسل صورة أو ملف بدلاً من النص، نقوم بتعديل الحالة تلقائياً
        if message.photo:
            mode = "waiting_photo"
        elif message.document:
            mode = "waiting_doc"
        else:
            mode = "waiting_text"

        # ====================================
        # TEXT BROADCAST
        # ====================================
        if mode == "waiting_text":
            text = message.text
            if text == "/cancel" or text == "إلغاء":
                state.pop(user_id, None)
                bot.send_message(message.chat.id, "❌ تم إلغاء عملية البث.")
                return

            bot.send_message(message.chat.id, "⏳ جاري بدء الإرسال في الخلفية... يمكنك استخدام البوت الآن بشكل طبيعي وسأخبرك بالنتيجة عند الاكتمال.")
            
            # تشغيل العملية في خيط منفصل (Background Thread)
            threading.Thread(target=run_text_broadcast_task, args=(bot, message.chat.id, text)).start()
            state.pop(user_id, None)

        # ====================================
        # PHOTO BROADCAST
        # ====================================
        elif mode == "waiting_photo":
            file_id = message.photo[-1].file_id
            caption = message.caption if message.caption else ""

            bot.send_message(message.chat.id, "⏳ جاري بدء بث الصورة في الخلفية... يمكنك استخدام البوت بشكل طبيعي الآن.")
            
            # تشغيل في الخلفية
            threading.Thread(target=run_photo_broadcast_task, args=(bot, message.chat.id, file_id, caption)).start()
            state.pop(user_id, None)

        # ====================================
        # DOCUMENT BROADCAST
        # ====================================
        elif mode == "waiting_doc":
            file_id = message.document.file_id
            caption = message.caption if message.caption else ""

            bot.send_message(message.chat.id, "⏳ jاري بدء بث الملف في الخلفية... يمكنك استخدام البوت بشكل طبيعي الآن.")
            
            # تشغيل في الخلفية
            threading.Thread(target=run_document_broadcast_task, args=(bot, message.chat.id, file_id, caption)).start()
            state.pop(user_id, None)
            

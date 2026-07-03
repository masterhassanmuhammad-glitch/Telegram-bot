from telebot.types import Message, CallbackQuery

from database import execute
from config import OWNER_ID


# ============================================
# STATE SYSTEM
# ============================================

consult_state = {}


# ============================================
# REGISTER CONSULTATION HANDLERS
# ============================================

def register_consultation_handlers(bot):

    # ========================================
    # USER SEND QUESTION
    # ========================================

    @bot.message_handler(commands=['ask'])
    def ask_start(message: Message):

        consult_state[message.from_user.id] = "waiting_question"

        bot.send_message(
            message.chat.id,
            "🩺 اكتب سؤالك الطبي وسيتم الرد عليك قريبًا:"
        )


    # ========================================
    # HANDLE USER QUESTION
    # ========================================

    @bot.message_handler(func=lambda m: m.from_user.id in consult_state)
    def handle_consultation(message: Message):

        user_id = message.from_user.id
        state = consult_state.get(user_id)

        if state != "waiting_question":
            return

        question = message.text

        # حفظ السؤال في قاعدة البيانات
        execute("""
            INSERT INTO messages(user_id, username, message_text, status)
            VALUES(%s, %s, %s, 0)
        """, (
            user_id,
            message.from_user.username,
            question
        ))

        # إرسال للأدمن
        bot.send_message(
            OWNER_ID,
            f"""
🩺 استشارة جديدة:

👤 User ID: {user_id}
📩 السؤال:
{question}

💬 للرد استخدم:
/reply {user_id} <ردك>
"""
        )

        bot.send_message(
            message.chat.id,
            "✅ تم إرسال سؤالك، سيتم الرد قريبًا."
        )

        consult_state.pop(user_id, None)


    # ============================================
    # ADMIN REPLY
    # ============================================

    @bot.message_handler(commands=['reply'])
    def reply_to_user(message: Message):

        if message.from_user.id != OWNER_ID:
            return

        try:
            parts = message.text.split(" ", 2)
            user_id = int(parts[1])
            answer = parts[2]
        except:
            bot.reply_to(message, "❌ استخدم: /reply <user_id> <answer>")
            return

        # إرسال الرد للمستخدم
        try:
            bot.send_message(
                user_id,
                f"🩺 رد الطبيب:\n\n{answer}"
            )
        except:
            bot.reply_to(message, "❌ لا يمكن إرسال الرسالة")

        # تحديث الحالة في DB
        execute("""
            UPDATE messages
            SET status = 1
            WHERE user_id = %s AND status = 0
        """, (user_id,))

        bot.send_message(message.chat.id, "✅ تم إرسال الرد")

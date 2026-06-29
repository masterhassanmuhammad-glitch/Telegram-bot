from telebot.types import Message, CallbackQuery
import logging

from database import execute
from keyboards import cancel_keyboard


# ============================================
# STATE SYSTEM (SIMPLE IN MEMORY)
# ============================================

file_state = {}


# ============================================
# ADD FILE TO ITEM (START)
# ============================================

def register_file_handlers(bot):

    @bot.callback_query_handler(func=lambda call: call.data == "admin_add_file")
    def add_file_start(call: CallbackQuery):
        
        # 🛠️ الحل هنا: إخطار تليجرام فوراً باستلام الضغطة لإيقاف التحميل والتعليق
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logging.error(f"Error answering callback: {e}")

        file_state[call.from_user.id] = {
            "step": "choose_item"
        }

        bot.send_message(
            call.message.chat.id,
            "📂 أرسل ID القسم الذي تريد إضافة ملف له:"
        )


    # ========================================
    # HANDLE FILE FLOW
    # ========================================

    @bot.message_handler(func=lambda m: m.from_user.id in file_state)
    def handle_file_flow(message: Message):

        user_id = message.from_user.id
        state = file_state.get(user_id)

        if not state:
            return

        # ====================================
        # STEP 1: CHOOSE ITEM ID
        # ====================================

        if state["step"] == "choose_item":

            try:
                item_id = int(message.text)
            except:
                bot.send_message(message.chat.id, "❌ أرسل رقم صحيح")
                return

            state["item_id"] = item_id
            state["step"] = "wait_file"

            bot.send_message(
                message.chat.id,
                "📤 الآن أرسل الملف (PDF / صورة / مستند):"
            )


        # ====================================
        # STEP 2: RECEIVE FILE
        # ====================================

        elif state["step"] == "wait_file":

            file_id = None
            file_type = None
            caption = message.caption or ""

            # PHOTO
            if message.photo:
                file_id = message.photo[-1].file_id
                file_type = "photo"

            # DOCUMENT
            elif message.document:
                file_id = message.document.file_id
                file_type = "document"

            # VIDEO (optional)
            elif message.video:
                file_id = message.video.file_id
                file_type = "video"

            else:
                bot.send_message(message.chat.id, "❌ أرسل ملف صحيح")
                return

            # حفظ في قاعدة البيانات
            execute("""
                INSERT INTO file_attachments(item_id, file_id, file_type, caption)
                VALUES(%s, %s, %s, %s)
            """, (
                state["item_id"],
                file_id,
                file_type,
                caption
            ))

            bot.send_message(
                message.chat.id,
                "✅ تم رفع الملف بنجاح",
                reply_markup=cancel_keyboard()
            )

            file_state.pop(user_id, None)


    # ============================================
    # LIST FILES BY ITEM
    # ============================================

    @bot.message_handler(commands=['files'])
    def list_files(message: Message):

        try:
            item_id = int(message.text.split()[1])
        except:
            bot.send_message(message.chat.id, "❌ استخدم: /files <item_id>")
            return

        files = execute("""
            SELECT id, file_id, file_type, caption
            FROM file_attachments
            WHERE item_id=%s
        """, (item_id,), fetch=True)

        if not files:
            bot.send_message(message.chat.id, "❌ لا توجد ملفات")
            return

        text = f"📂 ملفات القسم {item_id}:\n\n"

        for f in files:
            text += f"ID: {f['id']} | Type: {f['file_type']}\n"

        bot.send_message(message.chat.id, text)


    # ============================================
    # DELETE FILE
    # ============================================

    @bot.message_handler(commands=['deletefile'])
    def delete_file(message: Message):

        try:
            file_id = int(message.text.split()[1])
        except:
            bot.send_message(message.chat.id, "❌ استخدم: /deletefile <file_id>")
            return

        execute("""
            DELETE FROM file_attachments
            WHERE id=%s
        """, (file_id,))

        bot.send_message(message.chat.id, f"🗑 تم حذف الملف {file_id}")

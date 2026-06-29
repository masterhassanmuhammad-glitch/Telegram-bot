from telebot.types import Message, CallbackQuery
import logging

from database import execute
from keyboards import (
    main_menu_keyboard,
    back_keyboard,
    item_actions_keyboard,
    file_keyboard
)

def register_handlers(bot):

    # ============================================
    # 🚨 رادار كشف الأزرار (يصطاد أي ضغطة ويطبعها إجبارياً)
    # ============================================
    @bot.callback_query_handler(func=lambda call: True)
    def radar_test(call: CallbackQuery):
        # طباعة إجبارية تظهر في لوج Render فوراً مهما كانت الإعدادات
        print(f"🚨 [الرادار] تم ضغط زر! البيانات المخفية داخله هي: {call.data}", flush=True)
        
        # إظهار نافذة منبثقة على هاتف المستخدم تخبره بالقيمة
        try:
            bot.answer_callback_query(
                call.id, 
                text=f"📊 رادار الأزرار:\nالبيانات المستلمة: {call.data}", 
                show_alert=True
            )
        except Exception as e:
            print(f"❌ خطأ أثناء الرد بالرادار: {e}", flush=True)


    # ============================================
    # START MENU
    # ============================================
    @bot.message_handler(commands=['start'])
    def start(message: Message):
        user = message.from_user

        # حفظ المستخدم
        execute("""
        INSERT INTO users(user_id, username, first_name)
        VALUES(%s, %s, %s)
        ON CONFLICT(user_id) DO NOTHING
        """, (user.id, user.username, user.first_name))

        # جلب العناصر الرئيسية
        items = execute("""
        SELECT id, title FROM menu_items
        WHERE parent_id = 0
        ORDER BY sort_order
        """, fetch=True)

        text = "🏥 مرحباً بك في MedicalBot\nاختر القسم:"

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_menu_keyboard(items or [])
        )


    # ============================================
    # OPEN MENU ITEM
    # ============================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_"))
    def open_item(call: CallbackQuery):
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logging.error(f"Error answering callback: {e}")

        item_id = int(call.data.split("_")[1])

        item = execute("""
        SELECT id, title, description FROM menu_items
        WHERE id=%s
        """, (item_id,), fetchone=True)

        if not item:
            return

        children = execute("""
        SELECT id, title FROM menu_items
        WHERE parent_id=%s
        ORDER BY sort_order
        """, (item_id,), fetch=True)

        text = f"📂 {item['title']}\n\n{item['description'] or ''}"

        markup = main_menu_keyboard(children or [])
        markup.add(back_keyboard(0).keyboard[0])

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )


    # ============================================
    # BACK NAVIGATION
    # ============================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_"))
    def go_back(call: CallbackQuery):
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logging.error(f"Error answering callback: {e}")

        parent_id = int(call.data.split("_")[1])

        if parent_id == 0:
            items = execute("""
            SELECT id, title FROM menu_items
            WHERE parent_id=0
            ORDER BY sort_order
            """, fetch=True)

            bot.edit_message_text(
                "🏥 اختر القسم:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=main_menu_keyboard(items or [])
            )
            return

        parent = execute("""
        SELECT id, title, description FROM menu_items
        WHERE id=%s
        """, (parent_id,), fetchone=True)

        children = execute("""
        SELECT id, title FROM menu_items
        WHERE parent_id=%s
        ORDER BY sort_order
        """, (parent_id,), fetch=True)

        text = f"📂 {parent['title']}\n\n{parent['description'] or ''}"

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu_keyboard(children or [])
        )


    # ============================================
    # SHOW FILES INSIDE ITEM
    # ============================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("files_"))
    def show_files(call: CallbackQuery):
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logging.error(f"Error answering callback: {e}")

        item_id = int(call.data.split("_")[1])

        files = execute("""
        SELECT id, file_id, caption FROM file_attachments
        WHERE item_id=%s
        """, (item_id,), fetch=True)

        if not files:
            bot.send_message(call.message.chat.id, "❌ لا توجد ملفات في هذا القسم حالياً.")
            return

        for f in files:
            bot.send_document(
                call.message.chat.id,
                f["file_id"],
                caption=f["caption"] or "",
                reply_markup=file_keyboard(f["id"])
            )


    # ============================================
    # SHOW SINGLE FILE
    # ============================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("showfile_"))
    def show_file(call: CallbackQuery):
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logging.error(f"Error answering callback: {e}")

        file_id = int(call.data.split("_")[1])

        file = execute("""
        SELECT file_id, caption FROM file_attachments
        WHERE id=%s
        """, (file_id,), fetchone=True)

        if not file:
            return

        bot.send_document(
            call.message.chat.id,
            file["file_id"],
            caption=file["caption"] or ""
        )


    # ============================================
    # CANCEL ACTION
    # ============================================
    @bot.callback_query_handler(func=lambda call: call.data == "cancel_action")
    def cancel(call: CallbackQuery):
        try:
            bot.answer_callback_query(call.id, "تم الإلغاء")
        except Exception as e:
            logging.error(f"Error answering callback: {e}")
            

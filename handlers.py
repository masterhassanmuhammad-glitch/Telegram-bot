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
    # 🚨 رادار كشف الأزرار (ضعه في البداية تماماً ليمسك الضغطة أولاً)
    # ============================================
    @bot.callback_query_handler(func=lambda call: True)
    def radar_test(call: CallbackQuery):
        # طباعة إجبارية تظهر في لوج Render فوراً
        print(f"🚨 [الرادار] تم ضغط زر! البيانات المخفية داخله هي: {call.data}", flush=True)
        
        # إظهار نافذة منبثقة على هاتف المستخدم تخبره بالقيمة
        bot.answer_callback_query(
            call.id, 
            text=f"📊 رادار الأزرار:\nالبيانات المستلمة: {call.data}", 
            show_alert=True
        )


    # ============================================
    # START MENU
    # ============================================
    @bot.message_handler(commands=['start'])
    def start(message: Message):
        # بقية كود الـ start الحالي دون تغيير...
        
from telebot.types import Message, CallbackQuery
import logging

from database import execute
from keyboards import (
    main_menu_keyboard,
    back_keyboard,
    item_actions_keyboard,
    file_keyboard
)

# ============================================
# START MENU
# ============================================

def register_handlers(bot):

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
    # OPEN MENU ITEM (نسخة التتبع العميق)
    # ============================================

    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_"))
    def open_item(call: CallbackQuery):
        logging.info(f"🔮 [تتبع] 1. تم استقبال ضغطة الزر بنجاح البيانات: {call.data}")
        
        try:
            bot.answer_callback_query(call.id)
            logging.info("✅ [تتبع] 2. تم إرسال أمر إلغاء تعليق الساعة إلى تليجرام")
        except Exception as e:
            logging.error(f"❌ [تتبع] خطأ في إلغاء التعليق: {e}")

        logging.info("⏳ [تتبع] 3. جاري محاولة الاتصال بقاعدة البيانات لجلب القسم...")
        try:
            item_id = int(call.data.split("_")[1])
            item = execute("""
            SELECT id, title, description FROM menu_items
            WHERE id=%s
            """, (item_id,), fetchone=True)
            logging.info(f"✅ [تتبع] 4. اكتمل استعلام قاعدة البيانات بنجاح. النتيجة: {item}")
        except Exception as e:
            logging.error(f"❌ [تتبع] انهيار في قاعدة البيانات عند خطوة 4: {e}")
            return

        if not item:
            logging.warning("⚠️ [تتبع] تنبيه: هذا القسم غير موجود في الجداول")
            return

        logging.info("⏳ [تتبع] 5. جاري جلب العناصر الفرعية للقسم...")
        try:
            children = execute("""
            SELECT id, title FROM menu_items
            WHERE parent_id=%s
            ORDER BY sort_order
            """, (item_id,), fetch=True)
            logging.info(f"✅ [تتبع] 6. تم جلب العناصر الفرعية بنجاح. العدد: {len(children or [])}")
        except Exception as e:
            logging.error(f"❌ [تتبع] خطأ في جلب العناصر الفرعية: {e}")
            return

        logging.info("⏳ [تتبع] 7. جاري محاولة تعديل رسالة تليجرام وإرسال الأزرار الجديدة...")
        try:
            text = f"📂 {item['title']}\n\n{item['description'] or ''}"
            markup = main_menu_keyboard(children or [])
            markup.add(back_keyboard(0).keyboard[0])

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
            logging.info("🎉 [تتبع] 8. مبروك! تم تحديث واجهة البوت بالكامل بدون مشاكل.")
        except Exception as e:
            logging.error(f"❌ [تتبع] خطأ أثناء تعديل الرسالة في تليجرام: {e}")
            

    # ============================================
    # BACK NAVIGATION
    # ============================================

    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_"))
    def go_back(call: CallbackQuery):
        
        # 🛠️ حل التعليق: إلغاء تحميل زر العودة فوراً
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
        
        # 🛠️ حل التعليق: إيقاف التحميل فوراً قبل البدء في إرسال المستندات (لتجنب تعليق الزر أثناء الرفع)
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
        
        # 🛠️ حل التعليق: إيقاف تحميل زر عرض الملف الفردي
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

                # ============================================
    # 🕵️‍♂️ كاشف الأزرار العمومي (ضعه في آخر ملف handlers.py)
    # ============================================
    @bot.callback_query_handler(func=lambda call: True)
    def catch_all_callbacks(call: CallbackQuery):
        # هذا السطر سيجبر التليجرام على إظهار نافذة منبثقة تخبرنا ماذا يرسل الزر بالظبط
        bot.answer_callback_query(
            call.id, 
            text=f"⚠️ زر غير مـُعرّف في الكود!\nالبيانات المرسلة: {call.data}", 
            show_alert=True
        )
        logging.warning(f"Unmatched callback data received: {call.data}")
        

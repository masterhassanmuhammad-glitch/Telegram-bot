from telebot import types
from .helpers import (
    active_menus,
    send_files_and_recreate_menu,
    is_user_in_batch,
    send_join_request_menu,
    get_permissions,
    check_state
)

from config import bot, OWNER_ID, ADMIN_IDS
from database import execute_query, set_user_state, clear_user_state
from keyboards import make_main_menu_markup, make_sub_menu_markup

def register_user_handlers():

    # 1. أمر البدء (المدخل الرئيسي)
    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        username = message.from_user.username or "NoUsername"
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""

        # تسجيل المستخدم في قاعدة البيانات مع حفظ الأسماء
        execute_query(
            """
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET 
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name;
            """,
            (user_id, username, first_name, last_name),
            commit=True
        )

        clear_user_state(user_id)

        # أ. التحقق من المجموعة
        if not is_user_in_batch(bot, user_id):
            send_join_request_menu(bot, chat_id)
            return

        # ب. التحقق من رقم الهاتف
        res = execute_query("SELECT phone_number FROM users WHERE user_id = %s;", (user_id,), fetch=True)
        has_phone = bool(res and res[0][0])

        if not has_phone:
            ask_for_phone(chat_id, user_id)
            return

        # ج. إذا كان كل شيء تمام، عرض القائمة الرئيسية
        show_main_menu(chat_id, user_id)

    # 2. وظيفة طلب رقم الهاتف
    def ask_for_phone(chat_id, user_id):
        set_user_state(user_id, "WAITING_PHONE")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📱 مشاركة رقم الهاتف", request_contact=True))
        
        bot.send_message(
            chat_id,
            "⚠️ أهلاً بك يا دكتور! لاستكمال استخدام البوت، يرجى مشاركة رقم هاتفك بالضغط على الزر أدناه 👇",
            reply_markup=markup
        )

    # 3. معالجة إرسال الرقم
    @bot.message_handler(func=check_state("WAITING_PHONE"), content_types=['contact'])
    def process_phone_number(message):
        user_id = message.from_user.id
        phone_number = message.contact.phone_number
        
        execute_query("UPDATE users SET phone_number = %s WHERE user_id = %s;", (phone_number, user_id), commit=True)
        clear_user_state(user_id)
        
        bot.send_message(message.chat.id, "✅ تم تسجيل رقمك بنجاح. شكراً لك!", reply_markup=types.ReplyKeyboardRemove())
        show_main_menu(message.chat.id, user_id)

    # 4. زر التحقق من العضوية
    @bot.callback_query_handler(func=lambda call: call.data == "check_membership")
    def handle_check_membership(call):
        user_id = call.from_user.id
        if is_user_in_batch(bot, user_id):
            bot.answer_callback_query(call.id, "✅ تم التحقق من عضويتك!", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            # الانتقال لخطوة الهاتف أو القائمة
            res = execute_query("SELECT phone_number FROM users WHERE user_id = %s;", (user_id,), fetch=True)
            if not (res and res[0][0]):
                ask_for_phone(call.message.chat.id, user_id)
            else:
                show_main_menu(call.message.chat.id, user_id)
        else:
            bot.answer_callback_query(call.id, "عذراً، أنت لست عضواً في كلية الطب من الدفعتين 35&36", show_alert=True)

    # 5. عرض القائمة الرئيسية (دالة مساعدة)
    def show_main_menu(chat_id, user_id):
        perms = get_permissions(user_id)
        text = "👋 أهلاً بك في البوت الطبي التعليمي.\n\nالرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات الطبية 👇"
        sent_menu = bot.send_message(chat_id, text, reply_markup=make_main_menu_markup(perms, user_id))
        active_menus[chat_id] = sent_menu.message_id

    # 6. الروتينات الأخرى (القائمة، فتح المجلدات، المراسلة)
    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    def cb_main_menu(call):
        show_main_menu(call.message.chat.id, call.from_user.id)
        bot.answer_callback_query(call.id)

        # دالة فتح المجلد وإرسال الملفات (نسخة آمنة ومحمية من التعليق)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_"))
    def cb_open_folder(call):
        # 1. الاستجابة الفورية للتليجرام لإنهاء عجلة التحميل ومنع تعليق الزر نهائياً مهما حدث
        bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        parts = call.data.split("_")
        btn_id = int(parts[1])
        
        try:
                # دالة فتح المجلد وإرسال الملفات (النسخة المصححة لجدول button_files)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_"))
    def cb_open_folder(call):
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        parts = call.data.split("_")
        btn_id = int(parts[1])
        
        try:
            btn_info = execute_query("SELECT name, message_text FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
            if not btn_info: 
                bot.send_message(call.message.chat.id, "⚠️ عذراً، هذا القسم غير موجود أو تم حذفه مسبقاً.")
                return
            btn_name, msg_text = btn_info[0]
            
            # التعديل هنا: العودة لاسم الجدول الصحيح button_files مع الترتيب
            files_data = execute_query("SELECT file_id, file_type, NULL FROM button_files WHERE button_id = %s ORDER BY id ASC;", (btn_id,), fetch=True)
            
            perms = get_permissions(user_id)
            
            send_files_and_recreate_menu(
                bot, 
                call.message.chat.id, 
                files_data, 
                f"📂 {btn_name}\n\n{msg_text or ''}", 
                make_sub_menu_markup(btn_id, perms["is_admin"])
            )
            
        except Exception as e:
            print(f"❌ خطأ برمجي داخل دالة cb_open_folder: {e}")
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ داخلي في الكود:\n\n`{str(e)}`")
            
            
    @bot.callback_query_handler(func=lambda call: call.data == "user_contact")
    def cb_user_contact(call):
        set_user_state(call.from_user.id, "WAITING_FEEDBACK_MSG")
        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="📝 اكتب استفسارك هنا:")
        bot.answer_callback_query(call.id)

    # 7. معالجة الرسالة مع تفاصيل الطالب
    @bot.message_handler(func=check_state("WAITING_FEEDBACK_MSG"), content_types=["text"])
    def handle_feedback(message):
        user_id = message.from_user.id
        user_text = message.text
        
        # حفظ الرسالة في قاعدة البيانات
        execute_query("INSERT INTO feedback (user_id, username, message_text) VALUES (%s, %s, %s);", 
                      (user_id, message.from_user.username or "N/A", user_text), commit=True)
        
        # جلب بيانات الطالب كاملة من قاعدة البيانات
        user_info = execute_query("SELECT first_name, last_name, phone_number FROM users WHERE user_id = %s;", 
                                  (user_id,), fetch=True)
        
        f_name, l_name, phone = ("", "", "غير مسجل")
        if user_info:
            f_name, l_name, phone = user_info[0]

        # صياغة رسالة الإدارة
        admin_notification = (
            f"📬 رسالة جديدة من المستخدم:\n\n"
            f"👤 الاسم: {f_name} {l_name}\n"
            f"🆔 ID: {user_id}\n"
            f"📱 الهاتف: {phone}\n"
            f"🔗 المعرف: @{message.from_user.username or 'لا يوجد'}\n\n"
            f"📄 المحتوى:\n{user_text}"
        )

        # إرسال للإدارة
        notify_ids = {OWNER_ID} if OWNER_ID else set()
        db_admins = execute_query("SELECT admin_id FROM admins WHERE can_feedback = TRUE;", fetch=True)
        for (adm_id,) in db_admins: notify_ids.add(adm_id)
        for static_adm in ADMIN_IDS: notify_ids.add(static_adm)

        for admin_id in notify_ids:
            try: bot.send_message(admin_id, admin_notification)
            except: pass

        clear_user_state(user_id)
        bot.send_message(user_id, "✅ تم إرسال رسالتك للمشرفين بنجاح!")
        show_main_menu(message.chat.id, user_id)
        

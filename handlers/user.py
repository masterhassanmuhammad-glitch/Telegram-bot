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

PAGE_SIZE = 10  # عدد الملفات في كل صفحة

# 📑 الدالة المساعدة لتقسيم الملفات إلى صفحات
def send_button_files_page(chat_id, button_id, page=1):
    offset = (page - 1) * PAGE_SIZE
    
    # 1. جلب إجمالي عدد الملفات المرتبطة بهذا الزر
    count_res = execute_query("SELECT COUNT(*) FROM button_files WHERE button_id = %s;", (button_id,), fetch=True)
    total_files = count_res[0][0] if count_res else 0
    
    # إذا لم تكن هناك ملفات، نخرج فوراً دون إرسال أي شيء
    if total_files == 0:
        return
        
    # حساب إجمالي عدد الصفحات
    total_pages = (total_files + PAGE_SIZE - 1) // PAGE_SIZE
    
    # 2. جلب ملفات الصفحة الحالية فقط باستخدام LIMIT و OFFSET
    files = execute_query(
        "SELECT file_id, file_type FROM button_files WHERE button_id = %s ORDER BY id ASC LIMIT %s OFFSET %s;",
        (button_id, PAGE_SIZE, offset), fetch=True
    )
    
    # 3. إرسال الملفات العشرة الحالية للطالب
    for file_id, file_type in files:
        try:
            if file_type == 'document':
                bot.send_document(chat_id, file_id)
            elif file_type == 'photo':
                bot.send_photo(chat_id, file_id)
            elif file_type == 'audio':
                bot.send_audio(chat_id, file_id)
            elif file_type == 'video':
                bot.send_video(chat_id, file_id)
            elif file_type == 'voice':
                bot.send_voice(chat_id, file_id)
        except Exception as e:
            print(f"Error sending file {file_id}: {str(e)}")
            
    # 4. بناء كيبورد التنقل بين الصفحات (التالي والسابق)
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup()
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"files_{button_id}_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"files_{button_id}_{page+1}"))
        
    if nav_buttons:
        markup.row(*nav_buttons)
        
    # زر إضافي للعودة لتحديث محتوى القسم أو القائمة
    markup.add(InlineKeyboardButton(text="🔄 تحديث هذا القسم", callback_data=f"open_{button_id}"))
    
    # إرسال رسالة التحكم بالصفحات أسفل الملفات المرسلة
    bot.send_message(
        chat_id,
        f"📑 مجموعة الملفات الحالية: [ {page} من {total_pages} ]\n📦 إجمالي الملفات في هذا القسم: {total_files} ملف.",
        reply_markup=markup
    )


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

    # 3. معالجة إرسال الرقم (النسخة المؤمنة والمصححة)
    @bot.message_handler(func=check_state("WAITING_PHONE"), content_types=['contact'])
    def process_phone_number(message):
        user_id = message.from_user.id
        
        # 🛡️ التحقق من أن الرقم المرسل يخص الطالب نفسه لمنع انتحال الهويات
        if message.contact.user_id != user_id:
            bot.reply_to(
                message,
                "❌ يرجى مشاركة رقم هاتفك الشخصي فقط."
            )
            return
            
        phone_number = message.contact.phone_number
        
        execute_query("UPDATE users SET phone_number = %s WHERE user_id = %s;", (phone_number, user_id), commit=True)
        clear_user_state(user_id)
        
        # ✅ تم التعديل هنا إلى ReplyKeyboardRemove لإزالة أزرار مشاركة الرقم بدون مشاكل
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

        # 📁 دالة فتح المجلد المعدلة والمصححة بالكامل مع زر العودة الديناميكي
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_"))
    def cb_open_folder(call):
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        parts = call.data.split("_")
        btn_id = int(parts[1])
    
        try:
            # 1. جلب معلومات المجلد/الزر ومعه الـ parent_id من قاعدة البيانات
            btn_info = execute_query("SELECT name, message_text, parent_id FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
            if not btn_info: 
                bot.send_message(call.message.chat.id, "⚠️ عذراً، هذا القسم غير موجود أو تم حذفه مسبقاً.")
                return
                
            btn_name, msg_text, parent_id = btn_info[0]
            perms = get_permissions(user_id)
            
            # 2. توليد الكيبورد الفرعي الحالي من ملف الـ keyboards
            markup = make_sub_menu_markup(btn_id, perms["is_admin"])
            
            # 🔙 [إضافة زر العودة]: تحديد وجهة الرجوع تلقائياً
            if parent_id:
                back_callback = f"open_{parent_id}"  # يعود للقسم الأب الأعلى منه
            else:
                back_callback = "main_menu"          # إذا كان قسماً رئيسياً يعود للمنيو الرئيسي
                
            # إضافة زر الرجوع في سطر منفصل أسفل أزرار القسم
            markup.add(types.InlineKeyboardButton(text="🔙 عودة للقسم السابق", callback_data=back_callback))
            
            # 3. تحديث نص الرسالة الحالية وعرض القائمة والأزرار الفرعية مع زر العودة
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"📂 {btn_name}\n\n{msg_text or ''}",
                reply_markup=markup
            )
            
            # 4. استدعاء الدالة المساعدة لتبدأ تلقائياً بإرسال أول 10 ملفات فقط (الصفحة رقم 1)
            send_button_files_page(call.message.chat.id, btn_id, page=1)
            
        except Exception as e:
            print(f"❌ خطأ برمجي داخل دالة cb_open_folder: {e}")
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ داخلي في الكود:\n\n`{str(e)}`")
            

    # 🔄 معالج أزرار التنقل (التالي / السابق) لإدارة الصفحات
    @bot.callback_query_handler(func=lambda call: call.data.startswith("files_"))
    def cb_files_pagination(call):
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        parts = call.data.split("_")
        btn_id = int(parts[1])
        page = int(parts[2])
        
        # حذف رسالة التحكم بالصفحة السابقة لتبقى المحادثة نظيفة ومنظمة
        try:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        except Exception:
            pass
            
        # استدعاء الصفحة الجديدة المطلوبة من الملفات
        send_button_files_page(call.message.chat.id, btn_id, page=page)
        
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
    

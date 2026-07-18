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

# 🔄 قاموس لتتبع رسائل التحكم بالصفحات وحذفها عند التنقل بين الأقسام
active_pagination = {}

# 📑 الدالة المساعدة لتقسيم الملفات إلى صفحات (تعيد True إذا أرسلت ملفات و False إذا كانت فارغة)
def send_button_files_page(chat_id, button_id, page=1):
    offset = (page - 1) * PAGE_SIZE
    
    # 1. جلب إجمالي عدد الملفات المرتبطة بهذا الزر
    count_res = execute_query("SELECT COUNT(*) FROM button_files WHERE button_id = %s;", (button_id,), fetch=True)
    total_files = count_res[0][0] if count_res else 0
    
    if total_files == 0:
        return False
        
    # حساب إجمالي عدد الصفحات
    total_pages = (total_files + PAGE_SIZE - 1) // PAGE_SIZE
    
    # 2. جلب ملفات الصفحة الحالية فقط
    files = execute_query(
        "SELECT file_id, file_type FROM button_files WHERE button_id = %s ORDER BY id ASC LIMIT %s OFFSET %s;",
        (button_id, PAGE_SIZE, offset), fetch=True
    )
    
    # 3. إرسال الملفات للطالب
    for file_id, file_type in files:
        try:
            if file_type == 'document': bot.send_document(chat_id, file_id)
            elif file_type == 'photo': bot.send_photo(chat_id, file_id)
            elif file_type == 'audio': bot.send_audio(chat_id, file_id)
            elif file_type == 'video': bot.send_video(chat_id, file_id)
            elif file_type == 'voice': bot.send_voice(chat_id, file_id)
        except Exception as e:
            print(f"Error sending file {file_id}: {str(e)}")
            
    # 4. بناء كيبورد التحكم (التالي + العودة الذكية للقسم السابق)
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup()
    
    # زر التالي (يظهر فقط إذا كان هناك صفحات قادمة)
    if page < total_pages:
        markup.row(InlineKeyboardButton(text="التالي ▶️", callback_data=f"files_{button_id}_{page+1}"))
        
    # جلب الـ parent_id للقسم الحالي
    parent_res = execute_query("SELECT parent_id FROM buttons WHERE id = %s;", (button_id,), fetch=True)
    parent_id = parent_res[0][0] if parent_res else None
    
    # [تعديل حسن]: التحقق الدقيق باستخدام is not None لتفادي مشكلة القيمة صفر أو NULL
    back_callback = f"back_{parent_id}" if parent_id is not None else "main_menu"
    
    markup.add(InlineKeyboardButton(text="🔙 العودة للقسم السابق", callback_data=back_callback))
    
    # إرسال رسالة التحكم بالصفحات
    sent_pag = bot.send_message(
        chat_id,
        f"📑 مجموعة الملفات الحالية: [ {page} من {total_pages} ]\n📦 إجمالي الملفات في هذا القسم: {total_files} ملف.",
        reply_markup=markup
    )
    active_pagination[chat_id] = sent_pag.message_id
    return True


def register_user_handlers():

# 1. أمر البدء (المدخل الرئيسي)
@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

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

    # الفلترة الأولية لمنع غير الأعضاء من المرور لخطوة طلب الهاتف
    if not is_user_in_batch(bot, user_id):
        send_join_request_menu(bot, chat_id)
        return

    res = execute_query("SELECT phone_number FROM users WHERE user_id = %s;", (user_id,), fetch=True)
    has_phone = bool(res and res[0][0])

    if not has_phone:
        ask_for_phone(chat_id, user_id)
        return

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
    if message.contact.user_id != user_id:
        bot.reply_to(message, "❌ يرجى مشاركة رقم هاتفك الشخصي فقط.")
        return
        
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
        res = execute_query("SELECT phone_number FROM users WHERE user_id = %s;", (user_id,), fetch=True)
        if not (res and res[0][0]):
            ask_for_phone(call.message.chat.id, user_id)
        else:
            show_main_menu(call.message.chat.id, user_id)
    else:
        bot.answer_callback_query(call.id, "عذراً، أنت لست عضواً في كلية الطب من الدفعتين 35&36", show_alert=True)

# 5. عرض القائمة الرئيسية (الحارس المركزي للمنيو)
def show_main_menu(chat_id, user_id):
    # 🔒 صمام أمان مركزي: إذا استطاع أي مستخدم الوصول لهذه الدالة بطريقة ملتوية وهو ليس في الدفعة، سيتم طرده فوراً لشاشة الاشتراك
    if not is_user_in_batch(bot, user_id):
        send_join_request_menu(bot, chat_id)
        return

    perms = get_permissions(user_id)
    text = "👋 أهلاً بك في البوت الطبي التعليمي.\n\nالرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات الطبية 👇"
    sent_menu = bot.send_message(chat_id, text, reply_markup=make_main_menu_markup(perms, user_id))
    active_menus[chat_id] = sent_menu.message_id

# 6. العودة للمنيو الرئيسي (أصبحت آمنة تماماً الآن بفضل الحماية المركزية)
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def cb_main_menu(call):
    chat_id = call.message.chat.id
    if chat_id in active_pagination:
        try:
            bot.delete_message(chat_id, active_pagination[chat_id])
            active_pagination.pop(chat_id, None)
        except Exception: pass
            
    if chat_id in active_menus:
        try:
            bot.delete_message(chat_id, active_menus[chat_id])
            active_menus.pop(chat_id, None)
        except Exception: pass
            
    show_main_menu(chat_id, call.from_user.id)
    bot.answer_callback_query(call.id)
    

    # 📁 دالة فتح المجلد عند التصفح لأول مرة (ترسل الملفات + المنيو بالأسفل)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_"))
    def cb_open_folder(call):
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        parts = call.data.split("_")
        btn_id = int(parts[1])
        
        try:
            btn_info = execute_query("SELECT name, message_text FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
            if not btn_info: 
                bot.send_message(chat_id, "⚠️ عذراً، هذا القسم غير موجود أو تم حذفه مسبقاً.")
                return
            btn_name, msg_text = btn_info[0]
            perms = get_permissions(user_id)
            
            if chat_id in active_pagination:
                try:
                    bot.delete_message(chat_id, active_pagination[chat_id])
                    active_pagination.pop(chat_id, None)
                except Exception: pass

            has_files = send_button_files_page(chat_id, btn_id, page=1)
            
            if has_files:
                try: bot.delete_message(chat_id, call.message.message_id)
                except Exception: pass
                
                new_menu = bot.send_message(
                    chat_id,
                    f"📂 {btn_name}\n\n{msg_text or ''}",
                    reply_markup=make_sub_menu_markup(btn_id, perms["is_admin"])
                )
                active_menus[chat_id] = new_menu.message_id
            else:
                # [تعديل حسن النحوي]: تصحيح طريقة إسناد المجلد لتجنب الـ SyntaxError
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text=f"📂 {btn_name}\n\n{msg_text or ''}",
                    reply_markup=make_sub_menu_markup(btn_id, perms["is_admin"])
                )
                active_menus[chat_id] = call.message.message_id
            
        except Exception as e:
            print(f"❌ خطأ داخل دالة cb_open_folder: {e}")

    # 🔙 [معالج حسن الذكي للرجوع]: حماية كاملة من الـ ValueError وتجنب تكرار الملفات
    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_"))
    def cb_back(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        
        # [تعديل حسن]: تفكيك آمن للنص وحمايته من السلسلة النصية 'None'
        parent = call.data.split("_")[1]
        if parent == "None":
            show_main_menu(chat_id, user_id)
            return
            
        parent_id = int(parent)

        # 1. حذف رسالة التحكم/الصفحات الحالية بالكامل
        try: 
            bot.delete_message(chat_id, call.message.message_id)
            active_pagination.pop(chat_id, None)
        except: pass

        # 2. تنظيف وإزالة المنيو الحالي من القاموس لمنع التراكم
        if chat_id in active_menus:
            try:
                bot.delete_message(chat_id, active_menus[chat_id])
                active_menus.pop(chat_id, None)
            except: pass

        perms = get_permissions(user_id)

        # 3. إذا كان المجلد الأب هو الصفر (أي المنيو الرئيسي)
        if parent_id == 0:
            show_main_menu(chat_id, user_id)
            return

        # 4. جلب بيانات القسم الأب لعرض أزراره فقط
        btn = execute_query("SELECT name, message_text FROM buttons WHERE id=%s;", (parent_id,), fetch=True)
        if not btn:
            show_main_menu(chat_id, user_id)
            return

        btn_name, msg_text = btn[0]

        # 5. إرسال منيو الأب نظيفاً في الأسفل
        new_menu = bot.send_message(
            chat_id,
            f"📂 {btn_name}\n\n{msg_text or ''}",
            reply_markup=make_sub_menu_markup(parent_id, perms["is_admin"])
        )
        active_menus[chat_id] = new_menu.message_id

    # 🔄 معالج أزرار التنقل (التالي فقط)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("files_"))
    def cb_files_pagination(call):
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        parts = call.data.split("_")
        btn_id = int(parts[1])
        page = int(parts[2])
        
        try: 
            bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
            active_pagination.pop(chat_id, None)
        except Exception: pass
            
        if chat_id in active_menus:
            try: 
                bot.delete_message(chat_id, active_menus[chat_id])
                # [تعديل حسن لمخازن البيانات]: حذف العنصر من القاموس فور مسحه لمنع المؤشرات الميتة
                active_menus.pop(chat_id, None)
            except Exception: pass
                
        send_button_files_page(chat_id, btn_id, page=page)
        
        try:
            btn_info = execute_query("SELECT name, message_text FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
            if btn_info:
                btn_name, msg_text = btn_info[0]
                perms = get_permissions(user_id)
                new_menu = bot.send_message(
                    chat_id,
                    f"📂 {btn_name}\n\n{msg_text or ''}",
                    reply_markup=make_sub_menu_markup(btn_id, perms["is_admin"])
                )
                active_menus[chat_id] = new_menu.message_id
        except Exception as e:
            print(f"Error restoring menu in pagination: {e}")
        
    @bot.callback_query_handler(func=lambda call: call.data == "user_contact")
    def cb_user_contact(call):
        set_user_state(call.from_user.id, "WAITING_FEEDBACK_MSG")
        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="📝 اكتب استفسارك هنا:")
        bot.answer_callback_query(call.id)

    # 7. معالجة الرسالة مع تفاصيل الطالب للإدارة
    @bot.message_handler(func=check_state("WAITING_FEEDBACK_MSG"), content_types=["text"])
    def handle_feedback(message):
        user_id = message.from_user.id
        user_text = message.text
        
        execute_query("INSERT INTO feedback (user_id, username, message_text) VALUES (%s, %s, %s);", 
                      (user_id, message.from_user.username or "N/A", user_text), commit=True)
        
        user_info = execute_query("SELECT first_name, last_name, phone_number FROM users WHERE user_id = %s;", 
                                  (user_id,), fetch=True)
        
        f_name, l_name, phone = ("", "", "غير مسجل")
        if user_info:
            f_name, l_name, phone = user_info[0]

        admin_notification = (
            f"📬 رسالة جديدة من المستخدم:\n\n"
            f"👤 الاسم: {f_name} {l_name}\n"
            f"🆔 ID: {user_id}\n"
            f"📱 الهاتف: {phone}\n"
            f"🔗 المعرف: @{message.from_user.username or 'لا يوجد'}\n\n"
            f"📄 المحتوى:\n{user_text}"
        )

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
        

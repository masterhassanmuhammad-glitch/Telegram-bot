import time
from telebot import types
from gemini import ask_gemini_stream

from config import bot, OWNER_ID, ADMIN_IDS
from database import (
    log_command,
    execute_query,
    set_user_state,
    get_user_state,
    clear_user_state
)
from keyboards import make_main_menu_markup, make_sub_menu_markup
from .helpers import (
    is_user_in_batch,
    send_join_request_menu,
    get_permissions,
    check_state
)

PAGE_SIZE = 10  # عدد الملفات في كل صفحة


# 📑 الدالة المساعدة لإرسال الملفات ودمج أزرار التحكم في رسالة موحدة بالأسفل
def send_button_files_page(chat_id, button_id, page=1, sub_menu_markup=None, base_text=""):
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
    
    # 3. إرسال الملفات للمستخدم أولاً مع إضافة اليوزرنيم
    for file_id, file_type in files:
        try:
            if file_type == 'document': bot.send_document(chat_id, file_id, caption="@Sudanmedicinebot")
            elif file_type == 'photo': bot.send_photo(chat_id, file_id, caption="@Sudanmedicinebot")
            elif file_type == 'audio': bot.send_audio(chat_id, file_id, caption="@Sudanmedicinebot")
            elif file_type == 'video': bot.send_video(chat_id, file_id, caption="@Sudanmedicinebot")
            elif file_type == 'voice': bot.send_voice(chat_id, file_id, caption="@Sudanmedicinebot")
        except Exception as e:
            print(f"Error sending file {file_id}: {str(e)}")
            
    # 4. دمج التحكم بالصفحات مع أزرار المجلد المستقبلة
    markup = sub_menu_markup if sub_menu_markup is not None else types.InlineKeyboardMarkup()
    
    # إضافة زر "التالي ▶️" فقط إذا وُجدت صفحات تالية
    if page < total_pages:
        markup.row(types.InlineKeyboardButton(text="التالي ▶️", callback_data=f"files_{button_id}_{page+1}"))
    
    # بناء نص الرسالة الموحدة المكتملة
    full_text = f"{base_text}\n\n📑 مجموعة الملفات: [ {page} من {total_pages} ]\n📦 إجمالي الملفات في هذا القسم: {total_files} ملف."
    
    bot.send_message(chat_id, full_text, reply_markup=markup)
    return True


# 🛠️ الدالة الرئيسية لتسجيل كل معالجات المستخدم (User Handlers)
def register_user_handlers():

    # 1. أمر البدء (مع الحذف الفوري لرسالة الـ /start وتسجيل اللوج)
    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        username = message.from_user.username or "NoUsername"

        # 📝 تسجيل استخدام أمر /start
        log_command(
            user_id=user_id,
            username=username,
            command="/start"
        )

        # حذف رسالة الـ /start التي أرسلها المستخدم فوراً
        try: bot.delete_message(chat_id, message.message_id)
        except Exception: pass

        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""

        clear_user_state(user_id)

         # التحقق أولاً: إذا لم يكن في القناة، أرسل رسالة الانضمام واقطع التنفيذ فوراً دون حفظه


        # الحفظ في قاعدة البيانات يتم هنا فقط بعد تخطي الفحص بنجاح
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

    # 4. زر التحقق من العضوية (المحدث لتسجيل البيانات عند النجاح)
    @bot.callback_query_handler(func=lambda call: call.data == "check_membership")
    def handle_check_membership(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if is_user_in_batch(bot, user_id):
            bot.answer_callback_query(call.id, "✅ تم التحقق من عضويتك!", show_alert=True)
            
            try: bot.delete_message(chat_id, call.message.message_id)
            except Exception: pass
            
            # بما أنه نجح بالتحقق الآن، نقوم بإدراج بياناته في قاعدة البيانات لأول مرة
            username = call.from_user.username or "NoUsername"
            first_name = call.from_user.first_name or ""
            last_name = call.from_user.last_name or ""
            
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
            
            res = execute_query("SELECT phone_number FROM users WHERE user_id = %s;", (user_id,), fetch=True)
            if not (res and res[0][0]):
                ask_for_phone(chat_id, user_id)
            else:
                show_main_menu(chat_id, user_id)
        else:
            bot.answer_callback_query(call.id, "عذراً، أنت لست عضواً في كلية الطب من الدفعتين 35&36", show_alert=True)

    # 5. عرض القائمة الرئيسية (الحارس المركزي للمنيو)
    def show_main_menu(chat_id, user_id):
        # التحقق من انضمام المستخدم للدفعة


        # جلب الصلاحيات وبناء القائمة
        perms = get_permissions(user_id)
        
        text = """🏛️ القائمة الرئيسية

﴿يَرْفَعِ اللَّهُ الَّذِينَ آمَنُوا مِنكُمْ وَالَّذِينَ أُوتُوا الْعِلْمَ دَرَجَاتٍ﴾
📖 سورة المجادلة: 11"""

        bot.send_message(chat_id, text, reply_markup=make_main_menu_markup(perms, user_id))

    # 6. العودة للمنيو الرئيسي
    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    def cb_main_menu(call):
        chat_id = call.message.chat.id
        
        try: bot.delete_message(chat_id, call.message.message_id)
        except Exception: pass
                
        show_main_menu(chat_id, call.from_user.id)
        bot.answer_callback_query(call.id)

    # 📁 دالة فتح المجلد الذكية
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
            
            base_text = f"📂 {btn_name}\n\n{msg_text or ''}"
            sub_markup = make_sub_menu_markup(btn_id, perms["is_admin"])
            
            count_res = execute_query("SELECT COUNT(*) FROM button_files WHERE button_id = %s;", (btn_id,), fetch=True)
            total_files = count_res[0][0] if count_res else 0
            
            if total_files > 0:
                try: bot.delete_message(chat_id, call.message.message_id)
                except Exception: pass
                
                send_button_files_page(chat_id, btn_id, page=1, sub_menu_markup=sub_markup, base_text=base_text)
            else:
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        text=base_text,
                        reply_markup=sub_markup
                    )
                except Exception:
                    pass
            
        except Exception as e:
            print(f"❌ خطأ داخل دالة cb_open_folder: {e}")

    # 🔙 معالج الرجوع الآمن والتعديل الفوري
    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_"))
    def cb_back(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        
        parent = call.data.split("_")[1]
        if parent == "None" or parent == "0":
            try: bot.delete_message(chat_id, call.message.message_id)
            except Exception: pass
            show_main_menu(chat_id, user_id)
            return
            
        parent_id = int(parent)
        perms = get_permissions(user_id)

        btn = execute_query("SELECT name, message_text FROM buttons WHERE id=%s;", (parent_id,), fetch=True)
        if not btn:
            try: bot.delete_message(chat_id, call.message.message_id)
            except Exception: pass
            show_main_menu(chat_id, user_id)
            return

        btn_name, msg_text = btn[0]
        base_text = f"📂 {btn_name}\n\n{msg_text or ''}"
        parent_markup = make_sub_menu_markup(parent_id, perms["is_admin"])

        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=base_text,
                reply_markup=parent_markup
            )
        except Exception:
            try: bot.delete_message(chat_id, call.message.message_id)
            except Exception: pass
            bot.send_message(chat_id, base_text, reply_markup=parent_markup)

    # 🔄 معالج أزرار التنقل
    @bot.callback_query_handler(func=lambda call: call.data.startswith("files_"))
    def cb_files_pagination(call):
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        parts = call.data.split("_")
        btn_id = int(parts[1])
        page = int(parts[2])
        
        try: bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        except Exception: pass
                
        try:
            btn_info = execute_query("SELECT name, message_text FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
            if btn_info:
                btn_name, msg_text = btn_info[0]
                base_text = f"📂 {btn_name}\n\n{msg_text or ''}"
                perms = get_permissions(user_id)
                sub_markup = make_sub_menu_markup(btn_id, perms["is_admin"])
                
                send_button_files_page(chat_id, btn_id, page=page, sub_menu_markup=sub_markup, base_text=base_text)
        except Exception as e:
            print(f"Error in pagination: {e}")
        
    @bot.callback_query_handler(func=lambda call: call.data == "user_contact")
    def cb_user_contact(call):
        chat_id = call.message.chat.id
        set_user_state(call.from_user.id, "WAITING_FEEDBACK_MSG")
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="📝 اكتب استفسارك هنا:")
        except Exception:
            pass
        bot.answer_callback_query(call.id)

    # 7. معالجة الرسالة وإرسالها للإدارة
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

    # 🤖 8. معالج الرد التلقائي عبر الذكاء الاصطناعي (يوضع دائماً في النهاية للتقاط أي نص عادي)
    # 🟢 التعديل في السطر الأول فقط (إضافة الشرط لمنع التقاط الأوامر)
    @bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'), content_types=['text'])
    def auto_ai_handler(message):
        print(f"📩 [Received] User: {message.from_user.username or message.from_user.id} | Text: {message.text}")

    # 🚫 1. تجاهل المجموعات والقنوات
        if message.chat.type in ['group', 'supergroup']:
            return

    # 🚫 2. تجاهل الحالات الإدارية والتفاعلية
        if get_user_state(message.from_user.id):
            return

        text = message.text.strip()
        if not text:
            return
    
    # ... باقي كود الدالة كما هو دون تغيير ...
        
    # ... باقي كود الدالة كما هو دون تغيير ...
        

        text = message.text.strip()
        if not text:
            return

        user_id = message.from_user.id
        username = message.from_user.username or "NoUsername"
        chat_id = message.chat.id

        # 📝 تسجيل النص والأسئلة في السجلات
        log_command(
            user_id=user_id,
            username=username,
            command="/ask",
            prompt=text
        )

        waiting_msg = bot.reply_to(message, "🤖 جارِ التفكير، يرجى الإنتظار...")

        try:
            full_text = ""
            last_edit_time = 0

            for chunk_text in ask_gemini_stream(text):
                full_text += chunk_text

                cleaned_text = (
                    full_text.replace("<p>", "")
                    .replace("</p>", "\n")
                    .replace("<br>", "\n")
                    .replace("<br/>", "\n")
                )

                current_time = time.time()

                if current_time - last_edit_time > 1.5:
                    try:
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=waiting_msg.message_id,
                            text=cleaned_text[:4000] + " ✍️...",
                            parse_mode="HTML"
                        )
                        last_edit_time = current_time
                    except Exception:
                        pass

            final_text = (
                full_text.replace("<p>", "")
                .replace("</p>", "\n")
                .replace("<br>", "\n")
                .replace("<br/>", "\n")
            )[:4000]

            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=waiting_msg.message_id,
                    text=final_text if final_text else "⚠️ لم يتم استلام أي نص.",
                    parse_mode="HTML"
                )
            except Exception:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=waiting_msg.message_id,
                    text=final_text if final_text else "⚠️ لم يتم استلام أي نص."
                )

        except Exception as e:
            print(f"❌ AI Error: {e}")
            try:
                bot.delete_message(chat_id, waiting_msg.message_id)
            except Exception:
                pass
            bot.reply_to(message, "❌ حدث خطأ أثناء معالجة الطلب.")
    

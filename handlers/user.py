from .helpers import (  # تأكد هنا أن اسم الملف هو نفس اسم ملفك (مثلاً helpers.py)
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

    @bot.message_handler(func=lambda message: message.chat.type in ["group", "supergroup"])
    def debug_chat_id(message):
        print(f"DEBUG: Group Chat ID is {message.chat.id}")

    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        username = message.from_user.username or "NoUsername"

        print(f"👋 [البدء] {message.from_user.first_name} (@{username}) دخل البوت.")

        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        execute_query(
            """
            INSERT INTO users (user_id, username)
            VALUES (%s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET username = EXCLUDED.username;
            """,
            (user_id, username),
            commit=True
        )

        clear_user_state(user_id)

        if not is_user_in_batch(bot, user_id):
            send_join_request_menu(bot, chat_id)
            return

        welcome_text = (
            "👋 أهلاً بك في البوت الطبي التعليمي.\n\n"
            "الرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات والمحاضرات الطبية بسهولة 👇"
        )

        perms = get_permissions(user_id)

        sent_menu = bot.send_message(
            chat_id,
            welcome_text,
            reply_markup=make_main_menu_markup(perms, user_id)
        )

        active_menus[chat_id] = sent_menu.message_id

    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    def cb_main_menu(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        clear_user_state(user_id)
        perms = get_permissions(user_id)
        
        send_files_and_recreate_menu(
            bot, chat_id, [], 
            "👋 أهلاً بك في البوت الطبي التعليمي.\n\nالرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات الطبية 👇",
            make_main_menu_markup(perms, user_id)
        )

        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_"))
    def cb_open_folder(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        data_call = call.data

        parts = data_call.split("_")
        if len(parts) < 2 or parts[1] in ["None", "null"]:
            perms = get_permissions(user_id)
            send_files_and_recreate_menu(
                bot, chat_id, [], 
                "👋 أهلاً بك في البوت الطبي التعليمي.\n\nالرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات الطبية 👇",
                make_main_menu_markup(perms, user_id)
            )
            bot.answer_callback_query(call.id)
            return

        btn_id = int(parts[1])
        btn_info = execute_query("SELECT name, message_text FROM buttons WHERE id = %s;", (btn_id,), fetch=True)

        if not btn_info:
            bot.answer_callback_query(call.id, "⚠️ هذا المجلد لم يعد موجوداً!")
            return

        btn_name, msg_text = btn_info[0]
        display_text = f"📂 القسم: {btn_name}" + (f"\n\n📄 {msg_text}" if msg_text else "")
        
        perms = get_permissions(user_id)

        files_data = execute_query(
            "SELECT file_id, file_type, NULL FROM button_files WHERE button_id = %s ORDER BY id ASC;",
            (btn_id,),
            fetch=True
        )

        send_files_and_recreate_menu(
            bot, 
            chat_id, 
            files_data, 
            display_text, 
            make_sub_menu_markup(btn_id, perms["is_admin"])
        )

        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "user_contact")
    def cb_user_contact(call):
        user_id = call.from_user.id
        set_user_state(user_id, "WAITING_FEEDBACK_MSG")

        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text="📝 اكتب رسالتك أو استفسارك هنا وسنقوم بإيصالها للمشرفين فوراً للرد عليك:\n\n(ملاحظة: اضغط /start للإلغاء)"
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_FEEDBACK_MSG"), content_types=["text"])
    def handle_user_feedback(message):
        user_id = message.from_user.id
        username = message.from_user.username or "NoUsername"

        execute_query(
            "INSERT INTO feedback (user_id, username, message_text) VALUES (%s, %s, %s);",
            (user_id, username, message.text),
            commit=True
        )

        clear_user_state(user_id)
        perms = get_permissions(user_id)

        bot.send_message(
            user_id,
            "✅ تم إرسال رسالتك بنجاح إلى المشرفين. سيتم الرد عليك قريباً! 🥰",
            reply_markup=make_main_menu_markup(perms, user_id)
        )

        notify_ids = {OWNER_ID} if OWNER_ID else set()
        db_feedback_admins = execute_query("SELECT admin_id FROM admins WHERE can_feedback = TRUE;", fetch=True)
        for (adm_id,) in db_feedback_admins: notify_ids.add(adm_id)
        for static_adm in ADMIN_IDS: notify_ids.add(static_adm)

        for target_admin in notify_ids:
            try:
                bot.send_message(target_admin, f"📬 رسالة جديدة من المستخدم @{username} ({user_id}):\n\n📄 {message.text}")
            except Exception: pass

    @bot.callback_query_handler(func=lambda call: call.data == "check_membership")
    def handle_check_membership(call):
        chat_id = call.message.chat.id
        user_id = call.from_user.id

        if is_user_in_batch(bot, user_id):
            try: bot.delete_message(chat_id, call.message.message_id)
            except Exception: pass
            
            clear_user_state(user_id)
            perms = get_permissions(user_id)
            bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح! مرحباً بك.", show_alert=True)
            
            sent_menu = bot.send_message(
                chat_id,
                "👋 أهلاً بك في البوت الطبي التعليمي.\n\nالرجاء استخدام الأزرار أدناه للتنقل.",
                reply_markup=make_main_menu_markup(perms, user_id)
            )
            active_menus[chat_id] = sent_menu.message_id
        else:
            bot.answer_callback_query(call.id, "❌ لم تنضم إلى مجموعة الدفعة بعد.", show_alert=True)
                                

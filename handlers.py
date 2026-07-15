from config import bot, ADMIN_IDS, OWNER_ID
from database import (
    execute_query, execute_query_dict, 
    set_user_state, get_user_state, clear_user_state
)
from keyboards import (
    make_main_menu_markup, make_sub_menu_markup, 
    make_admin_settings_markup, make_admin_edit_options_markup,
    make_admin_choose_parent_markup, make_admin_move_button_markup,
    make_admin_file_manager_markup,
    make_owner_manage_admins_markup, make_remove_admin_list_markup,
    make_permissions_markup
)
import telebot

# --- دالة فحص والتحقق من الصلاحيات الفردية والديناميكية ---
def get_permissions(user_id):
    # 1. إذا كان هو المالك الأساسي (صاحب أول معرف ID في السيرفر) فلديه كامل الصلاحيات والتحكم بالمشرفين
    if OWNER_ID and user_id == OWNER_ID:
        return {
            'is_admin': True,
            'is_owner': True,
            'can_settings': True,
            'can_broadcast': True,
            'can_feedback': True,
            'can_count': True
        }
    
    # 2. فحص الصلاحيات الممنوحة للمشرف من قاعدة بيانات Neon
    res = execute_query("SELECT can_settings, can_broadcast, can_feedback, can_count FROM admins WHERE admin_id = %s;", (user_id,), fetch=True)
    if res:
        return {
            'is_admin': True,
            'is_owner': False,
            'can_settings': res[0][0],
            'can_broadcast': res[0][1],
            'can_feedback': res[0][2],
            'can_count': res[0][3]
        }
    
    # 3. دعم احتياطي للمعرفات الثابتة في البيئة بجميع الصلاحيات
    if user_id in ADMIN_IDS:
        return {
            'is_admin': True,
            'is_owner': False,
            'can_settings': True,
            'can_broadcast': True,
            'can_feedback': True,
            'can_count': True
        }
        
    return {
        'is_admin': False,
        'is_owner': False,
        'can_settings': False,
        'can_broadcast': False,
        'can_feedback': False,
        'can_count': False
    }

def register_handlers():
    
    # ==========================================
    # 1. Start Command & Main Menu
    # ==========================================
    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        user_id = message.from_user.id
        username = message.from_user.username or "NoUsername"
        
        execute_query(
            "INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username;",
            (user_id, username), commit=True
        )
        
        clear_user_state(user_id)
        
        welcome_text = (
            "👋 أهلاً بك في البوت الطبي التعليمي.\n\n"
            "الرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات والمحاضرات الطبية بسهولة 👇"
        )
        perms = get_permissions(user_id)
        bot.send_message(user_id, welcome_text, reply_markup=make_main_menu_markup(perms, user_id))

    # ==========================================
    # 2. Master Text & Document Handler (FSM)
    # ==========================================
    @bot.message_handler(content_types=['text', 'document', 'photo', 'audio', 'video', 'voice'])
    def handle_all_messages(message):
        user_id = message.from_user.id
        state, data = get_user_state(user_id)
        perms = get_permissions(user_id)
        
        if not state:
            if perms['is_admin']:
                bot.send_message(user_id, "⚠️ لم أفهم هذا الأمر. الرجاء استخدام أزرار لوحة التحكم أو كتابة /start للبدء.")
            else:
                bot.send_message(user_id, "⚠️ الرجاء استخدام أزرار القائمة للتنقل. إذا واجهت مشكلة اضغط /start أو انقر على زر 'مراسلة الإدارة'.")
            return

        # --- أ) معالجات المستخدم العادي ---
        
        if state == "WAITING_FEEDBACK_MSG":
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ عذراً، يجب إرسال رسالة نصية فقط للمشرفين.")
                return
            
            username = message.from_user.username or "NoUsername"
            execute_query(
                "INSERT INTO feedback (user_id, username, message_text) VALUES (%s, %s, %s);",
                (user_id, username, message.text), commit=True
            )
            
            clear_user_state(user_id)
            perms = get_permissions(user_id)
            bot.send_message(user_id, "✅ تم إرسال رسالتك بنجاح إلى المشرفين. سيتم الرد عليك قريباً! 🥰", reply_markup=make_main_menu_markup(perms, user_id))
            
            # إرسال الإشعار للمشرفين الذين يمتلكون صلاحية استقبال الرسائل والمالك
            notify_ids = {OWNER_ID} if OWNER_ID else set()
            db_feedback_admins = execute_query("SELECT admin_id FROM admins WHERE can_feedback = TRUE;", fetch=True)
            for (adm_id,) in db_feedback_admins:
                notify_ids.add(adm_id)
            for static_adm in ADMIN_IDS:
                notify_ids.add(static_adm)
                
            for target_admin in notify_ids:
                try:
                    bot.send_message(target_admin, f"📬 رسالة جديدة من المستخدم @{username} ({user_id}):\n\n📄 {message.text}")
                except Exception:
                    pass
            return

        # --- ب) معالجات المشرف (Admin) والتحقق من الصلاحيات ---
        if not perms['is_admin']:
            clear_user_state(user_id)
            return

        # معالجة البث الجماعي
        if state == "WAITING_BROADCAST_MSG":
            if not perms['can_broadcast']:
                bot.send_message(user_id, "❌ عذراً، لا تملك صلاحية البث الجماعي.")
                clear_user_state(user_id)
                return
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ عذراً، يجب إرسال رسالة نصية فقط للبث الجماعي.")
                return
            
            broadcast_text = message.text
            all_users = execute_query("SELECT user_id FROM users;", fetch=True)
            
            success_count = 0
            for u_id_tuple in all_users:
                u_id = u_id_tuple[0]
                try:
                    bot.send_message(u_id, f"📢 إعلان هام من الإدارة:\n\n{broadcast_text}")
                    success_count += 1
                except Exception:
                    pass
            
            clear_user_state(user_id)
            bot.send_message(user_id, f"✅ تم إرسال الإعلان الجماعي بنجاح إلى {success_count} مستخدم.", reply_markup=make_main_menu_markup(perms, user_id))
            return

        # معالجة رد المشرف على رسالة مستخدم
        if state == "WAITING_ADMIN_REPLY":
            if not perms['can_feedback']:
                bot.send_message(user_id, "❌ ليس لديك صلاحية الرد على رسائل المستخدمين.")
                clear_user_state(user_id)
                return
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ الرجاء كتابة رد نصي فقط.")
                return
            
            target_user_id = data.get('target_user_id')
            fb_id = data.get('fb_id')
            
            try:
                bot.send_message(target_user_id, f"💬 رد من الإدارة على استفسارك:\n\n{message.text}")
                execute_query("UPDATE feedback SET status = 'replied' WHERE id = %s;", (fb_id,), commit=True)
                bot.send_message(user_id, "✅ تم إرسال الرد بنجاح للمستخدم!", reply_markup=make_main_menu_markup(perms, user_id))
            except Exception as e:
                bot.send_message(user_id, f"❌ فشل إرسال الرد للمستخدم. الخطأ: {str(e)}")
            
            clear_user_state(user_id)
            return

        # معالجة إدخال اسم الزر الجديد
        if state == "WAITING_BTN_NAME":
            if not perms['can_settings']:
                bot.send_message(user_id, "❌ ليس لديك صلاحية التعديل على الأزرار.")
                clear_user_state(user_id)
                return
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ اسم الزر يجب أن يكون نصياً. أعد الإرسال:")
                return
            
            btn_name = message.text.strip()
            if len(btn_name) > 50:
                bot.send_message(user_id, "❌ الاسم طويل جداً (أقصى حد 50 حرف). أعد الإرسال:")
                return
                
            clear_user_state(user_id)
            bot.send_message(
                user_id, 
                f"📂 حدد موقع الزر الجديد [ {btn_name} ] في الشجرة الهيكلية:", 
                reply_markup=make_admin_choose_parent_markup(btn_name)
            )
            return

        # معالجة إدخال نص رسالة الزر
        if state == "WAITING_BTN_TEXT":
            if not perms['can_settings']:
                clear_user_state(user_id)
                return
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ محتوى الرسالة يجب أن يكون نصاً. أعد الإرسال:")
                return
            
            btn_id = data.get('button_id')
            execute_query("UPDATE buttons SET message_text = %s WHERE id = %s;", (message.text, btn_id), commit=True)
            
            clear_user_state(user_id)
            bot.send_message(
                user_id, 
                "✅ تم حفظ الرسالة النصية للزر بنجاح! يمكنك الآن إدارة الملفات المربوطة به.", 
                reply_markup=make_admin_edit_options_markup(btn_id)
            )
            return

        # معالجة تعديل اسم الزر
        if state == "WAITING_EDIT_NAME":
            if not perms['can_settings']:
                clear_user_state(user_id)
                return
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ الاسم الجديد يجب أن يكون نصاً:")
                return
            
            btn_id = data.get('button_id')
            new_name = message.text.strip()
            
            execute_query("UPDATE buttons SET name = %s WHERE id = %s;", (new_name, btn_id), commit=True)
            clear_user_state(user_id)
            bot.send_message(user_id, "✅ تم تعديل اسم الزر بنجاح!", reply_markup=make_admin_edit_options_markup(btn_id))
            return

        # معالجة تعديل رسالة الزر
        if state == "WAITING_EDIT_TEXT":
            if not perms['can_settings']:
                clear_user_state(user_id)
                return
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ الرسالة يجب أن تكون نصاً:")
                return
            
            btn_id = data.get('button_id')
            new_text = message.text
            
            execute_query("UPDATE buttons SET message_text = %s WHERE id = %s;", (new_text, btn_id), commit=True)
            clear_user_state(user_id)
            bot.send_message(user_id, "✅ تم تعديل الرسالة النصية للزر بنجاح!", reply_markup=make_admin_edit_options_markup(btn_id))
            return

        # معالجة استقبال الملفات
        if state == "WAITING_ADD_FILE":
            if not perms['can_settings']:
                clear_user_state(user_id)
                return
            btn_id = data.get('button_id')
            file_id = None
            file_type = None
            
            if message.content_type == 'document':
                file_id = message.document.file_id
                file_type = 'document'
            elif message.content_type == 'photo':
                file_id = message.photo[-1].file_id
                file_type = 'photo'
            elif message.content_type == 'audio':
                file_id = message.audio.file_id
                file_type = 'audio'
            elif message.content_type == 'video':
                file_id = message.video.file_id
                file_type = 'video'
            elif message.content_type == 'voice':
                file_id = message.voice.file_id
                file_type = 'voice'
            
            if not file_id:
                bot.send_message(user_id, "❌ لم يتم التعرف على نوع الملف المرسل. الرجاء إرسال الملف مجدداً:")
                return
                
            execute_query(
                "INSERT INTO button_files (button_id, file_id, file_type) VALUES (%s, %s, %s);",
                (btn_id, file_id, file_type), commit=True
            )
            
            clear_user_state(user_id)
            bot.send_message(
                user_id, 
                "✅ تم رفع الملف وربطه بالزر بنجاح!", 
                reply_markup=make_admin_file_manager_markup(btn_id)
            )
            return

        # معالجة إرسال ID الآدمن الجديد (خاص بالمالك فقط)
        if state == "WAITING_NEW_ADMIN_ID":
            if user_id != OWNER_ID:
                clear_user_state(user_id)
                return
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ الرجاء إرسال رقم الـ ID فقط:")
                return
            
            try:
                new_admin_id = int(message.text.strip())
            except ValueError:
                bot.send_message(user_id, "❌ الـ ID يجب أن يتكون من أرقام فقط. أعد المحاولة:")
                return
                
            # تهيئة الصلاحيات الافتراضية للمشرف الجديد (تكون مغلقة افتراضياً)
            perms_dict = {
                'settings': False,
                'broadcast': False,
                'feedback': False,
                'count': False
            }
            
            set_user_state(user_id, "CHOOSING_ADMIN_PERMISSIONS", {"new_admin_id": new_admin_id, "perms": perms_dict})
            bot.send_message(
                user_id,
                f"👤 المشرف المراد إضافته: `{new_admin_id}`\n\n"
                "⚙️ حدد صلاحيات المشرف الجديد (يجب تفعيل خيار واحد على الأقل):",
                parse_mode="Markdown",
                reply_markup=make_permissions_markup(perms_dict, new_admin_id)
            )
            return


    # ==========================================
    # 3. Inline Query Callback Handlers
    # ==========================================
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        user_id = call.from_user.id
        data_call = call.data
        perms = get_permissions(user_id)
        
        # القائمة الرئيسية والعودة لها
        if data_call == "main_menu":
            clear_user_state(user_id)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="👋 أهلاً بك في البوت الطبي التعليمي.\n\nالرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات الطبية 👇",
                reply_markup=make_main_menu_markup(perms, user_id)
            )
            bot.answer_callback_query(call.id)
            return

        # فتح المجلدات والملفات (متاح للجميع)
        if data_call.startswith("open_"):
            parts = data_call.split("_")
            if len(parts) < 2 or parts[1] == "None" or parts[1] == "null":
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    text="👋 أهلاً بك في البوت الطبي التعليمي.\n\nالرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات الطبية 👇",
                    reply_markup=make_main_menu_markup(perms, user_id)
                )
                bot.answer_callback_query(call.id)
                return
                
            btn_id = int(parts[1])
            
            btn_info = execute_query("SELECT name, message_text FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
            if not btn_info:
                bot.answer_callback_query(call.id, "⚠️ هذا المجلد أو الزر لم يعد موجوداً!")
                return
            
            btn_name, msg_text = btn_info[0]
            
            display_text = f"📂 القسم: {btn_name}"
            if msg_text:
                display_text += f"\n\n📄 {msg_text}"
                
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=display_text,
                reply_markup=make_sub_menu_markup(btn_id, perms['is_admin'])
            )
            
            files = execute_query("SELECT file_id, file_type FROM button_files WHERE button_id = %s ORDER BY id ASC;", (btn_id,), fetch=True)
            for f_id, f_type in files:
                try:
                    if f_type == 'document':
                        bot.send_document(user_id, f_id)
                    elif f_type == 'photo':
                        bot.send_photo(user_id, f_id)
                    elif f_type == 'audio':
                        bot.send_audio(user_id, f_id)
                    elif f_type == 'video':
                        bot.send_video(user_id, f_id)
                    elif f_type == 'voice':
                        bot.send_voice(user_id, f_id)
                except Exception as e:
                    print(f"Error sending file {f_id}: {str(e)}")
            
            bot.answer_callback_query(call.id)
            return

        # زر مراسلة الإدارة للأعضاء
        if data_call == "user_contact":
            set_user_state(user_id, "WAITING_FEEDBACK_MSG")
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📝 اكتب رسالتك أو استفسارك هنا وسنقوم بإيصالها للمشرفين فوراً للرد عليك:\n\n(ملاحظة: اضغط /start لإلغاء المراسلة والعودة)"
            )
            bot.answer_callback_query(call.id)
            return

        # =======================================================
        # فحص جدار الحماية الأمني للصلاحيات والتراخيص
        # =======================================================
        
        # 1. فلترة حماية صلاحيات الإعدادات والتعديل
        settings_callbacks = [
            "admin_settings", "adm_add_btn", "adm_del_btn", "choose_edit_", 
            "editopt_name_", "editopt_msg_", "editopt_move_", "exec_move_", 
            "editopt_files_", "addfile_", "delfile_", "setparent_new_"
        ]
        if any(data_call.startswith(sc) for sc in settings_callbacks):
            if not perms['can_settings']:
                bot.answer_callback_query(call.id, "❌ عذراً، لا تملك صلاحية الإعدادات الإدارية وتعديل الأزرار.", show_alert=True)
                return

        # 2. فلترة حماية صلاحيات إرسال الرسائل الجماعية
        if data_call == "admin_broadcast":
            if not perms['can_broadcast']:
                bot.answer_callback_query(call.id, "❌ عذراً، لا تملك صلاحية إرسال الرسائل الجماعية.", show_alert=True)
                return

        # 3. فلترة حماية صلاحيات تصفح رسائل الأعضاء والردود
        feedback_callbacks = ["admin_view_feedback", "replyfb_"]
        if any(data_call.startswith(fc) for fc in feedback_callbacks):
            if not perms['can_feedback']:
                bot.answer_callback_query(call.id, "❌ عذراً، لا تملك صلاحية تصفح أو رد رسائل الأعضاء.", show_alert=True)
                return

        # 4. فلترة حماية صلاحيات عرض أرقام الإحصائيات
        if data_call == "admin_count_users":
            if not perms['can_count']:
                bot.answer_callback_query(call.id, "❌ عذراً، لا تملك صلاحية عرض إحصائيات وعدد المستخدمين.", show_alert=True)
                return

        # 5. فلترة حماية المالك فقط (إدارة المشرفين بالكامل)
        owner_callbacks = [
            "owner_manage_admins", "owner_add_admin", "owner_remove_admin_list", 
            "exec_remove_admin_", "toggle_", "save_admin_"
        ]
        if any(data_call.startswith(oc) for oc in owner_callbacks):
            if user_id != OWNER_ID:
                bot.answer_callback_query(call.id, "❌ هذا القسم والخيارات مخصصة لمالك البوت الأصلي فقط!", show_alert=True)
                return

        # ==========================================
        # تنفيذ العمليات الإدارية الآمنة بعد الفلترة
        # ==========================================

        # فتح لوحة الإعدادات
        if data_call == "admin_broadcast":
            set_user_state(user_id, "WAITING_BROADCAST_MSG")
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📢 أرسل الآن الرسالة النصية التي تريد نشرها لكافة مستخدمي البوت:\n\n(اضغط /start للإلغاء)"
            )
            bot.answer_callback_query(call.id)
            return

        # عرض عدد مستخدمي البوت
        if data_call == "admin_count_users":
            count = execute_query("SELECT COUNT(*) FROM users;", fetch=True)[0][0]
            bot.answer_callback_query(call.id, f"📊 إجمالي عدد المشتركين في البوت: {count} مستخدم.", show_alert=True)
            return

        # عرض الرسائل الواردة
        if data_call == "admin_view_feedback":
            feedbacks = execute_query_dict("SELECT id, user_id, username, message_text FROM feedback WHERE status = 'pending' ORDER BY id DESC LIMIT 5;")
            if not feedbacks:
                bot.answer_callback_query(call.id, "📥 لا توجد رسائل معلقة حالياً! كل شيء هادئ.", show_alert=True)
                return
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📥 إليك آخر 5 رسائل معلقة من الأعضاء:",
                reply_markup=make_admin_settings_markup()
            )
            
            for fb in feedbacks:
                reply_markup = telebot.types.InlineKeyboardMarkup()
                reply_markup.add(telebot.types.InlineKeyboardButton(text="💬 الرد على الرسالة", callback_data=f"replyfb_{fb['id']}_{fb['user_id']}"))
                bot.send_message(
                    user_id,
                    f"👤 العضو: @{fb['username']} ({fb['user_id']})\n\n📄 الرسالة:\n{fb['message_text']}",
                    reply_markup=reply_markup
                )
            bot.answer_callback_query(call.id)
            return

        # الرد على رسالة مستخدم
        if data_call.startswith("replyfb_"):
            parts = data_call.split("_")
            fb_id = int(parts[1])
            target_user_id = int(parts[2])
            
            set_user_state(user_id, "WAITING_ADMIN_REPLY", {"target_user_id": target_user_id, "fb_id": fb_id})
            bot.send_message(user_id, "✍️ اكتب ردك الآن ليتم إرساله فوراً للمستخدم:")
            bot.answer_callback_query(call.id)
            return

        # إضافة زر
        if data_call == "adm_add_btn":
            set_user_state(user_id, "WAITING_BTN_NAME")
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="✍️ حسناً، أرسل الآن اسم الزر الجديد الذي تريد إنشاءه:"
            )
            bot.answer_callback_query(call.id)
            return

        # تحديد موقع الزر وحفظه
        if data_call.startswith("setparent_new_"):
            parts = data_call.split("_")
            btn_name = parts[2]
            parent_raw = parts[3]
            
            parent_id = None if parent_raw == "null" else int(parent_raw)
            res = execute_query(
                "INSERT INTO buttons (name, parent_id) VALUES (%s, %s) RETURNING id;",
                (btn_name, parent_id), fetch=True, commit=True
            )
            new_btn_id = res[0][0]
            
            set_user_state(user_id, "WAITING_BTN_TEXT", {"button_id": new_btn_id})
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=f"✅ تم إنشاء زر [ {btn_name} ] بنجاح!\n\n✍️ أرسل الآن الرسالة النصية التوضيحية له:"
            )
            bot.answer_callback_query(call.id)
            return

        # قائمة تعديل الأزرار
        if data_call == "adm_del_btn":
            buttons = execute_query("SELECT id, name FROM buttons ORDER BY id ASC;", fetch=True)
            if not buttons:
                bot.answer_callback_query(call.id, "⚠️ لا توجد أزرار مضافة لتعديلها حالياً!", show_alert=True)
                return
            
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            for b_id, b_name in buttons:
                markup.add(telebot.types.InlineKeyboardButton(text=f"✏️ تعديل: {b_name}", callback_data=f"choose_edit_{b_id}"))
            markup.add(telebot.types.InlineKeyboardButton(text="🔙 إلغاء", callback_data="admin_settings"))
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="✏️ اختر الزر الذي ترغب بتعديله:",
                reply_markup=markup
            )
            bot.answer_callback_query(call.id)
            return

        # استعراض خيارات تعديل زر
        if data_call.startswith("choose_edit_"):
            btn_id = int(data_call.split("_")[2])
            btn_info = execute_query("SELECT name FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
            if not btn_info:
                bot.answer_callback_query(call.id, "⚠️ هذا الزر غير متوفر!")
                return
                
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=f"🛠 تعديل خصائص الزر: [ {btn_info[0][0]} ]",
                reply_markup=make_admin_edit_options_markup(btn_id)
            )
            bot.answer_callback_query(call.id)
            return

        # تعديل اسم الزر
        if data_call.startswith("editopt_name_"):
            btn_id = int(data_call.split("_")[2])
            set_user_state(user_id, "WAITING_EDIT_NAME", {"button_id": btn_id})
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="✍️ أرسل الاسم الجديد للزر الآن:"
            )
            bot.answer_callback_query(call.id)
            return

        # تعديل رسالة الزر
        if data_call.startswith("editopt_msg_"):
            btn_id = int(data_call.split("_")[2])
            set_user_state(user_id, "WAITING_EDIT_TEXT", {"button_id": btn_id})
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="✍️ أرسل الرسالة النصية الجديدة للزر:"
            )
            bot.answer_callback_query(call.id)
            return

        # نقل موقع الزر
        if data_call.startswith("editopt_move_"):
            btn_id = int(data_call.split("_")[2])
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="🔄 اختر المجلد الأب الجديد للزر:",
                reply_markup=make_admin_move_button_markup(btn_id)
            )
            bot.answer_callback_query(call.id)
            return

        # تنفيذ النقل
        if data_call.startswith("exec_move_"):
            parts = data_call.split("_")
            btn_id = int(parts[2])
            parent_raw = parts[3]
            
            parent_id = None if parent_raw == "null" else int(parent_raw)
            execute_query("UPDATE buttons SET parent_id = %s WHERE id = %s;", (parent_id, btn_id), commit=True)
            
            bot.answer_callback_query(call.id, "✅ تم نقل الزر بنجاح وتحديث الشجرة!", show_alert=True)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="🛠 تم تحديث موضع الزر بنجاح. ما الذي ترغب بفعله الآن؟",
                reply_markup=make_admin_edit_options_markup(btn_id)
            )
            return

        # إدارة ملفات الزر
        if data_call.startswith("editopt_files_"):
            btn_id = int(data_call.split("_")[2])
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📁 قائمة الملفات المربوطة بهذا الزر حالياً. يمكنك تعديلها:",
                reply_markup=make_admin_file_manager_markup(btn_id)
            )
            bot.answer_callback_query(call.id)
            return

        # رفع ملف جديد
        if data_call.startswith("addfile_"):
            btn_id = int(data_call.split("_")[1])
            set_user_state(user_id, "WAITING_ADD_FILE", {"button_id": btn_id})
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📤 أرسل الآن الملف الذي تريد ربطه بالزر (PDF، صورة، فيديو، إلخ):"
            )
            bot.answer_callback_query(call.id)
            return

        # حذف ملف من الزر
        if data_call.startswith("delfile_"):
            parts = data_call.split("_")
            file_record_id = int(parts[1])
            btn_id = int(parts[2])
            
            execute_query("DELETE FROM button_files WHERE id = %s;", (file_record_id,), commit=True)
            bot.answer_callback_query(call.id, "✅ تم حذف الملف بنجاح!", show_alert=True)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📁 تم تحديث الملفات بنجاح. يمكنك إضافة ملفات أخرى أو العودة:",
                reply_markup=make_admin_file_manager_markup(btn_id)
            )
            return

        # ==========================================
        # 👥 تنفيذ أوامر المالك (إدارة المشرفين وصلاحياتهم)
        # ==========================================

        # فتح لوحة المشرفين
        if data_call == "owner_manage_admins":
            clear_user_state(user_id)
            admins = execute_query("SELECT admin_id, can_settings, can_broadcast, can_feedback, can_count FROM admins;", fetch=True)
            text = "👥 **قائمة المشرفين الحاليين وصلاحياتهم:**\n\n"
            if not admins:
                text += "⚠️ لا يوجد أي مشرف مضاف حالياً."
            else:
                for adm_id, c_set, c_broad, c_feed, c_cnt in admins:
                    perms_list = []
                    if c_set: perms_list.append("⚙️ إعدادات")
                    if c_broad: perms_list.append("📢 بث جماعي")
                    if c_feed: perms_list.append("📥 رسائل الأعضاء")
                    if c_cnt: perms_list.append("📊 إحصائيات")
                    
                    text += f"👤 ID: `{adm_id}`\nالصلاحيات: {', '.join(perms_list) if perms_list else 'لا توجد'}\n\n"
                    
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=make_owner_manage_admins_markup()
            )
            bot.answer_callback_query(call.id)
            return

        # الضغط على إضافة مشرف
        if data_call == "owner_add_admin":
            set_user_state(user_id, "WAITING_NEW_ADMIN_ID")
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="✍️ حسناً، أرسل الآن الـ ID الرقمي للمشرف الجديد الذي ترغب في إضافته:"
            )
            bot.answer_callback_query(call.id)
            return

        # استعراض المشرفين لحذفهم
        if data_call == "owner_remove_admin_list":
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="🗑️ اختر المشرف الذي ترغب في حذفه تماماً وسحب صلاحياته:",
                reply_markup=make_remove_admin_list_markup()
            )
            bot.answer_callback_query(call.id)
            return

        # تأكيد حذف مشرف
        if data_call.startswith("exec_remove_admin_"):
            target_id = int(data_call.split("_")[3])
            execute_query("DELETE FROM admins WHERE admin_id = %s;", (target_id,), commit=True)
            bot.answer_callback_query(call.id, "✅ تم إزالة المشرف وسحب جميع صلاحياته بنجاح!", show_alert=True)
            
            # تحديث القائمة فوراً وعرضها
            clear_user_state(user_id)
            admins = execute_query("SELECT admin_id, can_settings, can_broadcast, can_feedback, can_count FROM admins;", fetch=True)
            text = "👥 **قائمة المشرفين الحاليين وصلاحياتهم:**\n\n"
            if not admins:
                text += "⚠️ لا يوجد أي مشرف مضاف حالياً."
            else:
                for adm_id, c_set, c_broad, c_feed, c_cnt in admins:
                    perms_list = []
                    if c_set: perms_list.append("⚙️ إعدادات")
                    if c_broad: perms_list.append("📢 بث جماعي")
                    if c_feed: perms_list.append("📥 رسائل الأعضاء")
                    if c_cnt: perms_list.append("📊 إحصائيات")
                    text += f"👤 ID: `{adm_id}`\nالصلاحيات: {', '.join(perms_list) if perms_list else 'لا توجد'}\n\n"
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=make_owner_manage_admins_markup()
            )
            return

        # التحكم بصناديق الاختيار (تفعيل الصلاحيات أو حفظ المشرف الجديد)
        if data_call.startswith("toggle_") or data_call.startswith("save_admin_"):
            parts = data_call.split("_")
            action = parts[0]
            
            if action == "toggle":
                perm_type = parts[1]
                target_admin_id = int(parts[2])
                
                state, state_data = get_user_state(user_id)
                if state == "CHOOSING_ADMIN_PERMISSIONS" and state_data.get('new_admin_id') == target_admin_id:
                    perms_dict = state_data.get('perms', {})
                    
                    if perm_type == "all":
                        perms_dict = {k: True for k in perms_dict}
                    else:
                        perms_dict[perm_type] = not perms_dict.get(perm_type, False)
                        
                    set_user_state(user_id, "CHOOSING_ADMIN_PERMISSIONS", {"new_admin_id": target_admin_id, "perms": perms_dict})
                    bot.edit_message_reply_markup(
                        chat_id=user_id,
                        message_id=call.message.message_id,
                        reply_markup=make_permissions_markup(perms_dict, target_admin_id)
                    )
                bot.answer_callback_query(call.id)
                return
                
            elif action == "save":
                target_admin_id = int(parts[2])
                state, state_data = get_user_state(user_id)
                if state == "CHOOSING_ADMIN_PERMISSIONS" and state_data.get('new_admin_id') == target_admin_id:
                    perms_dict = state_data.get('perms', {})
                    
                    # شرط الأمان: اختيار صلاحية واحدة على الأقل
                    if not any(perms_dict.values()):
                        bot.answer_callback_query(call.id, "⚠️ يجب اختيار صلاحية واحدة على الأقل للمشرف الجديد!", show_alert=True)
                        return
                        
                    execute_query('''
                        INSERT INTO admins (admin_id, can_settings, can_broadcast, can_feedback, can_count)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (admin_id)
                        DO UPDATE SET 
                            can_settings = EXCLUDED.can_settings,
                            can_broadcast = EXCLUDED.can_broadcast,
                            can_feedback = EXCLUDED.can_feedback,
                            can_count = EXCLUDED.can_count;
                    ''', (target_admin_id, perms_dict['settings'], perms_dict['broadcast'], perms_dict['feedback'], perms_dict['count']), commit=True)
                    
                    clear_user_state(user_id)
                    bot.answer_callback_query(call.id, "✅ تم حفظ المشرف الجديد وتفعيل صلاحياته بنجاح!", show_alert=True)
                    
                    # تحديث القائمة فوراً وعرضها للمالك
                    admins = execute_query("SELECT admin_id, can_settings, can_broadcast, can_feedback, can_count FROM admins;", fetch=True)
                    text = "👥 **قائمة المشرفين الحاليين وصلاحياتهم:**\n\n"
                    if not admins:
                        text += "⚠️ لا يوجد أي مشرف مضاف حالياً."
                    else:
                        for adm_id, c_set, c_broad, c_feed, c_cnt in admins:
                            perms_list = []
                            if c_set: perms_list.append("⚙️ إعدادات")
                            if c_broad: perms_list.append("📢 بث جماعي")
                            if c_feed: perms_list.append("📥 رسائل الأعضاء")
                            if c_cnt: perms_list.append("📊 إحصائيات")
                            text += f"👤 ID: `{adm_id}`\nالصلاحيات: {', '.join(perms_list) if perms_list else 'لا توجد'}\n\n"
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=call.message.message_id,
                        text=text,
                        parse_mode="Markdown",
                        reply_markup=make_owner_manage_admins_markup()
                    )
                return

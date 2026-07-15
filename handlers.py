from config import bot, ADMIN_IDS
from database import (
    execute_query, execute_query_dict, 
    set_user_state, get_user_state, clear_user_state
)
from keyboards import (
    make_main_menu_markup, make_sub_menu_markup, 
    make_admin_settings_markup, make_admin_edit_options_markup,
    make_admin_choose_parent_markup, make_admin_move_button_markup,
    make_admin_file_manager_markup
)
import telebot

def is_admin(user_id):
    return user_id in ADMIN_IDS

def register_handlers():
    
    # ==========================================
    # 1. Start Command & Main Menu
    # ==========================================
    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        user_id = message.from_user.id
        username = message.from_user.username or "NoUsername"
        
        # تسجيل المستخدم في قاعدة البيانات إن لم يكن مسجلاً
        execute_query(
            "INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username;",
            (user_id, username), commit=True
        )
        
        clear_user_state(user_id)
        
        welcome_text = (
            "👋 أهلاً بك في البوت الطبي التعليمي.\n\n"
            "الرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات والمحاضرات الطبية بسهولة 👇"
        )
        bot.send_message(user_id, welcome_text, reply_markup=make_main_menu_markup(is_admin(user_id)))

    # ==========================================
    # 2. Master Text & Document Handler (FSM)
    # ==========================================
    @bot.message_handler(content_types=['text', 'document', 'photo', 'audio', 'video', 'voice'])
    def handle_all_messages(message):
        user_id = message.from_user.id
        state, data = get_user_state(user_id)
        
        if not state:
            # إذا لم يكن هناك حالة نشطة، ولم يكن المشرف يستعمل الأوامر
            if is_admin(user_id):
                bot.send_message(user_id, "⚠️ لم أفهم هذا الأمر. الرجاء استخدام أزرار لوحة التحكم أو كتابة /start للبدء.")
            else:
                bot.send_message(user_id, "⚠️ الرجاء استخدام أزرار القائمة للتنقل. إذا واجهت مشكلة اضغط /start أو انقر على زر 'مراسلة الإدارة'.")
            return

        # --- أ) معالجات المستخدم العادي ---
        
        # 1. معالجة إرسال رسالة تواصل للمشرف
        if state == "WAITING_FEEDBACK_MSG":
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ عذراً، يجب إرسال رسالة نصية فقط للمشرفين.")
                return
            
            # حفظ الشكوى في قاعدة البيانات
            username = message.from_user.username or "NoUsername"
            execute_query(
                "INSERT INTO feedback (user_id, username, message_text) VALUES (%s, %s, %s);",
                (user_id, username, message.text), commit=True
            )
            
            clear_user_state(user_id)
            bot.send_message(user_id, "✅ تم إرسال رسالتك بنجاح إلى المشرفين. سيتم الرد عليك قريباً! 🥰", reply_markup=make_main_menu_markup(False))
            
            # إشعار كافة المشرفين بالرسالة الجديدة
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, f"📬 رسالة جديدة من المستخدم @{username} ({user_id}):\n\n📄 {message.text}")
                except Exception:
                    pass
            return

        # --- ب) معالجات المشرف (Admin) ---
        if not is_admin(user_id):
            clear_user_state(user_id)
            return

        # 2. معالجة إرسال الإرسال الجماعي (Broadcast)
        if state == "WAITING_BROADCAST_MSG":
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
            bot.send_message(user_id, f"✅ تم إرسال الإعلان الجماعي بنجاح إلى {success_count} مستخدم من أصل {len(all_users)}.", reply_markup=make_main_menu_markup(True))
            return

        # 3. معالجة رد المشرف على رسالة مستخدم
        if state == "WAITING_ADMIN_REPLY":
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ الرجاء كتابة رد نصي فقط.")
                return
            
            target_user_id = data.get('target_user_id')
            fb_id = data.get('fb_id')
            
            try:
                bot.send_message(target_user_id, f"💬 رد من الإدارة على استفسارك:\n\n{message.text}")
                execute_query("UPDATE feedback SET status = 'replied' WHERE id = %s;", (fb_id,), commit=True)
                bot.send_message(user_id, "✅ تم إرسال الرد بنجاح للمستخدم!", reply_markup=make_main_menu_markup(True))
            except Exception as e:
                bot.send_message(user_id, f"❌ فشل إرسال الرد للمستخدم. ربما قام بحظر البوت. الخطأ: {str(e)}")
            
            clear_user_state(user_id)
            return

        # 4. معالجة إدخال اسم الزر الجديد
        if state == "WAITING_BTN_NAME":
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

        # 5. معالجة إدخال نص رسالة الزر (بعد الإنشاء)
        if state == "WAITING_BTN_TEXT":
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

        # 6. معالجة تعديل اسم الزر
        if state == "WAITING_EDIT_NAME":
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ الاسم الجديد يجب أن يكون نصاً:")
                return
            
            btn_id = data.get('button_id')
            new_name = message.text.strip()
            
            execute_query("UPDATE buttons SET name = %s WHERE id = %s;", (new_name, btn_id), commit=True)
            clear_user_state(user_id)
            bot.send_message(user_id, "✅ تم تعديل اسم الزر بنجاح!", reply_markup=make_admin_edit_options_markup(btn_id))
            return

        # 7. معالجة تعديل رسالة الزر
        if state == "WAITING_EDIT_TEXT":
            if message.content_type != 'text':
                bot.send_message(user_id, "❌ الرسالة يجب أن تكون نصاً:")
                return
            
            btn_id = data.get('button_id')
            new_text = message.text
            
            execute_query("UPDATE buttons SET message_text = %s WHERE id = %s;", (new_text, btn_id), commit=True)
            clear_user_state(user_id)
            bot.send_message(user_id, "✅ تم تعديل الرسالة النصية للزر بنجاح!", reply_markup=make_admin_edit_options_markup(btn_id))
            return

        # 8. معالجة استقبال الملفات لربطها بالزر
        if state == "WAITING_ADD_FILE":
            btn_id = data.get('button_id')
            file_id = None
            file_type = None
            
            if message.content_type == 'document':
                file_id = message.document.file_id
                file_type = 'document'
            elif message.content_type == 'photo':
                # نأخذ أعلى جودة للصورة المرسلة
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
                bot.send_message(user_id, "❌ لم يتم التعرف على نوع الملف المرسل. الرجاء إرسال (ملف، صورة، مقطع صوتي، فيديو، أو بصمة صوتية):")
                return
                
            # حفظ معرف الملف في قاعدة البيانات
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


    # ==========================================
    # 3. Inline Query Callback Handlers
    # ==========================================
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        user_id = call.from_user.id
        data_call = call.data
        
        # أ) التنقل في القائمة الرئيسية
        if data_call == "main_menu":
            clear_user_state(user_id)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="👋 أهلاً بك في البوت الطبي التعليمي.\n\nالرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات الطبية 👇",
                reply_markup=make_main_menu_markup(is_admin(user_id))
            )
            bot.answer_callback_query(call.id)
            return

        # ب) فتح مجلد أو زر معين (متاح للجميع)
        if data_call.startswith("open_"):
            parts = data_call.split("_")
            # إذا كان "open_None" أو لا يوجد رقم، نرجع للقائمة الرئيسية
            if len(parts) < 2 or parts[1] == "None" or parts[1] == "null":
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    text="👋 أهلاً بك في البوت الطبي التعليمي.\n\nالرجاء استخدام الأزرار أدناه للتنقل وتصفح الملفات الطبية 👇",
                    reply_markup=make_main_menu_markup(is_admin(user_id))
                )
                bot.answer_callback_query(call.id)
                return
                
            btn_id = int(parts[1])
            
            # جلب معلومات الزر من قاعدة البيانات
            btn_info = execute_query("SELECT name, message_text FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
            if not btn_info:
                bot.answer_callback_query(call.id, "⚠️ هذا المجلد أو الزر لم يعد موجوداً!")
                return
            
            btn_name, msg_text = btn_info[0]
            
            # جلب الأزرار الفرعية تحت هذا الزر
            sub_count = execute_query("SELECT COUNT(*) FROM buttons WHERE parent_id = %s;", (btn_id,), fetch=True)[0][0]
            
            # 1. إرسال أو تعديل الواجهة
            display_text = f"📂 القسم: {btn_name}"
            if msg_text:
                display_text += f"\n\n📄 {msg_text}"
                
            # تعديل الرسالة وإظهار الأزرار الفرعية
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=display_text,
                reply_markup=make_sub_menu_markup(btn_id, is_admin(user_id))
            )
            
            # 2. إرسال الملفات المربوطة بهذا الزر (إن وجدت)
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

        # ج) مراسلة الإدارة للمستخدمين العاديين
        if data_call == "user_contact":
            set_user_state(user_id, "WAITING_FEEDBACK_MSG")
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📝 اكتب رسالتك أو استفسارك هنا وسنقوم بإيصالها للمشرفين فوراً للرد عليك:\n\n(ملاحظة: اضغط /start لإلغاء المراسلة والعودة)"
            )
            bot.answer_callback_query(call.id)
            return

        # --- د) كافة الأوامم الإدارية التالية خاصة بالمشرفين فقط ---
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ عذراً، هذا الخيار مخصص للمشرفين فقط.", show_alert=True)
            return

        # فتح لوحة الإعدادات
        if data_call == "admin_settings":
            clear_user_state(user_id)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="⚙️ مرحباً بك في لوحة تحكم المشرف.\n\nالرجاء تحديد الإجراء الذي ترغب في القيام به:",
                reply_markup=make_admin_settings_markup()
            )
            bot.answer_callback_query(call.id)
            return

        # إرسال رسالة جماعية
        if data_call == "admin_broadcast":
            set_user_state(user_id, "WAITING_BROADCAST_MSG")
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📢 أرسل الآن الرسالة النصية التي تريد نشرها لكافة مستخدمي البوت:\n\n(اضغط /start للإلغاء)"
            )
            bot.answer_callback_query(call.id)
            return

        # عدد مستخدمي البوت
        if data_call == "admin_count_users":
            count = execute_query("SELECT COUNT(*) FROM users;", fetch=True)[0][0]
            bot.answer_callback_query(call.id, f"📊 إجمالي عدد المشتركين في البوت: {count} مستخدم.", show_alert=True)
            return

        # عرض رسائل واستفسارات المستخدمين المعلقة
        if data_call == "admin_view_feedback":
            feedbacks = execute_query_dict("SELECT id, user_id, username, message_text FROM feedback WHERE status = 'pending' ORDER BY id DESC LIMIT 5;")
            if not feedbacks:
                bot.answer_callback_query(call.id, "📥 لا توجد رسائل معلقة حالياً من المستخدمين! كل شيء هادئ.", show_alert=True)
                return
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📥 إليك آخر 5 رسائل واردة ومعلقة من الأعضاء:",
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

        # النقر على الرد على رسالة مستخدم
        if data_call.startswith("replyfb_"):
            parts = data_call.split("_")
            fb_id = int(parts[1])
            target_user_id = int(parts[2])
            
            set_user_state(user_id, "WAITING_ADMIN_REPLY", {"target_user_id": target_user_id, "fb_id": fb_id})
            bot.send_message(user_id, "✍️ اكتب ردك الآن ليتم إرساله فوراً للمستخدم:")
            bot.answer_callback_query(call.id)
            return

        # إضافة زر جديد
        if data_call == "adm_add_btn":
            set_user_state(user_id, "WAITING_BTN_NAME")
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="✍️ حسناً، أرسل الآن اسم الزر الجديد الذي تريد إنشاءه:"
            )
            bot.answer_callback_query(call.id)
            return

        # تحديد موقع الزر الجديد في الشجرة وحفظه
        if data_call.startswith("setparent_new_"):
            parts = data_call.split("_")
            btn_name = parts[2]
            parent_raw = parts[3]
            
            parent_id = None if parent_raw == "null" else int(parent_raw)
            
            # إدراج الزر الجديد في قاعدة البيانات
            res = execute_query(
                "INSERT INTO buttons (name, parent_id) VALUES (%s, %s) RETURNING id;",
                (btn_name, parent_id), fetch=True, commit=True
            )
            new_btn_id = res[0][0]
            
            # الطلب من الآدمن كتابة رسالة توضيحية للزر
            set_user_state(user_id, "WAITING_BTN_TEXT", {"button_id": new_btn_id})
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=f"✅ تم إنشاء زر [ {btn_name} ] بنجاح!\n\n✍️ أرسل الآن الرسالة النصية التوضيحية التي ستظهر للمستخدم عند نقر هذا الزر:"
            )
            bot.answer_callback_query(call.id)
            return

        # حذف زر
        if data_call == "adm_del_btn":
            buttons = execute_query("SELECT id, name FROM buttons ORDER BY id ASC;", fetch=True)
            if not buttons:
                bot.answer_callback_query(call.id, "⚠️ لا توجد أي أزرار مضافة حالياً لحذفها!", show_alert=True)
                return
            
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            for b_id, b_name in buttons:
                markup.add(telebot.types.InlineKeyboardButton(text=f"🗑 حذف: {b_name}", callback_data=f"confirm_del_{b_id}"))
            markup.add(telebot.types.InlineKeyboardButton(text="🔙 إلغاء", callback_data="admin_settings"))
            
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="❌ حدد الزر الذي ترغب بحذفه نهائياً (ملاحظة: سيؤدي هذا إلى حذف كافة الملفات والأزرار الفرعية بداخله تلقائياً):",
                reply_markup=markup
            )
            bot.answer_callback_query(call.id)
            return

        # تأكيد الحذف النهائي للزر
        if data_call.startswith("confirm_del_"):
            btn_id = int(data_call.split("_")[2])
            execute_query("DELETE FROM buttons WHERE id = %s;", (btn_id,), commit=True)
            
            bot.answer_callback_query(call.id, "✅ تم حذف الزر وكافة تفاصيله وفروعه نهائياً من السيستم!", show_alert=True)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="⚙️ تم التحديث بنجاح! اختر إجراءً آخر من لوحة التحكم:",
                reply_markup=make_admin_settings_markup()
            )
            return

        # تعديل زر (اختيار الزر للتعديل)
        if data_call == "adm_edit_btn":
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
                text="✏️ اختر الزر الذي ترغب بتعديل خصائصه وملفاته وموقعه:",
                reply_markup=markup
            )
            bot.answer_callback_query(call.id)
            return

        # استعراض خيارات تعديل زر معين
        if data_call.startswith("choose_edit_"):
            btn_id = int(data_call.split("_")[2])
            btn_info = execute_query("SELECT name FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
            if not btn_info:
                bot.answer_callback_query(call.id, "⚠️ هذا الزر غير متوفر!")
                return
                
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text=f"🛠 تعديل خصائص الزر: [ {btn_info[0][0]} ]\n\nاختر الحقل الذي تود العمل عليه:",
                reply_markup=make_admin_edit_options_markup(btn_id)
            )
            bot.answer_callback_query(call.id)
            return

        # طلب تعديل الاسم للزر
        if data_call.startswith("editopt_name_"):
            btn_id = int(data_call.split("_")[2])
            set_user_state(user_id, "WAITING_EDIT_NAME", {"button_id": btn_id})
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="✍️ حسناً، أرسل الاسم الجديد للزر الآن:"
            )
            bot.answer_callback_query(call.id)
            return

        # طلب تعديل الرسالة للزر
        if data_call.startswith("editopt_msg_"):
            btn_id = int(data_call.split("_")[2])
            set_user_state(user_id, "WAITING_EDIT_TEXT", {"button_id": btn_id})
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="✍️ حسناً، أرسل الرسالة التوضيحية الجديدة للزر الآن:"
            )
            bot.answer_callback_query(call.id)
            return

        # طلب نقل الزر لمكان آخر (تعديل الأب)
        if data_call.startswith("editopt_move_"):
            btn_id = int(data_call.split("_")[2])
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="🔄 اختر المجلد الجديد الذي ترغب بنقل هذا الزر إليه:",
                reply_markup=make_admin_move_button_markup(btn_id)
            )
            bot.answer_callback_query(call.id)
            return

        # تنفيذ عملية النقل فعلياً
        if data_call.startswith("exec_move_"):
            parts = data_call.split("_")
            btn_id = int(parts[2])
            parent_raw = parts[3]
            
            parent_id = None if parent_raw == "null" else int(parent_raw)
            execute_query("UPDATE buttons SET parent_id = %s WHERE id = %s;", (parent_id, btn_id), commit=True)
            
            bot.answer_callback_query(call.id, "✅ تم نقل الزر بنجاح وتحديث الشجرة الهيكلية!", show_alert=True)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="🛠 تم تحديث موضع الزر بنجاح. ما الذي ترغب بفعله الآن؟",
                reply_markup=make_admin_edit_options_markup(btn_id)
            )
            return

        # فتح لوحة إدارة الملفات المربوطة بالزر
        if data_call.startswith("editopt_files_"):
            btn_id = int(data_call.split("_")[2])
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📁 قائمة الملفات المربوطة بهذا الزر حالياً. يمكنك إضافة المزيد أو حذف الملفات القديمة:",
                reply_markup=make_admin_file_manager_markup(btn_id)
            )
            bot.answer_callback_query(call.id)
            return

        # طلب رفع ملف جديد للزر
        if data_call.startswith("addfile_"):
            btn_id = int(data_call.split("_")[1])
            set_user_state(user_id, "WAITING_ADD_FILE", {"button_id": btn_id})
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📤 أرسل الآن الملف الذي تريد ربطه بالزر (مستند PDF، صورة، فيديو، ملف صوتي، إلخ):\n\n(سيقوم البوت بحفظه وتمريره ديناميكياً للطلاب)"
            )
            bot.answer_callback_query(call.id)
            return

        # حذف ملف مربوط بزر
        if data_call.startswith("delfile_"):
            parts = data_call.split("_")
            file_record_id = int(parts[1])
            btn_id = int(parts[2])
            
            execute_query("DELETE FROM button_files WHERE id = %s;", (file_record_id,), commit=True)
            bot.answer_callback_query(call.id, "✅ تم حذف الملف بنجاح من قاعدة البيانات!", show_alert=True)
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📁 تم تحديث الملفات بنجاح. يمكنك إضافة ملفات أخرى أو العودة:",
                reply_markup=make_admin_file_manager_markup(btn_id)
            )
            return

print("DEBUG: الملف admin.py تم تحميله بنجاح مع دعم التنسيق الشبكي الكامل")

import telebot
from config import bot, ADMIN_IDS, OWNER_ID
from database import execute_query, execute_query_dict, set_user_state, get_user_state, clear_user_state
from keyboards import (
    make_admin_settings_markup, make_admin_edit_options_markup,
    make_admin_choose_parent_markup, make_admin_move_button_markup,
    make_admin_file_manager_markup, make_main_menu_markup
)
from handlers.helpers import get_permissions, check_state

# دالة مساعدة لحقن أزرار التنسيق الشبكي ديناميكياً والحفاظ على زر العودة بالأسفل دائماً
def get_edit_markup(btn_id):
    markup = make_admin_edit_options_markup(btn_id)
    layout_row = [
        telebot.types.InlineKeyboardButton(text="📐 تعديل السطر", callback_data=f"editopt_row_{btn_id}"),
        telebot.types.InlineKeyboardButton(text="↔️ تعديل الترتيب", callback_data=f"editopt_sort_{btn_id}")
    ]
    # إدراج أزرار التحكم بالشبكة فوق زر العودة للخلف مباشرة
    if len(markup.keyboard) >= 1:
        markup.keyboard.insert(-1, layout_row)
    else:
        markup.row(*layout_row)
    return markup

# دالة مساعدة لفحص الحقوق ديناميكياً وعرض رسائل تنبيهية عند الرفض
def is_admin_or_alert(call, perms, perm_type='can_settings'):
    if not perms[perm_type]:
        bot.answer_callback_query(call.id, "❌ عذراً، لا تملك الصلاحية اللازمة للقيام بهذا الإجراء.", show_alert=True)
        return False
    return True

def register_admin_handlers():
    
    # لوحة الإدارة الرئيسية
    @bot.callback_query_handler(func=lambda call: call.data == "admin_settings")
    def cb_admin_settings(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        clear_user_state(user_id)
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="⚙️ مرحباً بك في لوحة تحكم المشرف.\n\nالرجاء تحديد الإجراء الذي ترغب في القيام به:",
            reply_markup=make_admin_settings_markup()
        )
        bot.answer_callback_query(call.id)

    # ==========================================
    # البث الجماعي للطلاب (مع ميزة الإلغاء)
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
    def cb_admin_broadcast_init(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_broadcast'): return
        
        set_user_state(user_id, "WAITING_BROADCAST_MSG")
        
        cancel_markup = telebot.types.InlineKeyboardMarkup()
        cancel_markup.add(telebot.types.InlineKeyboardButton(text="❌ إلغاء العملية", callback_data="cancel_broadcast"))
        
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="📢 أرسل الآن الرسالة النصية التي تريد نشرها لكافة مستخدمي البوت👇:",
            reply_markup=cancel_markup
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_broadcast")
    def cb_cancel_broadcast(call):
        user_id = call.from_user.id
        clear_user_state(user_id)
        bot.answer_callback_query(call.id, "💥 تم إلغاء الإرسال الجماعي.", show_alert=False)
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="⚙️ مرحباً بك في لوحة تحكم المشرف.\n\nالرجاء تحديد الإجراء الذي ترغب في القيام به:",
            reply_markup=make_admin_settings_markup()
        )

    @bot.message_handler(func=check_state("WAITING_BROADCAST_MSG"), content_types=['text'])
    def process_broadcast_message(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_broadcast']:
            clear_user_state(user_id)
            return
            
        all_users = execute_query("SELECT user_id FROM users;", fetch=True)
        success_count = 0
        for u_id_tuple in all_users:
            u_id = u_id_tuple[0]
            try:
                bot.send_message(u_id, f"📢 إعلان هام من الإدارة:\n\n{message.text}")
                success_count += 1
            except Exception: pass
            
        clear_user_state(user_id)
        bot.send_message(user_id, f"✅ تم إرسال الإعلان الجماعي بنجاح إلى {success_count} مستخدم.", reply_markup=make_main_menu_markup(perms, user_id))
        
    # عرض عدد المستخدمين
    @bot.callback_query_handler(func=lambda call: call.data == "admin_count_users")
    def cb_count_users(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_count'): return
        count = execute_query("SELECT COUNT(*) FROM users;", fetch=True)[0][0]
        bot.answer_callback_query(call.id, f"📊 إجمالي عدد المشتركين في البوت: {count} مستخدم.", show_alert=True)

    # إدارة صندوق وارد الاستفسارات والرد عليها
    @bot.callback_query_handler(func=lambda call: call.data == "admin_view_feedback")
    def cb_view_feedbacks(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_feedback'): return
        
        feedbacks = execute_query_dict("SELECT id, user_id, username, message_text FROM feedback WHERE status = 'pending' ORDER BY id DESC;")
        
        if not feedbacks:
            bot.answer_callback_query(call.id, "📥 لا توجد رسائل معلقة حالياً!", show_alert=True)
            return

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="main_menu"))
        
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text=f"📥 إليك جميع الرسائل المعلقة ({len(feedbacks)} رسالة):",
            reply_markup=markup
        )
        
        for fb in feedbacks:
            reply_markup = telebot.types.InlineKeyboardMarkup()
            reply_markup.add(
                telebot.types.InlineKeyboardButton(text="💬 الرد", callback_data=f"replyfb_{fb['id']}_{fb['user_id']}"),
                telebot.types.InlineKeyboardButton(text="🗑 حذف", callback_data=f"delfb_{fb['id']}")
            )
            bot.send_message(
                user_id,
                f"👤 العضو: @{fb['username']} ({fb['user_id']})\n\n📄 الرسالة:\n{fb['message_text']}",
                reply_markup=reply_markup
            )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delfb_"))
    def cb_delete_feedback(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_feedback'): return
        
        fb_id = int(call.data.split("_")[1])
        execute_query("UPDATE feedback SET status = 'deleted' WHERE id = %s;", (fb_id,), commit=True)
        
        bot.answer_callback_query(call.id, "✅ تم حذف الرسالة بنجاح.", show_alert=True)
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith("replyfb_"))
    def cb_reply_feedback_init(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_feedback'): return
        parts = call.data.split("_")
        fb_id = int(parts[1])
        target_user_id = int(parts[2])
        set_user_state(user_id, "WAITING_ADMIN_REPLY", {"target_user_id": target_user_id, "fb_id": fb_id})
        bot.send_message(user_id, "✍️ اكتب ردك الآن ليتم إرساله فوراً للمستخدم:")
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_ADMIN_REPLY"), content_types=['text'])
    def process_admin_reply(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_feedback']:
            clear_user_state(user_id)
            return
        state, data = get_user_state(user_id)
        target_user_id = data.get('target_user_id')
        fb_id = data.get('fb_id')
        try:
            bot.send_message(target_user_id, f"💬 رد من الإدارة على استفسارك:\n\n{message.text}")
            execute_query("UPDATE feedback SET status = 'replied' WHERE id = %s;", (fb_id,), commit=True)
            bot.send_message(user_id, "✅ تم إرسال الرد بنجاح للمستخدم!", reply_markup=make_main_menu_markup(perms, user_id))
        except Exception as e:
            bot.send_message(user_id, f"❌ فشل إرسال الرد للمستخدم. الخطأ: {str(e)}")
        clear_user_state(user_id)

    # ==========================================
    # شجرة وهيكلة الأزرار (إضافة زر بتنسيق شبكي)
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data == "adm_add_btn")
    def cb_add_button_init(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        set_user_state(user_id, "WAITING_BTN_NAME")
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="✍️ حسناً، أرسل الآن اسم الزر الجديد الذي تريد إنشاءه:"
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_BTN_NAME"), content_types=['text'])
    def process_btn_name(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_settings']:
            clear_user_state(user_id)
            return
        btn_name = message.text.strip()
        clear_user_state(user_id)
        bot.send_message(
            user_id, f"📂 حدد موقع الزر الجديد [ {btn_name} ] في الشجرة الهيكلية:",
            reply_markup=make_admin_choose_parent_markup(btn_name)
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("setparent_new_"))
    def cb_set_parent_new(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        parts = call.data.split("_")
        btn_name = parts[2]
        parent_raw = parts[3]
        parent_id = None if parent_raw == "null" else int(parent_raw)
        
        # تخزين البيانات مؤقتاً والانتقال لطلب رقم السطر
        set_user_state(user_id, "WAITING_BTN_ROW", {"btn_name": btn_name, "parent_id": parent_id})
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text=f"📐 ممتاز! الآن أرسل **رقم السطر** الذي تريد ظهور زر [ {btn_name} ] فيه:\n(مثال: أدخل 1 ليكون بالسطر الأول فوق، أو 3 ليكون بالسطر الثالث...)"
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_BTN_ROW"), content_types=['text'])
    def process_btn_row(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_settings']:
            clear_user_state(user_id)
            return
        if not message.text.strip().isdigit():
            bot.send_message(user_id, "❌ الرجاء إدخال رقم صحيح فقط لرقم السطر:")
            return
        
        row_num = int(message.text.strip())
        state, data = get_user_state(user_id)
        data["row_number"] = row_num
        
        set_user_state(user_id, "WAITING_BTN_SORT", data)
        bot.send_message(
            user_id, f"↔️ رائع! الآن أرسل **الترتيب الأفقي** للزر داخل السطر {row_num}:\n(مثال: أدخل 1 ليكون الأول من اليسار، 2 ليكون بجانبه، وهكذا...)"
        )

    @bot.message_handler(func=check_state("WAITING_BTN_SORT"), content_types=['text'])
    def process_btn_sort(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_settings']:
            clear_user_state(user_id)
            return
        if not message.text.strip().isdigit():
            bot.send_message(user_id, "❌ الرجاء إدخال رقم صحيح فقط للترتيب الأفقي:")
            return
            
        sort_ord = int(message.text.strip())
        state, data = get_user_state(user_id)
        
        btn_name = data.get("btn_name")
        parent_id = data.get("parent_id")
        row_num = data.get("row_number")
        
        # حفظ الزر الجديد بالكامل في قاعدة البيانات مع موقعه الشبكي المخصص
        res = execute_query(
            "INSERT INTO buttons (name, parent_id, row_number, sort_order) VALUES (%s, %s, %s, %s) RETURNING id;",
            (btn_name, parent_id, row_num, sort_ord), fetch=True, commit=True
        )
        new_btn_id = res[0][0]
        
        set_user_state(user_id, "WAITING_BTN_TEXT", {"button_id": new_btn_id})
        bot.send_message(
            user_id, f"✅ تم تثبيت الزر وإعداد موقعه بنجاح!\n\n✍️ أرسل الآن الرسالة النصية التوضيحية له:"
        )

    @bot.message_handler(func=check_state("WAITING_BTN_TEXT"), content_types=['text'])
    def process_btn_text(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_settings']:
            clear_user_state(user_id)
            return
        state, data = get_user_state(user_id)
        btn_id = data.get('button_id')
        execute_query("UPDATE buttons SET message_text = %s WHERE id = %s;", (message.text, btn_id), commit=True)
        clear_user_state(user_id)
        bot.send_message(
            user_id, "✅ تم حفظ الرسالة النصية للزر بنجاح! يمكنك الآن إدارة الملفات المربوطة به أو تعديل تنسيقه.",
            reply_markup=get_edit_markup(btn_id)
        )

    # تعديل الأزرار وحذفها ونقلها وإدارة ملفاتها
    @bot.callback_query_handler(func=lambda call: call.data == "adm_edit_btn")
    def cb_edit_list(call):
        print(f"DEBUG: cb_edit_list triggered with data: {call.data}")
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        buttons = execute_query("SELECT id, name FROM buttons ORDER BY id ASC;", fetch=True)
        if not buttons:
            bot.answer_callback_query(call.id, "⚠️ لا توجد أزرار مضافة لتعديلها حالياً!", show_alert=True)
            return
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for b_id, b_name in buttons:
            markup.add(telebot.types.InlineKeyboardButton(text=f"✏️ تعديل: {b_name}", callback_data=f"choose_edit_{b_id}"))
        markup.add(telebot.types.InlineKeyboardButton(text="🔙 العودة للإعدادات", callback_data="admin_settings"))
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="✏️ اختر الزر الذي ترغب بتعديله:", reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "adm_del_btn")
    def cb_delete_list(call):
        print(f"DEBUG: cb_delete_list triggered with data: {call.data}")
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        buttons = execute_query("SELECT id, name FROM buttons ORDER BY id ASC;", fetch=True)
        if not buttons:
            bot.answer_callback_query(call.id, "⚠️ لا توجد أزرار مضافة لحذفها حالياً!", show_alert=True)
            return
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for b_id, b_name in buttons:
            markup.add(telebot.types.InlineKeyboardButton(text=f"🗑️ حذف: {b_name}", callback_data=f"exec_del_btn_{b_id}"))
        markup.add(telebot.types.InlineKeyboardButton(text="🔙 العودة للإعدادات", callback_data="admin_settings"))
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="❌ اختر الزر الذي ترغب في حذفه تماماً (سيتم حذف تفريعاته وملفاته تلقائياً):",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("exec_del_btn_"))
    def cb_execute_del_btn(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        btn_id = int(call.data.split("_")[3])
        btn_info = execute_query("SELECT name FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
        if not btn_info:
            bot.answer_callback_query(call.id, "⚠️ هذا الزر غير موجود بالفعل!")
            return
        btn_name = btn_info[0][0]
        execute_query("DELETE FROM buttons WHERE id = %s;", (btn_id,), commit=True)
        bot.answer_callback_query(call.id, f"✅ تم حذف الزر [ {btn_name} ] بنجاح!", show_alert=True)
        
        buttons = execute_query("SELECT id, name FROM buttons ORDER BY id ASC;", fetch=True)
        if not buttons:
            bot.edit_message_text(
                chat_id=user_id, message_id=call.message.message_id,
                text="⚙️ لوحة الإعدادات الإدارية خالية من الأزرار حالياً.",
                reply_markup=make_admin_settings_markup()
            )
            return
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for b_id, b_name in buttons:
            markup.add(telebot.types.InlineKeyboardButton(text=f"🗑️ حذف: {b_name}", callback_data=f"exec_del_btn_{b_id}"))
        markup.add(telebot.types.InlineKeyboardButton(text="🔙 العودة للإعدادات", callback_data="admin_settings"))
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="❌ اختر الزر الذي ترغب في حذفه تماماً (سيتم حذف تفريعاته وملفاته تلقائياً):",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("choose_edit_"))
    def cb_choose_edit(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        btn_id = int(call.data.split("_")[2])
        btn_info = execute_query("SELECT name, row_number, sort_order FROM buttons WHERE id = %s;", (btn_id,), fetch=True)
        if not btn_info:
            bot.answer_callback_query(call.id, "⚠️ هذا الزر غير متوفر!")
            return
        name, row_num, sort_ord = btn_info[0]
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text=f"🛠 تعديل خصائص الزر: [ {name} ]\n📌 الموضع الشبكي الحالي: السطر {row_num} | الترتيب الأفقي {sort_ord}",
            reply_markup=get_edit_markup(btn_id)
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("editopt_name_"))
    def cb_edit_name_init(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        btn_id = int(call.data.split("_")[2])
        set_user_state(user_id, "WAITING_EDIT_NAME", {"button_id": btn_id})
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="✍️ أرسل الاسم الجديد للزر الآن:"
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_EDIT_NAME"), content_types=['text'])
    def process_edit_name(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_settings']:
            clear_user_state(user_id)
            return
        state, data = get_user_state(user_id)
        btn_id = data.get('button_id')
        new_name = message.text.strip()
        execute_query("UPDATE buttons SET name = %s WHERE id = %s;", (new_name, btn_id), commit=True)
        clear_user_state(user_id)
        bot.send_message(user_id, "✅ تم تعديل اسم الزر بنجاح!", reply_markup=get_edit_markup(btn_id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("editopt_msg_"))
    def cb_edit_msg_init(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        btn_id = int(call.data.split("_")[2])
        set_user_state(user_id, "WAITING_EDIT_TEXT", {"button_id": btn_id})
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="✍️ أرسل الرسالة النصية الجديدة للزر:"
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_EDIT_TEXT"), content_types=['text'])
    def process_edit_text(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_settings']:
            clear_user_state(user_id)
            return
        state, data = get_user_state(user_id)
        btn_id = data.get('button_id')
        execute_query("UPDATE buttons SET message_text = %s WHERE id = %s;", (message.text, btn_id), commit=True)
        clear_user_state(user_id)
        bot.send_message(user_id, "✅ تم تعديل الرسالة النصية للزر بنجاح!", reply_markup=get_edit_markup(btn_id))

    # ==========================================
    # تعديل موضع زر شبكياً (السطر والترتيب الأفقي)
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data.startswith("editopt_row_"))
    def cb_edit_row_init(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        btn_id = int(call.data.split("_")[2])
        set_user_state(user_id, "WAITING_EDIT_ROW", {"button_id": btn_id})
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="📐 أرسل رقم السطر الجديد للزر الآن (رقم صحيح):"
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_EDIT_ROW"), content_types=['text'])
    def process_edit_row(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_settings']:
            clear_user_state(user_id)
            return
        if not message.text.strip().isdigit():
            bot.send_message(user_id, "❌ الرجاء إدخال رقم صحيح فقط لرقم السطر:")
            return
        state, data = get_user_state(user_id)
        btn_id = data.get('button_id')
        new_row = int(message.text.strip())
        execute_query("UPDATE buttons SET row_number = %s WHERE id = %s;", (new_row, btn_id), commit=True)
        clear_user_state(user_id)
        bot.send_message(user_id, "✅ تم تعديل رقم سطر الزر بنجاح!", reply_markup=get_edit_markup(btn_id))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("editopt_sort_"))
    def cb_edit_sort_init(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        btn_id = int(call.data.split("_")[2])
        set_user_state(user_id, "WAITING_EDIT_SORT", {"button_id": btn_id})
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="↔️ أرسل رقم الترتيب الأفقي الجديد للزر داخل السطر (رقم صحيح):"
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_EDIT_SORT"), content_types=['text'])
    def process_edit_sort(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_settings']:
            clear_user_state(user_id)
            return
        if not message.text.strip().isdigit():
            bot.send_message(user_id, "❌ الرجاء إدخال رقم صحيح فقط للترتيب الأفقي:")
            return
        state, data = get_user_state(user_id)
        btn_id = data.get('button_id')
        new_sort = int(message.text.strip())
        execute_query("UPDATE buttons SET sort_order = %s WHERE id = %s;", (new_sort, btn_id), commit=True)
        clear_user_state(user_id)
        bot.send_message(user_id, "✅ تم تعديل الترتيب الأفقي للزر بنجاح!", reply_markup=get_edit_markup(btn_id))

    # نقل زر (تعديل المجلد الأب في الشجرة)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("editopt_move_"))
    def cb_move_btn_init(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        btn_id = int(call.data.split("_")[2])
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="🔄 اختر المجلد الأب الجديد للزر:",
            reply_markup=make_admin_move_button_markup(btn_id)
        )
        bot.answer_callback_query(call.id)
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith("exec_move_"))
    def cb_execute_move(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        parts = call.data.split("_")
        btn_id = int(parts[2])
        parent_raw = parts[3]
        parent_id = None if parent_raw == "null" else int(parent_raw)
        execute_query("UPDATE buttons SET parent_id = %s WHERE id = %s;", (parent_id, btn_id), commit=True)
        bot.answer_callback_query(call.id, "✅ تم نقل الزر بنجاح وتحديث الشجرة!", show_alert=True)
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="🛠 تم تحديث موضع الزر بنجاح. ما الذي ترغب بفعله الآن؟",
            reply_markup=get_edit_markup(btn_id)
        )

    # إدارة ملفات الزر
    @bot.callback_query_handler(func=lambda call: call.data.startswith("editopt_files_"))
    def cb_manage_files(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        btn_id = int(call.data.split("_")[2])
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="📁 قائمة الملفات المربوطة بهذا الزر حالياً. يمكنك تعديلها:",
            reply_markup=make_admin_file_manager_markup(btn_id)
        )
        bot.answer_callback_query(call.id)

    # رفع ملفات متعددة للزر
    @bot.callback_query_handler(func=lambda call: call.data.startswith("addfile_"))
    def cb_add_file_init(call):
        user_id = call.from_user.id
        perms = get_permissions(user_id)
        if not is_admin_or_alert(call, perms, 'can_settings'): return
        btn_id = int(call.data.split("_")[1])
        
        set_user_state(user_id, "WAITING_ADD_FILE", {"button_id": btn_id})
        
        save_markup = telebot.types.InlineKeyboardMarkup()
        save_markup.add(telebot.types.InlineKeyboardButton(text="💾 حفظ وإنهاء الرفع", callback_data="save_uploaded_files"))
        
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="📤 أرسل الآن الملفات التي تريد ربطه بالزر (يمكنك إرسال أي عدد من الملفات متتالية).\n\n📌 عند الانتهاء تماماً، اضغط على زر الحفظ بالأسفل 👇:",
            reply_markup=save_markup
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_ADD_FILE"), content_types=['document', 'photo', 'audio', 'video', 'voice'])
    def process_add_file(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if not perms['can_settings']:
            clear_user_state(user_id)
            return
        state, data = get_user_state(user_id)
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
            
        if file_id:
            execute_query("INSERT INTO button_files (button_id, file_id, file_type) VALUES (%s, %s, %s);", (btn_id, file_id, file_type), commit=True)
            
            save_markup = telebot.types.InlineKeyboardMarkup()
            save_markup.add(telebot.types.InlineKeyboardButton(text="💾 حفظ وإنهاء الرفع", callback_data="save_uploaded_files"))
            
            bot.send_message(
                user_id, 
                "➕ تم استقبال الملف بنجاح!\n\nيمكنك الاستمرار بإرسال ملف آخر فوراً، أو اضغط على (حفظ وإنهاء الرفع) بالأسفل عند الاكتفاء 👇.",
                reply_markup=save_markup
            )
        else:
            bot.send_message(user_id, "❌ نوع الملف غير مدعوم أو فشل الرفع.")

    @bot.callback_query_handler(func=lambda call: call.data == "save_uploaded_files")
    def cb_save_uploaded_files(call):
        user_id = call.from_user.id
        state, data = get_user_state(user_id)
        
        if state != "WAITING_ADD_FILE":
            bot.answer_callback_query(call.id, "⚠️ انتهت جلسة الرفع بالفعل أو تم الحفظ مسبقاً.", show_alert=True)
            return
            
        btn_id = data.get('button_id')
        clear_user_state(user_id)
        
        bot.answer_callback_query(call.id, "💾 تم حفظ وإدراج جميع الملفات بنجاح!", show_alert=True)
        bot.send_message(
            user_id, 
            "✅ تم إنهاء الجلسة وتحديث محتويات المجلد بنجاح. يمكنك المراجعة الآن:",
            reply_markup=get_edit_markup(btn_id)
        )

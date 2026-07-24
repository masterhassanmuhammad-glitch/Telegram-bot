import html
from config import bot, OWNER_ID
from database import execute_query, set_user_state, get_user_state, clear_user_state
from keyboards import (
    make_owner_manage_admins_markup, 
    make_remove_admin_list_markup,
    make_permissions_markup
)
from handlers.helpers import check_state

def is_owner_or_alert(call):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذا القسم مخصص لمالك البوت الأصلي فقط!", show_alert=True)
        return False
    return True

# 📑 دالة مساعدة لتوليد نص قائمة المشرفين ولوحتها ومنع تكرار الكود
def get_admins_overview_data():
    admins = execute_query("SELECT admin_id, can_settings, can_broadcast, can_feedback, can_count FROM admins;", fetch=True)
    text = "👥 <b>قائمة المشرفين الحاليين وصلاحياتهم:</b>\n\n"
    if not admins:
        text += "⚠️ لا يوجد أي مشرف مضاف حالياً."
    else:
        for adm_id, c_set, c_broad, c_feed, c_cnt in admins:
            perms_list = []
            if c_set: perms_list.append("⚙️ إعدادات")
            if c_broad: perms_list.append("📢 بث جماعي")
            if c_feed: perms_list.append("📥 رسائل الأعضاء")
            if c_cnt: perms_list.append("📊 إحصائيات")
            text += f"👤 ID: <code>{adm_id}</code>\nالصلاحيات: {', '.join(perms_list) if perms_list else 'لا توجد'}\n\n"
    return text, make_owner_manage_admins_markup()

def register_owner_handlers():

    # 🔍 0️⃣ معالج أمر /info الاستعلامي للمالك
    @bot.message_handler(commands=['info'])
    def cmd_user_info(message):
        user_id = message.from_user.id
        
        # حماية الأمر للمالك فقط
        if user_id != OWNER_ID:
            bot.reply_to(message, "❌ هذا الأمر مخصص لمالك البوت فقط!")
            return

        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                bot.reply_to(
                    message, 
                    "⚠️ <b>الاستخدام الصحيح:</b>\n<code>/info 123456789</code>", 
                    parse_mode="HTML"
                )
                return

            target_id_str = args[1].strip()
            if not target_id_str.isdigit():
                bot.reply_to(message, "❌ يرجى إدخال ID صحيح (أرقام فقط).")
                return

            target_id = int(target_id_str)

            # جلب تفاصيل المستخدم من قاعدة البيانات
            res = execute_query(
                "SELECT user_id, username, first_name, phone_number FROM users WHERE user_id = %s;",
                (target_id,),
                fetch=True
            )

            if not res:
                bot.reply_to(
                    message, 
                    f"❌ لم يتم العثور على أي مستخدم بالـ ID: <code>{target_id}</code> في قاعدة البيانات.", 
                    parse_mode="HTML"
                )
                return

            u_id, u_name, f_name, phone = res[0]

            # جلب إحصائيات الأنشطة
            logs_res = execute_query("SELECT COUNT(*) FROM command_logs WHERE user_id = %s;", (target_id,), fetch=True)
            total_logs = logs_res[0][0] if logs_res else 0

            fb_res = execute_query("SELECT COUNT(*) FROM feedback WHERE user_id = %s;", (target_id,), fetch=True)
            total_fb = fb_res[0][0] if fb_res else 0

            # تهريب الرموز الخاصة لتفادي أخطاء HTML
            safe_first = html.escape(f_name or "غير مسجل")
            safe_username = html.escape(u_name or "لا يوجد")
            safe_phone = html.escape(phone or "غير مسجل")

            text = (
                f"🔍 <b>تفاصيل حساب المستخدم:</b>\n\n"
                f"🆔 <b>ID:</b> <code>{u_id}</code>\n"
                f"👤 <b>الاسم:</b> {safe_first}\n"
                f"🔗 <b>المعرف:</b> @{safe_username}\n"
                f"📱 <b>الهاتف:</b> {safe_phone}\n\n"
                f"📊 <b>إحصائيات النشاط:</b>\n"
                f"• السجلات والتفاعلات: <b>{total_logs}</b>\n"
                f"• الرسائل المرسلة للإدارة: <b>{total_fb}</b>"
            )

            bot.reply_to(message, text, parse_mode="HTML")

        except Exception as e:
            print(f"❌ [/info Error]: {e}")
            bot.reply_to(message, f"❌ حدث خطأ أثناء تنفيذ الأمر:\n<code>{e}</code>", parse_mode="HTML")

    # 1️⃣ استعراض المشرفين وصلاحياتهم
    # 1️⃣ استعراض المشرفين وصلاحياتهم
    @bot.callback_query_handler(func=lambda call: call.data == "owner_manage_admins")
    def cb_owner_manage_admins(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        clear_user_state(user_id)
        
        text, markup = get_admins_overview_data()
                
        bot.edit_message_text(
            chat_id=user_id, 
            message_id=call.message.message_id,
            text=text, 
            parse_mode="HTML", 
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    # 2️⃣ بدء إضافة مشرف جديد
    @bot.callback_query_handler(func=lambda call: call.data == "owner_add_admin")
    def cb_owner_add_admin_init(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        set_user_state(user_id, "WAITING_NEW_ADMIN_ID")
        
        bot.edit_message_text(
            chat_id=user_id, 
            message_id=call.message.message_id,
            text="✍️ أرسل الآن الـ ID الرقمي للمشرف الجديد الذي ترغب في إضافته:\n\n<i>(لإلغاء العملية أرسل /cancel)</i>",
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)

    # 3️⃣ استقبال الـ ID ومعالجته
    @bot.message_handler(func=check_state("WAITING_NEW_ADMIN_ID"), content_types=['text'])
    def process_new_admin_id(message):
        user_id = message.from_user.id
        if user_id != OWNER_ID:
            clear_user_state(user_id)
            return
        
        text = message.text.strip()
        
        # دعم إلغاء العملية
        if text in ["/cancel", "إلغاء"]:
            clear_user_state(user_id)
            bot.send_message(user_id, "🚫 تم إلغاء عملية إضافة المشرف.")
            return
            
        try:
            new_admin_id = int(text)
        except ValueError:
            bot.send_message(user_id, "❌ الـ ID يجب أن يتكون من أرقام فقط. أعد المحاولة أو أرسل /cancel لإلغاء العملية:")
            return
            
        perms_dict = {'settings': False, 'broadcast': False, 'feedback': False, 'count': False}
        set_user_state(user_id, "CHOOSING_ADMIN_PERMISSIONS", {"new_admin_id": new_admin_id, "perms": perms_dict})
        
        bot.send_message(
            user_id,
            f"👤 المشرف المراد إضافته: <code>{new_admin_id}</code>\n\n⚙️ حدد صلاحيات المشرف الجديد (يجب تفعيل خيار واحد على الأقل):",
            parse_mode="HTML",
            reply_markup=make_permissions_markup(perms_dict, new_admin_id)
        )

    # 4️⃣ تبديل وتعيين الصلاحيات
    @bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
    def cb_toggle_permission(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        parts = call.data.split("_")
        perm_type = parts[1]
        target_admin_id = int(parts[2])
        
        state_res = get_user_state(user_id)
        if state_res:
            state, state_data = state_res
            if state == "CHOOSING_ADMIN_PERMISSIONS" and state_data.get('new_admin_id') == target_admin_id:
                perms_dict = state_data.get('perms', {})
                if perm_type == "all":
                    all_enabled = all(perms_dict.values())
                    perms_dict = {k: not all_enabled for k in perms_dict}
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

        bot.answer_callback_query(call.id, "⚠️ انتهت الجلسة، يرجى البدء من جديد من قائمة المشرفين.", show_alert=True)

    # 5️⃣ حفظ المشرف الجديد في قاعدة البيانات
    @bot.callback_query_handler(func=lambda call: call.data.startswith("save_admin_"))
    def cb_save_admin(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        parts = call.data.split("_")
        target_admin_id = int(parts[2])
        
        state_res = get_user_state(user_id)
        if state_res:
            state, state_data = state_res
            if state == "CHOOSING_ADMIN_PERMISSIONS" and state_data.get('new_admin_id') == target_admin_id:
                perms_dict = state_data.get('perms', {})
                if not any(perms_dict.values()):
                    bot.answer_callback_query(call.id, "⚠️ يجب اختيار صلاحية واحدة على الأقل للمشرف الجديد!", show_alert=True)
                    return
                    
                execute_query('''
                    INSERT INTO admins (admin_id, can_settings, can_broadcast, can_feedback, can_count)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (admin_id) DO UPDATE SET 
                        can_settings = EXCLUDED.can_settings,
                        can_broadcast = EXCLUDED.can_broadcast,
                        can_feedback = EXCLUDED.can_feedback,
                        can_count = EXCLUDED.can_count;
                ''', (target_admin_id, perms_dict['settings'], perms_dict['broadcast'], perms_dict['feedback'], perms_dict['count']), commit=True)
                
                clear_user_state(user_id)
                bot.answer_callback_query(call.id, "✅ تم حفظ المشرف وتفعيل صلاحياته بنجاح!", show_alert=True)
                
                text, markup = get_admins_overview_data()
                bot.edit_message_text(
                    chat_id=user_id, 
                    message_id=call.message.message_id,
                    text=text, 
                    parse_mode="HTML", 
                    reply_markup=markup
                )
                return

        bot.answer_callback_query(call.id, "⚠️ انتهت الجلسة، يرجى البدء من جديد.", show_alert=True)

    # 6️⃣ عرض قائمة الحذف
    @bot.callback_query_handler(func=lambda call: call.data == "owner_remove_admin_list")
    def cb_owner_remove_admin_list(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        
        bot.edit_message_text(
            chat_id=user_id, 
            message_id=call.message.message_id,
            text="🗑️ اختر المشرف الذي ترغب في حذفه تماماً وسحب صلاحياته:",
            reply_markup=make_remove_admin_list_markup()
        )
        bot.answer_callback_query(call.id)

    # 7️⃣ تنفيذ الحذف وسحب الصلاحية
    @bot.callback_query_handler(func=lambda call: call.data.startswith("exec_remove_admin_"))
    def cb_execute_remove_admin(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        target_id = int(call.data.split("_")[3])
        
        execute_query("DELETE FROM admins WHERE admin_id = %s;", (target_id,), commit=True)
        bot.answer_callback_query(call.id, "✅ تم إزالة المشرف وسحب جميع صلاحياته بنجاح!", show_alert=True)
        
        text, markup = get_admins_overview_data()
        bot.edit_message_text(
            chat_id=user_id, 
            message_id=call.message.message_id,
            text=text, 
            parse_mode="HTML", 
            reply_markup=markup
            )
                    

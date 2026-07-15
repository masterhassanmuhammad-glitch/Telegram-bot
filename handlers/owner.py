from config import bot, OWNER_ID
from database import execute_query, set_user_state, get_user_state, clear_user_state
from keyboards import (
    make_owner_manage_admins_markup, make_remove_admin_list_markup,
    make_permissions_markup
)
from handlers.helpers import check_state

def is_owner_or_alert(call):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ هذا القسم مخصص لمالك البوت الأصلي فقط!", show_alert=True)
        return False
    return True

def register_owner_handlers():
    
    # استعراض المشرفين وصلاحياتهم
    @bot.callback_query_handler(func=lambda call: call.data == "owner_manage_admins")
    def cb_owner_manage_admins(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
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
            chat_id=user_id, message_id=call.message.message_id,
            text=text, parse_mode="Markdown", reply_markup=make_owner_manage_admins_markup()
        )
        bot.answer_callback_query(call.id)

    # بدء إضافة مشرف جديد
    @bot.callback_query_handler(func=lambda call: call.data == "owner_add_admin")
    def cb_owner_add_admin_init(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        set_user_state(user_id, "WAITING_NEW_ADMIN_ID")
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="✍️ حسناً، أرسل الآن الـ ID الرقمي للمشرف الجديد الذي ترغب في إضافته:"
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=check_state("WAITING_NEW_ADMIN_ID"), content_types=['text'])
    def process_new_admin_id(message):
        user_id = message.from_user.id
        if user_id != OWNER_ID:
            clear_user_state(user_id)
            return
        try:
            new_admin_id = int(message.text.strip())
        except ValueError:
            bot.send_message(user_id, "❌ الـ ID يجب أن يتكون من أرقام فقط. أعد المحاولة:")
            return
            
        perms_dict = {'settings': False, 'broadcast': False, 'feedback': False, 'count': False}
        set_user_state(user_id, "CHOOSING_ADMIN_PERMISSIONS", {"new_admin_id": new_admin_id, "perms": perms_dict})
        bot.send_message(
            user_id,
            f"👤 المشرف المراد إضافته: `{new_admin_id}`\n\n⚙️ حدد صلاحيات المشرف الجديد (يجب تفعيل خيار واحد على الأقل):",
            parse_mode="Markdown",
            reply_markup=make_permissions_markup(perms_dict, new_admin_id)
        )

    # تبديل وحفظ الصلاحيات
    @bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
    def cb_toggle_permission(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        parts = call.data.split("_")
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
                chat_id=user_id, message_id=call.message.message_id,
                reply_markup=make_permissions_markup(perms_dict, target_admin_id)
            )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("save_admin_"))
    def cb_save_admin(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        parts = call.data.split("_")
        target_admin_id = int(parts[2])
        
        state, state_data = get_user_state(user_id)
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
            bot.answer_callback_query(call.id, "✅ تم حفظ المشرف الجديد وتفعيل صلاحياته بنجاح!", show_alert=True)
            
            # العودة للقائمة المحدثة
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
                chat_id=user_id, message_id=call.message.message_id,
                text=text, parse_mode="Markdown", reply_markup=make_owner_manage_admins_markup()
            )

    # سحب الرتبة وإلغاء المشرف
    @bot.callback_query_handler(func=lambda call: call.data == "owner_remove_admin_list")
    def cb_owner_remove_admin_list(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        bot.edit_message_text(
            chat_id=user_id, message_id=call.message.message_id,
            text="🗑️ اختر المشرف الذي ترغب في حذفه تماماً وسحب صلاحياته:",
            reply_markup=make_remove_admin_list_markup()
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("exec_remove_admin_"))
    def cb_execute_remove_admin(call):
        if not is_owner_or_alert(call): return
        user_id = call.from_user.id
        target_id = int(call.data.split("_")[3])
        execute_query("DELETE FROM admins WHERE admin_id = %s;", (target_id,), commit=True)
        bot.answer_callback_query(call.id, "✅ تم إزالة المشرف وسحب جميع صلاحياته بنجاح!", show_alert=True)
        
        # العودة للقائمة المحدثة
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
            chat_id=user_id, message_id=call.message.message_id,
            text=text, parse_mode="Markdown", reply_markup=make_owner_manage_admins_markup()
      )
      

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from config import OWNER_ID

def make_main_menu_markup(perms, user_id=None):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # 1. جلب الأزرار الرئيسية ديناميكياً وترتيبها حسب السطر والترتيب الأفقي
    main_buttons = execute_query(
        "SELECT id, name, row_number FROM buttons WHERE parent_id IS NULL ORDER BY row_number ASC, sort_order ASC;", 
        fetch=True
    )
    
    # تجميع الأزرار المخصصة في أسطر بناءً على إعدادات الآدمن
    rows = {}
    for btn_id, btn_name, row_num in main_buttons:
        if row_num not in rows:
            rows[row_num] = []
        rows[row_num].append(InlineKeyboardButton(text=btn_name, callback_data=f"open_{btn_id}"))
        
    # رص الأزرار الديناميكية أولاً في أعلى القائمة
    for r in sorted(rows.keys()):
        markup.row(*rows[r])
        
    # 2. إضافة الأزرار الإدارية الثابتة أسفل الأزرار الديناميكية بناءً على الصلاحيات
    if perms.get('is_admin'):
        row_buttons = []
        
        # أزرار الصلاحيات الفردية
        if perms.get('can_settings'):
            markup.add(InlineKeyboardButton(text="⚙️ الإعدادات الإدارية", callback_data="admin_settings"))
        if perms.get('can_broadcast'):
            markup.add(InlineKeyboardButton(text="📢 إرسال رسالة جماعية", callback_data="admin_broadcast"))
            
        if perms.get('can_count'):
            row_buttons.append(InlineKeyboardButton(text="📊 عدد المستخدمين", callback_data="admin_count_users"))
        if perms.get('can_feedback'):
            row_buttons.append(InlineKeyboardButton(text="📥 رسائل المستخدمين", callback_data="admin_view_feedback"))
            
        if row_buttons:
            markup.row(*row_buttons)
            
        # زر إدارة المشرفين يظهر للمالك فقط
        if perms.get('is_owner') or user_id == OWNER_ID:
            markup.add(InlineKeyboardButton(text="👥 إدارة المشرفين", callback_data="owner_manage_admins"))
    
    # زر مراسلة الإدارة الثابت للجميع (في آخر القائمة دائماً)
    markup.add(InlineKeyboardButton(text="📬 مراسلة الإدارة", callback_data="user_contact"))
    
    return markup


def make_sub_menu_markup(parent_id, is_admin=False):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # 1. جلب الأزرار الفرعية ديناميكياً وترتيبها حسب السطر والترتيب الأفقي
    sub_buttons = execute_query(
        "SELECT id, name, row_number FROM buttons WHERE parent_id = %s ORDER BY row_number ASC, sort_order ASC;", 
        (parent_id,), fetch=True
    )
    
    # تجميع الأزرار الفرعية المخصصة في أسطر
    rows = {}
    for btn_id, btn_name, row_num in sub_buttons:
        if row_num not in rows:
            rows[row_num] = []
        rows[row_num].append(InlineKeyboardButton(text=btn_name, callback_data=f"open_{btn_id}"))
        
    # رص الأزرار الفرعية الديناميكية
    for r in sorted(rows.keys()):
        markup.row(*rows[r])
        
    # 2. زر العودة الذكي للخلف (يظهر دائماً في الأسفل)
    parent_info = execute_query("SELECT parent_id FROM buttons WHERE id = %s;", (parent_id,), fetch=True)
    back_id = parent_info[0][0] if parent_info else None
    
    back_callback = f"open_{back_id}" if back_id is not None else "main_menu"
    markup.add(InlineKeyboardButton(text="🔙 عودة للخلف", callback_data=back_callback))
    
    return markup


def make_admin_settings_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(text="➕ إضافة زر جديد", callback_data="adm_add_btn"),
        InlineKeyboardButton(text="❌ حذف زر", callback_data="adm_del_btn"),
        InlineKeyboardButton(text="✏️ تعديل زر", callback_data="adm_edit_btn"),
        InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="main_menu")
    )
    return markup


def make_admin_edit_options_markup(button_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(text="✏️ تعديل الاسم", callback_data=f"editopt_name_{button_id}"),
        InlineKeyboardButton(text="📝 تعديل الرسالة النصية", callback_data=f"editopt_msg_{button_id}")
    )
    markup.add(
        InlineKeyboardButton(text="🔄 نقل الزر لمكان آخر", callback_data=f"editopt_move_{button_id}"),
        InlineKeyboardButton(text="📁 إدارة ملفات الزر", callback_data=f"editopt_files_{button_id}")
    )
    markup.add(InlineKeyboardButton(text="🔙 العودة للإعدادات", callback_data="admin_settings"))
    return markup


def make_admin_choose_parent_markup(button_name, exclude_id=None):
    markup = InlineKeyboardMarkup(row_width=1)
    
    # قص الاسم لـ 15 حرف كحد أقصى لضمان عدم تجاوز الـ 64 بايت مع الحروف العربية
    short_name = button_name[:15]
    
    markup.add(InlineKeyboardButton(text="📁 في القائمة الرئيسية مباشرة", callback_data=f"setparent_new_{short_name}_null"))
    
    if exclude_id:
        all_buttons = execute_query("SELECT id, name FROM buttons WHERE id != %s ORDER BY id ASC;", (exclude_id,), fetch=True)
    else:
        all_buttons = execute_query("SELECT id, name FROM buttons ORDER BY id ASC;", fetch=True)
        
    for b_id, b_name in all_buttons:
        markup.add(InlineKeyboardButton(text=f"📁 داخل [ {b_name} ]", callback_data=f"setparent_new_{short_name}_{b_id}"))
        
    return markup
    


def make_admin_move_button_markup(button_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text="📁 نقل إلى القائمة الرئيسية", callback_data=f"exec_move_{button_id}_null"))
    
    other_buttons = execute_query("SELECT id, name FROM buttons WHERE id != %s ORDER BY id ASC;", (button_id,), fetch=True)
    for ob_id, ob_name in other_buttons:
        markup.add(InlineKeyboardButton(text=f"📁 داخل [ {ob_name} ]", callback_data=f"exec_move_{button_id}_{ob_id}"))
        
    markup.add(InlineKeyboardButton(text="🔙 إلغاء ونكوص", callback_data=f"choose_edit_{button_id}"))
    return markup


def make_admin_file_manager_markup(button_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text="➕ إضافة ملف جديد لهذا الزر", callback_data=f"addfile_{button_id}"))
    markup.add(InlineKeyboardButton(text="🗑️ حذف جميع الملفات", callback_data=f"delallfiles_{button_id}"))
    
    files = execute_query("SELECT id, file_type FROM button_files WHERE button_id = %s ORDER BY id ASC;", (button_id,), fetch=True)
    for f_record_id, f_type in files:
        markup.add(InlineKeyboardButton(text=f"🗑 حذف ملف ({f_type})", callback_data=f"delfile_{f_record_id}_{button_id}"))
        
    markup.add(InlineKeyboardButton(text="🔙 عودة لخصائص الزر", callback_data=f"choose_edit_{button_id}"))
    return markup


def make_owner_manage_admins_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(text="➕ إضافة مشرف جديد", callback_data="owner_add_admin"),
        InlineKeyboardButton(text="🗑️ إزالة مشرف وسحب الصلاحيات", callback_data="owner_remove_admin_list"),
        InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="main_menu")
    )
    return markup


# 🛠️ الدالة المحدثة كلياً لعرض الاسم الفعلي ورقم الهاتف عند الإزالة
def make_remove_admin_list_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    
    # جلب معرف المشرف والاسم ورقم الهاتف عبر LEFT JOIN مع جدول الـ users
    admins = execute_query("""
        SELECT a.admin_id, u.first_name, u.last_name, u.phone_number 
        FROM admins a
        LEFT JOIN users u ON a.admin_id = u.user_id;
    """, fetch=True)
    
    if admins:
        for row in admins:
            adm_id, first_name, last_name, phone = row
            
            # التحقق من وجود الاسم الأول للمستخدم لبناء الاسم الكامل
            if first_name:
                full_name = f"{first_name} {last_name or ''}".strip()
            else:
                full_name = f"المشرف ({adm_id})"
            
            # دمج رقم الهاتف في نص الزر إن وجد بصيغة أنيقة
            phone_suffix = f" 📱 {phone}" if phone else " (بلا هاتف)"
            button_text = f"❌ إزالة {full_name}{phone_suffix}"
            
            markup.add(InlineKeyboardButton(text=button_text, callback_data=f"exec_remove_admin_{adm_id}"))
            
    markup.add(InlineKeyboardButton(text="🔙 عودة", callback_data="owner_manage_admins"))
    return markup


def make_permissions_markup(perms_dict, new_admin_id):
    markup = InlineKeyboardMarkup(row_width=1)
    
    settings_status = "✅" if perms_dict.get('settings') else "❌"
    broadcast_status = "✅" if perms_dict.get('broadcast') else "❌"
    feedback_status = "✅" if perms_dict.get('feedback') else "❌"
    count_status = "✅" if perms_dict.get('count') else "❌"
    
    markup.add(
        InlineKeyboardButton(text=f"{settings_status} صلاحية الإعدادات الإدارية", callback_data=f"toggle_settings_{new_admin_id}"),
        InlineKeyboardButton(text=f"{broadcast_status} صلاحية إرسال رسالة جماعية", callback_data=f"toggle_broadcast_{new_admin_id}"),
        InlineKeyboardButton(text=f"{feedback_status} صلاحية رسائل المستخدمين", callback_data=f"toggle_feedback_{new_admin_id}"),
        InlineKeyboardButton(text=f"{count_status} صلاحية عدد المستخدمين", callback_data=f"toggle_count_{new_admin_id}"),
        InlineKeyboardButton(text="⚡ منح جميع الصلاحيات", callback_data=f"toggle_all_{new_admin_id}"),
        InlineKeyboardButton(text="💾 حفظ وإضافة المشرف", callback_data=f"save_admin_{new_admin_id}"),
        InlineKeyboardButton(text="🔙 إلغاء والعودة", callback_data="owner_manage_admins")
    )
    return markup
            

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query

def make_main_menu_markup(is_admin=False):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # 1. جلب الأزرار الرئيسية (التي ليس لها أب) من قاعدة البيانات
    main_buttons = execute_query("SELECT id, name FROM buttons WHERE parent_id IS NULL ORDER BY id ASC;", fetch=True)
    
    for btn_id, btn_name in main_buttons:
        markup.add(InlineKeyboardButton(text=btn_name, callback_data=f"open_{btn_id}"))
        
    # 2. إضافة الأزرار الثابتة بناءً على نوع المستخدم (مشرف أم مستخدم عادي)
    if is_admin:
        # أزرار المشرف الثابتة داخل القائمة الرئيسية
        markup.add(InlineKeyboardButton(text="⚙️ الإعدادات الإدارية", callback_data="admin_settings"))
        markup.add(InlineKeyboardButton(text="📢 إرسال رسالة جماعية", callback_data="admin_broadcast"))
        markup.row(
            InlineKeyboardButton(text="📊 عدد المستخدمين", callback_data="admin_count_users"),
            InlineKeyboardButton(text="📥 رسائل المستخدمين", callback_data="admin_view_feedback")
        )
    
    # زر مراسلة الإدارة الثابت للجميع
    markup.add(InlineKeyboardButton(text="📬 مراسلة الإدارة", callback_data="user_contact"))
    
    return markup

def make_sub_menu_markup(parent_id, is_admin=False):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # 1. جلب الأزرار الفرعية التابعة للـ parent_id
    sub_buttons = execute_query("SELECT id, name FROM buttons WHERE parent_id = %s ORDER BY id ASC;", (parent_id,), fetch=True)
    
    for btn_id, btn_name in sub_buttons:
        markup.add(InlineKeyboardButton(text=btn_name, callback_data=f"open_{btn_id}"))
        
    # 2. زر العودة الذكي للخلف
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
    markup.add(InlineKeyboardButton(text="📁 في القائمة الرئيسية مباشرة", callback_data=f"setparent_new_{button_name}_null"))
    
    # جلب جميع الأزرار لتكون خياراً كمجلد أب
    if exclude_id:
        # عند النقل، نمنع نقل الزر لداخل نفسه لتفادي تعليق شجرة الأزرار
        all_buttons = execute_query("SELECT id, name FROM buttons WHERE id != %s ORDER BY id ASC;", (exclude_id,), fetch=True)
    else:
        all_buttons = execute_query("SELECT id, name FROM buttons ORDER BY id ASC;", fetch=True)
        
    for b_id, b_name in all_buttons:
        markup.add(InlineKeyboardButton(text=f"📁 داخل [ {b_name} ]", callback_data=f"setparent_new_{button_name}_{b_id}"))
        
    return markup

def make_admin_move_button_markup(button_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text="📁 نقل إلى القائمة الرئيسية", callback_data=f"exec_move_{button_id}_null"))
    
    # جلب الأزرار الأخرى المتاحة لتكون أب (باستثناء الزر نفسه)
    other_buttons = execute_query("SELECT id, name FROM buttons WHERE id != %s ORDER BY id ASC;", (button_id,), fetch=True)
    for ob_id, ob_name in other_buttons:
        markup.add(InlineKeyboardButton(text=f"📁 داخل [ {ob_name} ]", callback_data=f"exec_move_{button_id}_{ob_id}"))
        
    markup.add(InlineKeyboardButton(text="🔙 إلغاء ونكوص", callback_data=f"choose_edit_{button_id}"))
    return markup

def make_admin_file_manager_markup(button_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text="➕ إضافة ملف جديد لهذا الزر", callback_data=f"addfile_{button_id}"))
    
    # جلب الملفات الحالية المربوطة بالزر
    files = execute_query("SELECT id, file_type FROM button_files WHERE button_id = %s ORDER BY id ASC;", (button_id,), fetch=True)
    for f_record_id, f_type in files:
        markup.add(InlineKeyboardButton(text=f"🗑 حذف ملف ({f_type})", callback_data=f"delfile_{f_record_id}_{button_id}"))
        
    markup.add(InlineKeyboardButton(text="🔙 عودة لخصائص الزر", callback_data=f"choose_edit_{button_id}"))
    return markup
        

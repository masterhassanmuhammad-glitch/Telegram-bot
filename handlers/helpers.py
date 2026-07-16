from telebot import types
from config import ADMIN_IDS, OWNER_ID
from database import execute_query, get_user_state

def get_permissions(user_id):
    # 1. المالك الأساسي للبوت
    if OWNER_ID and user_id == OWNER_ID:
        return {
            'is_admin': True, 'is_owner': True,
            'can_settings': True, 'can_broadcast': True,
            'can_feedback': True, 'can_count': True
        }
    
    # 2. فحص المشرفين من قاعدة البيانات
    res = execute_query("SELECT can_settings, can_broadcast, can_feedback, can_count FROM admins WHERE admin_id = %s;", (user_id,), fetch=True)
    if res:
        return {
            'is_admin': True, 'is_owner': False,
            'can_settings': res[0][0], 'can_broadcast': res[0][1],
            'can_feedback': res[0][2], 'can_count': res[0][3]
        }
    
    # 3. دعم احتياطي لمعرفات البيئة الثابتة
    if user_id in ADMIN_IDS:
        return {
            'is_admin': True, 'is_owner': False,
            'can_settings': True, 'can_broadcast': True,
            'can_feedback': True, 'can_count': True
        }
        
    return {
        'is_admin': False, 'is_owner': False,
        'can_settings': False, 'can_broadcast': False,
        'can_feedback': False, 'can_count': False
    }

# فلتر مخصص للتحقق من حالة المستخدم (State Filter)
def check_state(state_name):
    return lambda message: get_user_state(message.from_user.id)[0] == state_name
    # ... الأكواد والدوال القديمة الخاصة بك ...

# قاموس لتخزين معرف رسالة التحكم النشطة حالياً لكل مستخدم
# الشكل: { user_id: message_id }
active_menus = {}

def send_files_and_recreate_menu(bot, chat_id, files_list, menu_text, reply_markup):
    """
    تقوم بحذف قائمة التحكم القديمة، إرسال قائمة ملفات، 
    ثم إرسال قائمة تحكم جديدة في أسفل الشات تماماً.
    """
    # 1. حذف قائمة التحكم القديمة لتجنب تكرار القوائم في الشات
    if chat_id in active_menus:
        try:
            bot.delete_message(chat_id, active_menus[chat_id])
        except Exception:
            pass

    # 2. إرسال جميع الملفات الموجودة في القائمة متتالية
    for file_id in files_list:
        try:
            bot.send_document(chat_id, file_id)
        except Exception as e:
            # لتفادي توقف البوت إذا كان هناك ملف تالف أو مفقود
            print(f"خطأ في إرسال الملف {file_id}: {e}")

    # 3. إرسال رسالة التحكم الجديدة في الأسفل لتكون تحت الملفات مباشرة
    try:
        new_menu = bot.send_message(chat_id, menu_text, reply_markup=reply_markup)
        # حفظ معرف القائمة الجديدة لاستخدامه في المرة القادمة
        active_menus[chat_id] = new_menu.message_id
    except Exception as e:
        print(f"خطأ في إرسال القائمة الجديدة: {e}")
        from telebot import types

# 1. ضع هنا يوزر مجموعة الدفعة (مثال: @OIU_Batch35) أو رقم الآيدي الخاص بها
BATCH_GROUP_ID = "@Your_Batch_Group_Username" 
# رابط المجموعة ليتمكن المستخدم من النقر عليه والانضمام مباشرة
GROUP_LINK = "https://t.me/Your_Batch_Group_Username"

def is_user_in_batch(bot, user_id):
    """
    تحقق مما إذا كان الطالب عضواً في مجموعة الدفعة أم لا.
    """
    try:
        # فحص حالة المستخدم داخل المجموعة
        member = bot.get_chat_member(BATCH_GROUP_ID, user_id)
        
        # الحالات المسموح لها باستخدام البوت (مالك، مشرف، عضو عادي)
        if member.status in ['creator', 'administrator', 'member']:
            return True
            
    except Exception as e:
        # إذا لم يجد المستخدم أو حدث خطأ (مثلاً البوت ليس مشرفاً)
        print(f"خطأ أثناء فحص العضوية: {e}")
        return False
        
    return False

def send_join_request_menu(bot, chat_id):
    """
    قائمة تظهر للمستخدم غير المنضم، تحتوي على رابط المجموعة وزر للتحقق.
    """
    keyboard = types.InlineKeyboardMarkup()
    # زر ينقل المستخدم مباشرة للمجموعة للانضمام
    btn_link = types.InlineKeyboardButton("🔗 انضم لمجموعة الدفعة من هنا", url=GROUP_LINK)
    # زر يضغط عليه الطالب بعد الانضمام ليفحص البوت حسابه مجدداً
    btn_check = types.InlineKeyboardButton("🔄 تم الانضمام، تحقق الآن", callback_data="check_membership")
    
    keyboard.add(btn_link)
    keyboard.add(btn_check)
    
    text = "⚠️ **عذراً، هذا البوت مخصص لطلاب دفعتنا فقط!**\n\nيرجى الانضمام إلى مجموعة الدفعة أولاً لتتمكن من استخدام الخدمات البرمجية والمفات المتاحة."
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)
    
        

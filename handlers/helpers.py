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

# ==========================================
# إضافة الكود الجديد في نهاية الملف:
# ==========================================

# قاموس لتخزين معرف آخر رسالة لكل مستخدم
last_messages = {}

def send_and_replace(bot, chat_id, text=None, document=None, reply_markup=None):
    """
    دالة ذكية لحذف الرسالة القديمة وإرسال رسالة أو ملف جديد مكانها.
    """
    # 1. محاولة حذف الرسالة القديمة إن وجدت
    if chat_id in last_messages:
        try:
            bot.delete_message(chat_id, last_messages[chat_id])
        except Exception:
            # نتجاهل أي خطأ في حال قام المستخدم بحذف الرسالة بنفسه
            pass

    # 2. إرسال المحتوى الجديد (ملف أو نص)
    sent_msg = None
    if document:
        sent_msg = bot.send_document(chat_id, document, caption=text, reply_markup=reply_markup)
    elif text:
        sent_msg = bot.send_message(chat_id, text, reply_markup=reply_markup)

    # 3. حفظ معرف الرسالة الجديدة في القاموس
    if sent_msg:
        last_messages[chat_id] = sent_msg.message_id
        
    return sent_msg
    
  

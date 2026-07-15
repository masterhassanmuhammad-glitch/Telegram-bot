from config import bot
from handlers.helpers import get_permissions

def register_fallback_handlers():
    @bot.message_handler(content_types=['text', 'document', 'photo', 'audio', 'video', 'voice'])
    def fallback_all_messages(message):
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        if perms['is_admin']:
            bot.send_message(user_id, "⚠️ لم أفهم هذا الأمر. الرجاء استخدام أزرار لوحة التحكم أو كتابة /start للبدء.")
        else:
            bot.send_message(user_id, "⚠️ الرجاء استخدام أزرار القائمة للتنقل. إذا واجهت مشكلة اضغط /start أو انقر على زر 'مراسلة الإدارة'.")
          

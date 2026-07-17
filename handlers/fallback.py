from config import bot
from handlers.helpers import get_permissions

def register_fallback_handlers():
    @bot.message_handler(func=lambda message: True) # سيتم تنفيذه لكل الرسائل
    def debug_and_fallback(message):
        # 1. طباعة تفاصيل الرسالة في الـ Logs (للتشخيص)
        print(f"DEBUG: [Received] ChatID: {message.chat.id} | Type: {message.chat.type} | User: {message.from_user.username} | Text: {message.text or 'NoText'}")

        # 2. متابعة عمل الـ Fallback المعتاد
        user_id = message.from_user.id
        perms = get_permissions(user_id)
        
        # إذا كانت الرسالة في مجموعة، لا نرد بشكل مزعج، نكتفي بالـ Log فقط
        if message.chat.type in ['group', 'supergroup']:
            return

        # الرد في المحادثات الخاصة فقط
        if perms['is_admin']:
            bot.send_message(user_id, "⚠️ لم أفهم هذا الأمر. الرجاء استخدام أزرار لوحة التحكم أو كتابة /start للبدء.")
        else:
            bot.send_message(user_id, "⚠️ الرجاء استخدام أزرار القائمة للتنقل. إذا واجهت مشكلة اضغط /start أو انقر على زر 'مراسلة الإدارة'.")
            

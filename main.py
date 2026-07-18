import config
from telebot import types
from database import init_db
from handlers import init_handlers

if __name__ == "__main__":
    print("⚡ جاري تهيئة قاعدة بيانات Neon...")
    init_db()
    
    print("⚙️ جاري تسجيل ومعالجة كافة الأوامر والملفات المقسمة...")
    init_handlers()
    
    # 🛠️ تعيين قائمة الأوامر (زر القائمة /start أسفل الشاشة)
    print("📋 جاري تعيين زر تشغيل البوت في القائمة...")
    config.bot.set_my_commands([
        types.BotCommand("start", "اضغط لتشغيل البوت")
    ])
    
    # إلغاء أي Webhook قديم عالق
    config.bot.remove_webhook()
    
    print("🚀 تم تشغيل البوت بنجاح ويقوم بالبث التفاعلي الآن!")
    config.bot.infinity_polling()
    

# main.py
import config
from database import init_db
from handlers import init_handlers

if __name__ == "__main__":
    print("⚡ جاري تهيئة قاعدة بيانات Neon...")
    init_db()
    
    print("⚙️ جاري تسجيل ومعالجة كافة الأوامر والملفات المقسمة...")
    init_handlers()
    
    print("🚀 تم تشغيل البوت بنجاح ويقوم بالبث التفاعلي الآن!")
    config.bot.infinity_polling()
    

import sys
import telebot
from config import bot
from database import init_db
from handlers import register_handlers

def main():
    print("⚡ [1/4] جاري تشغيل البوت الأكاديمي لـ (Batch 35 & 36)...")
    
    # 1. التحقق من تهيئة كائن البوت بنجاح من ملف الإعدادات
    if bot is None:
        print("❌ خطأ فادح: لم يتم العثور على توكن البوت (BOT_TOKEN) في متغيرات البيئة!")
        print("💡 يرجى التأكد من إضافة الـ Token في إعدادات البيئة على منصة Render.")
        sys.exit(1)
        
    try:
        # 2. فحص وتحديث جداول قاعدة البيانات (Neon PostgreSQL)
        print("🗄️ [2/4] جاري الاتصال وتحديث جداول قاعدة بيانات Neon...")
        init_db()
        print("✅ تم فحص وتحديث قاعدة البيانات بنجاح.")
        
        # 3. تسجيل جميع المعالجات والأوامر البرمجية
        print("🧠 [3/4] جاري تحميل وتسجيل معالجات الأحداث (Handlers)...")
        register_handlers()
        print("✅ تم تسجيل كافة الأوامر وأزرار التحكم بنجاح.")
        
        # 4. إطلاق البوت ليكون أونلاين واستقبال الرسائل
        print("🚀 [4/4] البوت يعمل الآن بنجاح وبانتظار رسائل الطلاب...")
        print("📡 جاري بدء الاستماع المستمر (Polling)...")
        
        # infinity_polling تضمن بقاء البوت مستيقظاً وتتعامل مع انقطاعات الشبكة تلقائياً
        bot.infinity_polling(timeout=15, long_polling_timeout=10)
        
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت يدوياً بنجاح. أراك لاحقاً يا حسن!")
    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع أثناء تشغيل البوت: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
  

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# استيراد الإعدادات والموزع المركزي وحوض الاتصال
import config
from database import DatabaseManager
from router import start_handler, callback_handler, text_handler
from services.setting_service import SettingService

# إعداد السجلات ومراقبة الأخطاء (Logging)
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def init_application():
    """تهيئة وإعداد تطبيق التليجرام والروابط"""
    # 1. تهيئة حوض اتصالات قاعدة البيانات (Neon Connection Pool)
    DatabaseManager.initialize()
    
    # 2. تهيئة الإعدادات الافتراضية للبوت في قاعدة البيانات إن لم تكن موجودة
    SettingService.initialize_default_settings()

    # 3. بناء تطبيق التليجرام باستخدام التوكن الممرر من متغيرات البيئة
    application = Application.builder().token(config.API_TOKEN).build()

    # 4. تسجيل الـ Handlers والمستقبلات وربطها بالموزع المركزي (router.py)
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CallbackQueryHandler(callback_handler))
    # استقبال النصوص والصور والملفات المباشرة للتعامل معها عبر الـ FSM
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        text_handler
    ))

    return application

def main():
    # بناء وتجهيز التطبيق
    application = init_application()

    # 5. تحديد طريقة التشغيل بناءً على البيئة (Render Webhook أم Local Polling)
    if config.RENDER_EXTERNAL_URL:
        # التشغيل بأسلوب الـ Webhook (الوضع المعتمد والمثالي لمنصة Render)
        logger.info("🌐 جاري تشغيل البوت عبر نظام الـ Webhook على منصة Render...")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=config.PORT,
            url_path=config.API_TOKEN,
            webhook_url=f"{config.RENDER_EXTERNAL_URL}/{config.API_TOKEN}"
        )
    else:
        # التشغيل بأسلوب الـ Polling (للإختبار والتطوير المحلي على جهازك)
        logger.info("🤖 جاري تشغيل البوت عبر نظام الـ Polling المحلّي...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
  

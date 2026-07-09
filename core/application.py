from telegram.ext import Application
from config import BOT_TOKEN

# استيراد الخدمات والدوال الضرورية
from services.bootstrap_service import initialize
from handlers.start import register as register_start
from handlers.callback import register as register_callback
from handlers.admin import register as register_admin
from handlers.admin_menus import register as register_admin_menus
from handlers.admin_add_menu import register as register_admin_add_menu
from handlers.admin_parent_menu import register as register_admin_parent_menu
from handlers.admin_sort_menu import register as register_admin_sort_menu

register_admin_sort_menu(application)

# 1. تشغيل الخدمات الأساسية أولاً (إذا كانت قاعدة البيانات تعتمد عليها)
initialize()

# 2. إنشاء كائن الـ Application وتجهيز التوكن
application = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

# 3. تسجيل جميع الـ Handlers بعد إنشاء الـ application بنجاح
register_start(application)
register_callback(application)
register_admin(application)
register_admin_menus(application)
register_admin_add_menu(application)
register_admin_parent_menu(application)

# 4. بدء تشغيل البوت (إضافة اختيارية إذا لم تكن تستدعيها في ملف آخر)
# if __name__ == "__main__":
#     application.run_polling()

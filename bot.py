print("BOT STARTING...")
import telebot
import logging
from flask import Flask, request

from config import API_TOKEN, PORT, RENDER_EXTERNAL_URL
from database import init_db, init_settings

# استيراد كافة مجمعات المعالجات من ملفاتها الخاصة
from handlers import register_handlers
from consultation import register_consultation_handlers
from files import register_file_handlers
from broadcast import register_broadcast_handlers
from users import register_user_handlers
from admin import register_admin_handlers

# ============================================
# LOGGING
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ============================================
# BOT INIT
# ============================================
# تفعيل خيار threaded=False لضمان معالجة الرسائل تزامناً مع طلب Flask وبدون اختفاء صامت
bot = telebot.TeleBot(API_TOKEN, parse_mode="HTML", threaded=False)

# ============================================
# FLASK APP (FOR WEBHOOK)
# ============================================
app = Flask(__name__)

# ============================================
# INIT DATABASE
# ============================================
init_db()
init_settings(owner_id=8203001172)

# ============================================
# REGISTER ALL HANDLERS (ربط كافة الملفات بالبوت)
# ============================================
register_handlers(bot)
register_consultation_handlers(bot)
register_file_handlers(bot)
register_broadcast_handlers(bot)
register_user_handlers(bot)
register_admin_handlers(bot)

# ============================================
# ROUTES (HEALTH CHECK & WEBHOOK)
# ============================================
# دمج المسارات على الرابط الرئيسي '/' ليتعامل مع الـ GET والـ POST في نفس الوقت
@app.route("/", methods=["GET", "HEAD", "POST"])
def index():
    if request.method in ["GET", "HEAD"]:
        return "MedicalBot is running and healthy! 🏥", 200
        
    elif request.method == "POST":
        if request.headers.get('content-type') == 'application/json':
            json_str = request.get_data().decode("utf-8")
            update = telebot.types.Update.de_json(json_str)
            bot.process_new_updates([update])
            return "OK", 200
        else:
            return "Invalid request", 400

# ============================================
# SET WEBHOOK
# ============================================
def set_webhook():
    if RENDER_EXTERNAL_URL:
        # جعل الويب هوك يشير إلى الرابط الرئيسي مباشرة دون الحاجة للتوكن في الآخِر ليتطابق مع الـ Route
        url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/"
        bot.remove_webhook()
        bot.set_webhook(url=url)
        logging.info(f"Webhook set to: {url}")
    else:
        logging.warning("RENDER_EXTERNAL_URL not set. Using polling.")

# استدعاء الدالة هنا مباشرة لتعمل فوراً تحت بيئة تشغيل Gunicorn
set_webhook()

# ============================================
# START BOT
# ============================================
if __name__ == "__main__":
    # هذا البلوك سيعمل فقط إذا قمت بتشغيل الملف محلياً على جهازك كمود Polling
    if not RENDER_EXTERNAL_URL:
        logging.info("Starting bot (Polling mode)")
        bot.infinity_polling()
        

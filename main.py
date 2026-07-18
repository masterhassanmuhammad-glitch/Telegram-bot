import os
from threading import Thread
from flask import Flask

import config
from telebot import types
from database import init_db
from handlers import init_handlers

# إنشاء خادم ويب صغير ليستجيب لـ Health Check في Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":

    # تشغيل خادم الويب في Thread منفصل
    web_thread = Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    print("🌐 Health check server running...")

    print("⚡ جاري تهيئة قاعدة بيانات Neon...")
    init_db()

    print("⚙️ جاري تسجيل ومعالجة كافة الأوامر والملفات المقسمة...")
    init_handlers()

    # 🛠️ تعيين قائمة الأوامر (زر القائمة /start أسفل الشاشة)
    print("📋 جاري تعيين زر تشغيل البوت في القائمة...")
    config.bot.set_my_commands([
        types.BotCommand("start", "اضغط لعرض القائمة 🎓")
    ])

    # إلغاء أي Webhook قديم عالق
    config.bot.remove_webhook()

    print("🚀 تم تشغيل البوت بنجاح ويقوم بالبث التفاعلي الآن!")

    config.bot.infinity_polling(
        timeout=30,
        long_polling_timeout=30,
        skip_pending=True
    )

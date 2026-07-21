import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

# 1. قراءة متغيرات البيئة من Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DATABASE_URL = os.environ.get('DATABASE_URL')
ADMIN_IDS_RAW = os.environ.get('ADMIN_IDS', '')

# تحويل هويات الآدمنية إلى قائمة أرقام بشكل آمن
ADMIN_IDS = []
if ADMIN_IDS_RAW:
    try:
        ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(',') if x.strip()]
    except ValueError:
        print("Warning: ADMIN_IDS environment variable contains invalid integers.")

# تهيئة كائن البوت بشكل آمن
bot = None
if BOT_TOKEN:
    bot = telebot.TeleBot(BOT_TOKEN)
else:
    print("Warning: BOT_TOKEN environment variable is not set. Bot will not initialize correctly.")

# 2. خادم ويب مصغر لحل مشكلة توقف ريندر (Health Check Server)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Bot is alive and kicking!".encode('utf-8'))
    
    def log_message(self, format, *args):
        # منع تسجيل الطلبات العادية للحفاظ على نظافة سجلات ريندر (Logs)
        return

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server running on port {port}...")
    server.serve_forever()

# تشغيل خادم الويب في الخلفية بشكل منفصل
threading.Thread(target=run_health_server, daemon=True).start()
# config.py (تأكد من إضافة هذا السطر في نهاية الملف)

# تعريف معرف المالك (أول ID يتم وضعه في قائمة المشرفين بمتغيرات البيئة)
OWNER_ID = ADMIN_IDS[0] if ADMIN_IDS else None
# config.py
GROQ_API_KEY = "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"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- 1. خادم ويب وهمي (Health Check) لمنع Render من إعادة التشغيل التلقائي ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

    def log_message(self, format, *args):
        return  # لمنع امتلاء السجلات (Logs) بطلبات الفحص التلقائية

def run_health_server():
    # منصة Render تمرر المنفذ تلقائياً عبر المتغير PORT
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"خادم الفحص الوهمي بدأ يعمل على المنفذ: {port}")
    server.serve_forever()

# تشغيل خادم الويب في خلفية مستقلة (Thread) حتى لا يعطل البوت الأساسي
threading.Thread(target=run_health_server, daemon=True).start()


# --- 2. إعدادات حساب تليجرام الخاص بك ---
API_ID = 21481541
API_HASH = '1f6e29780a4009249ba62846bdba8e55'

# تم وضع كود الجلسة الخاص بك هنا بنجاح في السطر 33
STRING_SESSION = '1BJWap1sBu0gGf_PDcUxXsj1KqwTax_3GjNrCLRx8_ND-Sgu_wBNMORTlHR9nx-5vC7bfAPpl-AnfEGnVlvoH1ZxHw3q-kFPKS5rRlxlg46YwpmdO4-N7DY7lm1DmpqwWmDLXkNHye8qKnK2SSKwGHj-WlDOUVQlkZjOWPCRkC8NWx6TkIw34WZAqwq6sWnD8tjhDiWppdZTY5WVkIUFbG6tSAkWSjP_vRG-ja2xJIhm7fVhKWC5ZaGRTfbUDKa2vs9c-DZZgu8eoJbJfT4Q3EuIBZeUIyEpmDpM1RsSukXNFAsm85_waytZcyjK58CRTc5cuw8ULZKxiPndjZfgqngXzW4bqDzk='


# --- 3. كود البوت الأساسي وتشغيله ---
async def main():
    print("جاري بدء الاتصال بتليجرام...")
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("خطأ: الجلسة غير صالحة أو انتهت صلاحيتها، يرجى إعادة استخراجها من ترمكس.")
        return

    print("تم تسجيل الدخول بنجاح تام إلى حساب تليجرام!")
    print("البوت مستقر الآن في السحاب ويعمل بدون انقطاع.")
    
    # يظل البوت يعمل ويستمع لأي أوامر أو مهام في الخلفية
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

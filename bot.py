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
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"خادم الفحص الوهمي بدأ يعمل على المنفذ: {port}")
    server.serve_forever()

# تشغيل خادم الويب في خلفية مستقلة (Thread)
threading.Thread(target=run_health_server, daemon=True).start()


# --- 2. إعدادات حساب تليجرام وبوت النقاط الخاص بك ---
API_ID = 21481541
API_HASH = '1f6e29780a4009249ba62846bdba8e55'
BOT_USERNAME = 'Sudaniotpbot'

# كود الجلسة المستخرج من ترمكس الخاص بك مدمج هنا بالكامل
STRING_SESSION = '1BJWap1sBu0gGf_PDcUxXsj1KqwTax_3GjNrCLRx8_ND-Sgu_wBNMORTlHR9nx-5vC7bfAPpl-AnfEGnVlvoH1ZxHw3q-kFPKS5rRlxlg46YwpmdO4-N7DY7lm1DmpqwWmDLXkNHye8qKnK2SSKwGHj-WlDOUVQlkZjOWPCRkC8NWx6TkIw34WZAqwq6sWnD8tjhDiWppdZTY5WVkIUFbG6tSAkWSjP_vRG-ja2xJIhm7fVhKWC5ZaGRTfbUDKa2vs9c-DZZgu8eoJbJfT4Q3EuIBZeUIyEpmDpM1RsSukXNFAsm85_waytZcyjK58CRTc5cuw8ULZKxiPndjZfgqngXzW4bqDzk='


# --- 3. الدالة المسؤولة عن الضغط التلقائي على الزر ---
async def click_target_button():
    print("جاري بدء الاتصال بتليجرام...")
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("خطأ: الجلسة غير صالحة، يرجى إعادة استخراجها من ترمكس.")
        return

    print("تم تسجيل الدخول بنجاح! جاري البحث عن آخر رسالة من البوت للتفاعل معها...")
    
    # جلب آخر رسالة من البوت للتفاعل مع أزرارها
    async for message in client.iter_messages(BOT_USERNAME, limit=1):
        if message.buttons:
            for row in message.buttons:
                for button in row:
                    # البحث عن الزر المطلوب بناءً على النص المطابق تماماً
                    if "أخذ النقاط للكل" in button.text:
                        print(f"تم العثور على الزر: [{button.text}]. جاري الضغط التلقائي...")
                        await button.click()
                        print("تم الضغط بنجاح واكتملت المهمة السحابية!")
                        await client.disconnect()
                        return
    print("تنبيه: لم يتم العثور على الزر المطلوبة في آخر رسالة.")
    await client.disconnect()


# --- 4. حلقة التشغيل والتكرار التلقائي كل 24 ساعة ---
async def main():
    while True:
        try:
            await click_target_button()
        except Exception as e:
            print(f"حدث خطأ أثناء التنفيذ: {e}")
        
        # الانتظار لمدة 24 ساعة (بالثواني) قبل تكرار العملية تلقائياً
        print("في انتظار الدورة القادمة بعد 24 ساعة...")
        await asyncio.sleep(24 * 60 * 60)

if __name__ == '__main__':
    asyncio.run(main())

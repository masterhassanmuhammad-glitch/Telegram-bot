import os
import asyncio
from datetime import datetime
import zoneinfo
from http.server import BaseHTTPRequestHandler, HTTPServer
from telethon import TelegramClient
from telethon.sessions import StringSession

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

    def log_message(self, format, *args):  
        return

async def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.timeout = 0.1 
    print(f"📡 Web server started on port: {port}")
    while True:
        server.handle_request()
        await asyncio.sleep(0.5)

API_ID = 21481541
API_HASH = '1f6e29780a4009249ba62846bdba8e55'
BOT_USERNAME = 'Sudaniotpbot'
STRING_SESSION = '1BJWap1sBu0gGf_PDcUxXsj1KqwTax_3GjNrCLRx8_ND-Sgu_wBNMORTlHR9nx-5vC7bfAPpl-AnfEGnVlvoH1ZxHw3q-kFPKS5rRlxlg46YwpmdO4-N7DY7lm1DmpqwWmDLXkNHye8qKnK2SSKwGHj-WlDOUVQlkZjOWPCRkC8NWx6TkIw34WZAqwq6sWnD8tjhDiWppdZTY5WVkIUFbG6tSAkWSjP_vRG-ja2xJIhm7fVhKWC5ZaGRTfbUDKa2vs9c-DZZgu8eoJbJfT4Q3EuIBZeUIyEpmDpM1RsSukXNFAsm85_waytZcyjK58CRTc5cuw8ULZKxiPndjZfgqngXzW4bqDzk='

async def click_target_button():
    print("🔄 Connecting to Telegram for scheduled task...")
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():  
        print("❌ Session is invalid!")  
        await client.disconnect()
        return  

    print("✅ Logged in! Searching for messages...")  
    async for message in client.iter_messages(BOT_USERNAME, limit=1):  
        if message.buttons:  
            for row in message.buttons:  
                for button in row:  
                    if "أخذ النقاط للكل" in button.text:  
                        print(f"🎯 Clicking button: [{button.text}]")  
                        await button.click()  
                        print("🎉 Done successfully!")  
                        await client.disconnect()
                        return  
                        
    print("⚠️ Button not found!")  
    await client.disconnect()

async def bot_loop():
    sudan_tz = zoneinfo.ZoneInfo("Africa/Khartoum")
    print("⏳ Time check loop started. Monitoring for 11:00 AM Sudan time...")
    
    # متغير للتأكد من عدم التكرار في نفس الدقيقة
    already_run_today = False
    
    while True:
        try:
            now = datetime.now(sudan_tz)
            
            # الحالة 1: الفحص اليومي المعتاد عند الساعة 11:00 صباحاً تماماً
            if now.hour == 11 and now.minute == 00:
                if not already_run_today:
                    await click_target_button()
                    already_run_today = True
                    await asyncio.sleep(60) # تجميد مؤقت لمنع التكرار في نفس الدقيقة
            
            # الحالة 2: للبدء الفوري اليوم إذا تم الرفع الآن قبل 11:05
            elif now.hour == 11 and now.minute <= 5:
                if not already_run_today:
                    print("🚀 First run detection for today active...")
                    await click_target_button()
                    already_run_today = True
            
            # إعادة تصفير السماح بالتشغيل في أي ساعة أخرى من اليوم ليتهيأ للغد
            else:
                already_run_today = False
                
        except Exception as e:
            print(f"💥 Error in loop: {e}")
            
        await asyncio.sleep(30)

async def main():
    await asyncio.gather(
        run_health_server(),
        bot_loop()
    )

if __name__ == '__main__':
    asyncio.run(main())
    

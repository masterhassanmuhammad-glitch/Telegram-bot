import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 38998080  
API_HASH = '9cd16a3fc4d5c8fa54bc5740988334fc'  
BOT_USERNAME = 'Sudaniotpbot'  

# كود الجلسة المشفر الخاص بك مدمج وجاهز تماماً
STRING_SESSION = '1BJWap1sBu0gGf_PDcUxXsj1KqwTax_3GjNrCLRx8_ND-Sgu_wBNMORTlHR9nx-5vC7bfAPpl-AnfEGnVlvoH1ZxHw3q-kFPKS5rRlxlg46YwpmdO4-N7DY7lm1DmpqwWmDLXkNHye8qKnK2SSKwGHj-WlDOUVQlkZjOWPCRkC8NWx6TkIw34WZAqwq6sWnD8tjhDiWppdZTY5WVkIUFbG6tSAkWSjP_vRG-ja2xJIhm7fVhKWC5ZaGRTfbUDKa2vs9c-DZZgu8eoJbJfT4Q3EuIBZeUIyEpmDpM1RsSukXNFAsm85_waytZcyjK58CRTc5cuw8ULZKxiPndjZfgqngXzW4bqDzk='

async def click_target_button():
    print("جاري الاتصال بتليجرام باستخدام الـ String Session الثابتة...")
    async with TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH) as client:
        print("تم الاتصال بنجاح آمن ومستمر! جاري البحث عن آخر رسالة من البوت...")
        
        async for message in client.iter_messages(BOT_USERNAME, limit=1):
            if message.buttons:
                for row in message.buttons:
                    for button in row:
                        if "أخذ النقاط للكل" in button.text:
                            print(f"تم العثور على الزر: [{button.text}]. جاري الضغط...")
                            await button.click()
                            print("تم الضغط بنجاح واكتملت المهمة!")
                            return
        print("تنبيه: لم يتم العثور على الزر في آخر رسالة.")

async def main():
    while True:
        try:
            await click_target_button()
        except Exception as e:
            print(f"حدث خطأ أثناء التنفيذ: {e}")
        
        print("في انتظار الدورة القادمة بعد 24 ساعة...")
        await asyncio.sleep(24 * 60 * 60)

if __name__ == '__main__':
    asyncio.run(main())

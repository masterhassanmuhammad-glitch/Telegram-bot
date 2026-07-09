import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

# رابط المشروع على ريندر لاستقبال الـ Webhook (مثال: https://med-bot.onrender.com)
WEBHOOK_URL = os.getenv("WEBHOOK_URL") 

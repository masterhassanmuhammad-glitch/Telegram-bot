import os
import logging

# إعدادات تسجيل الأحداث (Logs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# توكن البوت من BotFather
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("API_TOKEN is missing.")

# رابط قاعدة البيانات
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing.")

# معرف مالك البوت (الأدمن الأساسي)
OWNER_ID = int(os.getenv("OWNER_ID", "8203001172"))

# رابط الويب هوك الخارجي (مهم لمنصة Render)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# المنفذ الخاص بالسيرفر
PORT = int(os.getenv("PORT", "5000"))

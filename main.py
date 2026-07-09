from fastapi import FastAPI, Request, Response, status
from contextlib import asynccontextmanager
from telegram import Update
from telegram.ext import Application
import uvicorn

from config import BOT_TOKEN, WEBHOOK_URL
from database import init_db, pool
from handlers.start import register_start_handlers
from handlers.admin import register_admin_handlers

# تهيئة تطبيق python-telegram-bot بنظام الـ Async
ptb_app = Application.builder().token(BOT_TOKEN).updater(None).build()

# تسجيل الـ Handlers المقسمة
register_start_handlers(ptb_app)
register_admin_handlers(ptb_app)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. إعداد قاعدة البيانات والـ Connection Pool عند الإقلاع
    await init_db()
    # 2. تهيئة البوت
    await ptb_app.initialize()
    # 3. ضبط رابط الـ Webhook في تيلجرام ليوجه التحديثات إلى ريندر
    await ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print(f"🚀 Webhook set successfully to {WEBHOOK_URL}/webhook")
    
    yield
    
    # عند إغلاق التطبيق (Shutdown)
    await ptb_app.bot.delete_webhook()
    await ptb_app.shutdown()
    await pool.close()

# تهيئة تطبيق FastAPI
app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def process_telegram_update(request: Request):
    """المسار المسؤول عن استقبال الـ Updates وتحويلها لمعالجة البوت فوراً"""
    try:
        req_body = await request.json()
        update = Update.de_json(req_body, ptb_app.bot)
        await ptb_app.process_update(update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error processing update: {e}")
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "Medical Bot v2 Running with Webhooks"}

if __name__ == "__main__":
    # تشغيل السيرفر محلياً أو للتجربة (في ريندر يتم التشغيل عبر سطر الأوامر تلقائياً)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
  

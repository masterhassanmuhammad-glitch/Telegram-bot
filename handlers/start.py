from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import pool

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT is_verified FROM users WHERE user_id = %s", (user_id,))
            user = await cursor.fetchone()
            
    if user and user[0]: # إذا كان موثقاً مسبقاً
        await update.message.reply_text("✨ مرحباً بك مجدداً في البوت الأكاديمي للدفعة الطبية.")
        # كود عرض القائمة الرئيسية
        return

    # طلب مشاركة رقم الهاتف للتحقق
    keyboard = [[KeyboardButton("📱 مشاركة رقم الهاتف للتحقق", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "أهلاً بك. للوصول للمحاضرات والمستندات، يرجى مشاركة رقم هاتفك للتحقق من قيدك بالدفعة الطبية:",
        reply_markup=reply_markup
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.effective_user.id
    phone = contact.phone_number.replace("+", "").strip()
    
    # التحقق وتحديث البيانات في Neon
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO users (user_id, phone_number, is_verified, username) VALUES (%s, %s, TRUE, %s) "
                "ON CONFLICT (user_id) DO UPDATE SET is_verified = TRUE",
                (user_id, phone, update.effective_user.username)
            )
            await conn.commit()
            
    await update.message.reply_text("✅ تم التحقق من هويتك بنجاح! تم فتح الصلاحيات الأكاديمية.", reply_markup=ReplyKeyboardRemove())

def register_start_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
  

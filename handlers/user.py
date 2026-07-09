# handlers/user.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from database import pool
from config import OWNER_ID

# ---------- 1. جزء التنقل واستعراض الأزرار والمحتوى (تم توحيده) ----------
async def user_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة تنقل الطلاب بين الأزرار واستعراض المحتوى الأكاديمي والميديا."""
    query = update.callback_query
    await query.answer()
    
    # استخراج الـ ID الخاص بالزر من الـ callback_data
    btn_id = int(query.data.split('_')[2])
    
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            # جلب بيانات الزر الحالي
            await cursor.execute("SELECT id, text, type, message_text, parent_id FROM inline_buttons WHERE id = %s", (btn_id,))
            button = await cursor.fetchone()
            
            if not button:
                return
                
            btn_id_db, text, btn_type, message_text, parent_id = button
            
            # إذا كان الزر عبارة عن مجلد فرعي (Submenu)
            if btn_type == 'submenu':
                await cursor.execute(
                    "SELECT id, text FROM inline_buttons WHERE parent_id = %s ORDER BY sort_order ASC", 
                    (btn_id,)
                )
                child_buttons = await cursor.fetchall()
                
                keyboard = []
                # بناء الأزرار الفرعية
                for cb_id, cb_text in child_buttons:
                    keyboard.append([InlineKeyboardButton(cb_text, callback_data=f"user_view_{cb_id}")])
                
                # إضافة أزرار العودة للخلف
                if parent_id:
                    keyboard.append([InlineKeyboardButton("🔙 عودة للخلف", callback_data=f"user_view_{parent_id}")])
                else:
                    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="user_main_root")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # تعديل الرسالة وعرض نص الزر المحدث من الآدمن
                await query.edit_message_text(
                    text=message_text or "اختر من الأقسام التالية:",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                
            # إذا كان الزر يحتوي على ملفات وميديا (Media)
            elif btn_type == 'media':
                await cursor.execute(
                    "SELECT content_type, file_id, text_caption FROM button_contents WHERE button_id = %s", 
                    (btn_id,)
                )
                contents = await cursor.fetchall()
                
                # إرسال الملفات والصور للطالب بشكل متتابع
                for content_type, file_id, text_caption in contents:
                    if content_type == 'document':
                        await context.bot.send_document(
                            chat_id=update.effective_chat.id, 
                            document=file_id, 
                            caption=text_caption
                        )
                    elif content_type == 'photo':
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id, 
                            photo=file_id, 
                            caption=text_caption
                        )
                    elif content_type == 'text':
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id, 
                            text=text_caption
                        )


# ---------- 2. جزء مراسلة الإدارة والإشعارات الفورية ----------
async def handle_incoming_student_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال رسائل الطلاب والتحقق من حساباتهم ثم جدولة الرسالة للآدمن."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "لا يوجد معرف"
    msg_text = update.message.text
    
    # 1. التأكد أولاً من أن الطالب مسجل وموثق رقمه
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT is_verified FROM users WHERE user_id = %s", (user_id,))
            res = await cursor.fetchone()
            
            if not res or not res[0]:
                await update.message.reply_text("⚠️ عذراً، يجب عليك تفعيل حسابك ومشاركة رقمك أولاً عبر أمر /start لتتمكن من مراسلة الإدارة.")
                return
                
            # 2. حفظ الرسالة في قاعدة البيانات بوضع الانتظار pending
            await cursor.execute(
                "INSERT INTO user_messages (user_id, username, message_id, text) VALUES (%s, %s, %s, %s) RETURNING id",
                (user_id, username, update.message.message_id, msg_text)
            )
            msg_db_id = (await cursor.fetchone())[0]
            await conn.commit()
            
    await update.message.reply_text("📥 تم استلام استفسارك بنجاح. تم جدولته في لوحة الإدارة وسيتم الرد عليك قريباً.")
    
    # 3. إرسال إشعار فوري للآدمن الأساسي (Notification System) مع زر الرد السريع
    keyboard = [
        [
            InlineKeyboardButton("✍️ رد سريع", callback_data=f"adm_reply:{msg_db_id}:{user_id}"),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"adm_delmsg:{msg_db_id}")
        ]
    ]
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"🔔 **إشعار وارد:** وصلتك رسالة جديدة من الطالب: @{username}\n📝 **نص الرسالة:**\n{msg_text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------- 3. دالة تسجيل المعالجات الموحدة ----------
def register_user_handlers(application):
    """تسجيل جميع معالجات واجهة الطالب (التنقل والمراسلة)."""
    # معالج الضغط على أزرار التنقل وعرض المحتوى
    application.add_handler(CallbackQueryHandler(user_navigation, pattern="^user_view_"))
    
    # معالج استقبال الرسائل النصية من الطلاب لغرض المراسلة والتواصل (تأكد من وضعه في النهاية)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_student_feedback))
            

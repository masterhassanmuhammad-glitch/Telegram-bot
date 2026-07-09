from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from database import pool
from config import OWNER_ID

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # للتبسيط، نتحقق من الـ Owner ID (ويمكنك التوسع لجلب جداول المشرفين وصلاحياتهم)
    if update.effective_user.id != OWNER_ID:
        return

    keyboard = [
        [InlineKeyboardButton("🛠️ إدارة الأزرار، الرسائل والهيكلية", callback_data="adm_manage:root")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎛️ **لوحة التحكم المتكاملة من داخل البوت:**", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("adm_manage:"):
        parent_str = data.split(":")[1]
        parent_id = None if parent_str == "root" else int(parent_str)
        
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                # جلب الأزرار التابعة لهذا المستوى مرتبة تصاعدياً
                if parent_id is None:
                    await cursor.execute("SELECT id, text, type, message_text FROM inline_buttons WHERE parent_id IS NULL ORDER BY sort_order ASC")
                else:
                    await cursor.execute("SELECT id, text, type, message_text FROM inline_buttons WHERE parent_id = %s ORDER BY sort_order ASC", (parent_id,))
                buttons = await cursor.fetchall()
                
        keyboard = []
        for b in buttons:
            # زر الإدارة وزرين للترتيب بالأسهم الصاعدة والهابطة لتغيير الـ sort_order ديناميكياً
            keyboard.append([
                InlineKeyboardButton(f"⚙️ {b[1]}", callback_data=f"adm_edit:{b[0]}"),
                InlineKeyboardButton("⬆️", callback_data=f"adm_order:up:{b[0]}"),
                InlineKeyboardButton("⬇️", callback_data=f"adm_order:down:{b[0]}")
            ])
            
        keyboard.append([
            InlineKeyboardButton("➕ إضافة مجلد فرعي", callback_data=f"adm_create:sub:{parent_str}"),
            InlineKeyboardButton("➕ إضافة قسم ملفات وميدِيا", callback_data=f"adm_create:med:{parent_str}")
        ])
        
        if parent_id:
            keyboard.append([InlineKeyboardButton("📝 تعديل الرسالة المرتبطة بهذا الزر", callback_data=f"adm_modmsg:{parent_id}")])
            keyboard.append([InlineKeyboardButton("🔙 العودة للخلف", callback_data="adm_manage:root")]) # يمكنك جعلها ديناميكية للحفظ الشجري العميق
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📂 **تحكم بالأزرار وهيكلية الأقسام ورسائلها:**", reply_markup=reply_markup, parse_mode="Markdown")

    elif data.startswith("adm_edit:"):
        btn_id = int(data.split(":")[1])
        
        keyboard = [
            [InlineKeyboardButton("✏️ تعديل اسم/نص الزر نفسه", callback_data=f"adm_action:name:{btn_id}")],
            [InlineKeyboardButton("🔄 نقل الزر إلى داخل زر آخر (مجلد آخر)", callback_data=f"adm_action:move:{btn_id}")],
            [InlineKeyboardButton("🗑️ حذف الزر بالكامل وما بداخلة", callback_data=f"adm_action:del:{btn_id}")],
            [InlineKeyboardButton("🔙 عودة للقائمة", callback_data="adm_manage:root")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"🛠️ خيارات التحكم بالزر الحالي (ID: {btn_id}):\\nيمكنك تعديل أي تفاصيل، نقل الزر، أو حذفه بشكل صامت ودائم.", reply_markup=reply_markup)

def register_admin_handlers(application):
    application.add_handler(CallbackQueryHandler(handle_admin_callbacks, pattern="^(adm_manage:|adm_edit:|adm_order:|adm_create:|adm_modmsg:)"))
      

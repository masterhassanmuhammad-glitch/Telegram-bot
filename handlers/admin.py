# handlers/admin.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, MessageHandler, filters,
    CallbackQueryHandler, CommandHandler
)
from database import pool
from config import OWNER_ID


# ---------- دوال مساعدة ----------
async def check_permission(user_id: int, permission_column: str) -> bool:
    """التحقق من صلاحية مشرف معين في قاعدة البيانات."""
    if user_id == OWNER_ID:
        return True
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                f"SELECT {permission_column} FROM admins WHERE user_id = %s",
                (user_id,)
            )
            res = await cursor.fetchone()
            return res[0] if res else False


# ---------- 1. إدارة المحتوى (ملفات، مستندات، نصوص) داخل الأزرار ----------
async def start_add_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء رفع محتوى لزر معين (يُستدعى من كليك على زر إداري)."""
    query = update.callback_query
    btn_id = int(query.data.split(":")[2])

    if not await check_permission(update.effective_user.id, "can_edit_buttons"):
        await query.answer("❌ لا تملك صلاحية تعديل المحتوى الأكاديمي.", show_alert=True)
        return

    context.user_data["upload_to_btn"] = btn_id
    await query.edit_message_text(
        "📥 **أرسل الآن أي شيء:** (مستند PDF، صورة، محاضرة، أو نص عادي) "
        "ليتم حفظه داخل هذا الزر فوراً:"
    )


async def process_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الملف/النص المرسل من الآدمن لحفظه في قاعدة البيانات."""
    btn_id = context.user_data.get("upload_to_btn")
    if not btn_id:
        return  # ليس في وضع الرفع

    msg = update.message
    content_type = None
    file_id = None
    caption = msg.caption or msg.text or ""

    if msg.document:
        content_type = "document"
        file_id = msg.document.file_id
    elif msg.photo:
        content_type = "photo"
        file_id = msg.photo[-1].file_id  # أعلى جودة
    elif msg.text:
        content_type = "text"
        caption = msg.text

    if content_type:
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO button_contents (button_id, content_type, file_id, text_caption) "
                    "VALUES (%s, %s, %s, %s)",
                    (btn_id, content_type, file_id, caption)
                )
                await conn.commit()

        context.user_data.pop("upload_to_btn", None)
        await msg.reply_text(
            "✅ تم حفظ الملف والمحتوى الأكاديمي بنجاح داخل قاعدة بيانات Neon المربوطة بالزر!"
        )


# ---------- 2. عرض رسائل الطلاب والرد عليها ----------
async def view_incoming_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة الرسائل المعلقة من الطلاب (الأقدم فالأحدث)."""
    query = update.callback_query
    if not await check_permission(update.effective_user.id, "can_respond_messages"):
        await query.answer("❌ لا تملك صلاحية الرد على رسائل الطلاب.", show_alert=True)
        return

    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT id, user_id, username, text FROM user_messages "
                "WHERE status = 'pending' ORDER BY id ASC"
            )
            messages = await cursor.fetchall()

    if not messages:
        await query.edit_message_text("📥 لا توجد رسائل معلقة أو استفسارات من الطلاب حالياً.")
        return

    await query.message.reply_text("📥 **الرسائل الواردة من الطلاب المرتبة (الأقدم فالأحدث):**")
    for msg_db_id, u_id, username, text in messages:
        keyboard = [
            [
                InlineKeyboardButton("✍️ رد سريع", callback_data=f"adm_reply:{msg_db_id}:{u_id}"),
                InlineKeyboardButton("🗑️ حذف الرسالة", callback_data=f"adm_delmsg:{msg_db_id}")
            ]
        ]
        await query.message.reply_text(
            f"👤 **الطالب:** {u_id} (@{username})\n📝 **الرسالة:**\n{text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_msg_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار الرد أو الحذف على رسائل الطلاب."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    action = parts[0]
    msg_db_id = int(parts[1])

    if action == "adm_delmsg":
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM user_messages WHERE id = %s", (msg_db_id,))
                await conn.commit()
        await query.message.delete()

    elif action == "adm_reply":
        target_student_id = int(parts[2])
        context.user_data["reply_to_student"] = (target_student_id, msg_db_id)
        await query.message.reply_text("✍️ أرسل ردك الآن ليتم توجيهه للطالب عبر البوت:")


async def send_reply_to_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رد الآدمن إلى الطالب وتحديث حالة الرسالة."""
    reply_info = context.user_data.get("reply_to_student")
    if not reply_info:
        return

    student_id, msg_db_id = reply_info
    reply_text = update.message.text

    try:
        await context.bot.send_message(
            chat_id=student_id,
            text=f"💬 **رد رسمي من إدارة الدفعة الطبية:**\n\n{reply_text}",
            parse_mode="Markdown"
        )

        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE user_messages SET status = 'replied' WHERE id = %s",
                    (msg_db_id,)
                )
                await conn.commit()

        context.user_data.pop("reply_to_student", None)
        await update.message.reply_text("✅ تم إرسال الرد وتحديث قاعدة البيانات بنجاح.")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل إرسال الرد. قد يكون الطالب قد حظر البوت. الخطأ: {e}")


# ---------- 3. لوحة التحكم الإدارية الرئيسية (الأزرار، الهيكلية) ----------
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض القائمة الرئيسية للإدارة (يُستدعى بواسطة /admin)."""
    if update.effective_user.id != OWNER_ID:
        return

    keyboard = [
        [InlineKeyboardButton("🛠️ إدارة الأزرار، الرسائل والهيكلية", callback_data="adm_manage:root")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎛️ **لوحة التحكم المتكاملة من داخل البوت:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج جميع استعلامات الإدارة الخاصة بالأزرار والهيكلية.
    يشمل: عرض الأقسام، تعديل الأزرار، ترتيبها، إضافة فروع، وتعديل الرسائل.
    """
    query = update.callback_query
    await query.answer()
    data = query.data

    # ----- adm_manage: عرض أزرار مستوى معين -----
    if data.startswith("adm_manage:"):
        parent_str = data.split(":")[1]
        parent_id = None if parent_str == "root" else int(parent_str)

        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                if parent_id is None:
                    await cursor.execute(
                        "SELECT id, text, type, message_text FROM inline_buttons "
                        "WHERE parent_id IS NULL ORDER BY sort_order ASC"
                    )
                else:
                    await cursor.execute(
                        "SELECT id, text, type, message_text FROM inline_buttons "
                        "WHERE parent_id = %s ORDER BY sort_order ASC",
                        (parent_id,)
                    )
                buttons = await cursor.fetchall()

        keyboard = []
        for btn in buttons:
            btn_id, btn_text, btn_type, msg_text = btn
            keyboard.append([
                InlineKeyboardButton(f"⚙️ {btn_text}", callback_data=f"adm_edit:{btn_id}"),
                InlineKeyboardButton("⬆️", callback_data=f"adm_order:up:{btn_id}"),
                InlineKeyboardButton("⬇️", callback_data=f"adm_order:down:{btn_id}")
            ])

        keyboard.append([
            InlineKeyboardButton("➕ إضافة مجلد فرعي", callback_data=f"adm_create:sub:{parent_str}"),
            InlineKeyboardButton("➕ إضافة قسم ملفات وميديا", callback_data=f"adm_create:med:{parent_str}")
        ])

        if parent_id is not None:
            keyboard.append([
                InlineKeyboardButton("📝 تعديل الرسالة المرتبطة بهذا الزر", callback_data=f"adm_modmsg:{parent_id}")
            ])
            keyboard.append([
                InlineKeyboardButton("🔙 العودة للخلف", callback_data="adm_manage:root")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📂 **تحكم بالأزرار وهيكلية الأقسام ورسائلها:**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    # ----- adm_edit: خيارات تعديل زر معين -----
    elif data.startswith("adm_edit:"):
        btn_id = int(data.split(":")[1])
        keyboard = [
            [InlineKeyboardButton("✏️ تعديل اسم/نص الزر نفسه", callback_data=f"adm_action:name:{btn_id}")],
            [InlineKeyboardButton("🔄 نقل الزر إلى داخل زر آخر (مجلد آخر)", callback_data=f"adm_action:move:{btn_id}")],
            [InlineKeyboardButton("🗑️ حذف الزر بالكامل وما بداخلة", callback_data=f"adm_action:del:{btn_id}")],
            [InlineKeyboardButton("🔙 عودة للقائمة", callback_data="adm_manage:root")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🛠️ خيارات التحكم بالزر الحالي (ID: {btn_id}):\n"
            "يمكنك تعديل أي تفاصيل، نقل الزر، أو حذفه بشكل صامت ودائم.",
            reply_markup=reply_markup
        )

    # ----- adm_order: تغيير ترتيب الزر (⬆️ ⬇️) -----
    elif data.startswith("adm_order:"):
        _, direction, btn_id = data.split(":")
        btn_id = int(btn_id)
        # (هنا يمكن تنفيذ منطق تغيير sort_order، لكن نتركه كمثال)
        await query.edit_message_text(
            f"🔄 تم تغيير ترتيب الزر {btn_id} إلى {'أعلى' if direction == 'up' else 'أسفل'} (وهمي)."
        )

    # ----- adm_create: إضافة مجلد فرعي أو قسم ميديا -----
    elif data.startswith("adm_create:"):
        _, sub_type, parent_str = data.split(":")
        parent = None if parent_str == "root" else int(parent_str)
        await query.edit_message_text(
            f"🧩 إضافة {'مجلد فرعي' if sub_type == 'sub' else 'قسم ميديا'} تحت الأب {parent} (وهمي)."
        )

    # ----- adm_modmsg: تعديل رسالة الزر -----
    elif data.startswith("adm_modmsg:"):
        btn_id = int(data.split(":")[1])
        await query.edit_message_text(
            f"✏️ تعديل الرسالة المرتبطة بالزر {btn_id} (وهمي)."
        )

    # ----- adm_action: عمليات فرعية (تعديل اسم، نقل، حذف) -----
    elif data.startswith("adm_action:"):
        # هذه تُستدعى من داخل adm_edit، نتعامل معها بشكل مبسط
        parts = data.split(":")
        action = parts[1]
        btn_id = int(parts[2])
        if action == "name":
            await query.edit_message_text(f"✏️ تعديل اسم الزر {btn_id} (وهمي).")
        elif action == "move":
            await query.edit_message_text(f"🔄 نقل الزر {btn_id} (وهمي).")
        elif action == "del":
            await query.edit_message_text(f"🗑️ حذف الزر {btn_id} (وهمي).")


# ---------- تسجيل جميع المعالجات ----------
def register_admin_handlers(application):
    """تسجيل جميع معالجات الإدارة في التطبيق."""
    # أمر /admin
    application.add_handler(CommandHandler("admin", admin_menu))

    # معالجات رفع المحتوى (ملفات ونصوص)
    application.add_handler(
        CallbackQueryHandler(start_add_content, pattern="^adm_action:addcontent:")
    )
    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND & filters.Chat(OWNER_ID),
            process_file_upload
        )
    )

    # معالجات رسائل الطلاب
    application.add_handler(
        CallbackQueryHandler(view_incoming_messages, pattern="^adm_view_msgs$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_msg_actions, pattern="^(adm_reply:|adm_delmsg:)")
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Chat(OWNER_ID),
            send_reply_to_student
        )
    )

    # معالجات الإدارة الشاملة (القوائم، التعديل، الترتيب، الإضافة، ...)
    application.add_handler(
        CallbackQueryHandler(
            handle_admin_callbacks,
            pattern="^(adm_manage:|adm_edit:|adm_order:|adm_create:|adm_modmsg:|adm_action:)"
        )
    )

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

# استيراد خدمات إدارة الحالات والمسؤولين
from services.admin_state import set as set_admin_state, get as get_admin_state, clear as clear_admin_state
from services.admins_service import is_admin
from services import menus_service


async def admin_menus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    menus = menus_service.all()
    text = "📂 إدارة الأقسام\n\n"

    if not menus:
        text += "لا توجد أقسام."
    else:
        for menu in menus:
            icon = menu.get("icon") or "📁"
            text += f"{icon} {menu['id']} - {menu['title']}\n"

    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ إضافة قسم", callback_data="admin:add_menu")
        ],
        [
            InlineKeyboardButton("✏️ تعديل قسم", callback_data="admin:edit_menu"),
            InlineKeyboardButton("🗑 حذف قسم", callback_data="admin:delete_menu")
        ],
        [
            InlineKeyboardButton("⬆️ ترتيب الأقسام", callback_data="admin:sort_menu")
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="admin:panel")
        ]
    ])

    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup
    )


async def add_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    # تعيين حالة الأدمن
    set_admin_state(
        query.from_user.id,
        "ADD_MENU"
    )

    # التعديل الثاني: تعديل الرسالة الحالية بدل إرسال رسالة جديدة لمنع التراكم
    await query.edit_message_text(
        "📂 أرسل اسم القسم الجديد:"
    )


async def admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    state = get_admin_state(user.id)

    if not state:
        return

    # التعديل الأول: الفحص المباشر للحالة بناءً على هيكلة الـ dict المتفق عليها
    if state["action"] == "ADD_MENU":
        
        # إنشاء القسم في قاعدة البيانات
        menus_service.create(
            title=update.message.text,
            parent_id=0,
            description="",
            icon="📁",
            sort_order=0,
            visible=True
        )

        # التعديل الثالث والمهم جداً لإعادة إظهار لوحة التحكم المحدثة بشكل نظيف:
        
        # 1. مسح حالة الأدمن
        clear_admin_state(user.id)

        # 2. حذف رسالة المستخدم النصية التي تحتوي على الاسم
        await update.message.delete()

        # 3. جلب الأقسام المحدثة وبناء اللوحة من جديد
        menus = menus_service.all()
        text = "📂 إدارة الأقسام\n\n"

        if not menus:
            text += "لا توجد أقسام."
        else:
            for menu in menus:
                icon = menu.get("icon") or "📁"
                text += f"{icon} {menu['id']} - {menu['title']}\n"

        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ إضافة قسم", callback_data="admin:add_menu")
            ],
            [
                InlineKeyboardButton("✏️ تعديل قسم", callback_data="admin:edit_menu"),
                InlineKeyboardButton("🗑 حذف قسم", callback_data="admin:delete_menu")
            ],
            [
                InlineKeyboardButton("⬆️ ترتيب الأقسام", callback_data="admin:sort_menu")
            ],
            [
                InlineKeyboardButton("🔙 رجوع", callback_data="admin:panel")
            ]
        ])

        # 4. إرسال اللوحة المحدثة للمستخدم في رسالة جديدة لتكون هي رسالة التحكم الوحيدة النشطة
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup
        )


def register(application):
    application.add_handler(
        CallbackQueryHandler(
            admin_menus,
            pattern=r"^admin:menus$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            add_menu_start,
            pattern=r"^admin:add_menu$"
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_messages
        )
    )
    

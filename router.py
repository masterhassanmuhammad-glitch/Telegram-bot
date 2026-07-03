import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

# استيراد الخدمات التي قمنا ببنائها سابقاً
from services.user_service import UserService
from services.session_service import SessionService
from services.menu_service import MenuService
from services.content_service import ContentService
from services.setting_service import SettingService

logger = logging.getLogger(__name__)

# --- دالة مساعدة لبناء لوحة الأزرار (Inline Keyboard) ديناميكياً ---
def build_keyboard(menu_id: int, user_id: int) -> InlineKeyboardMarkup:
    # 1. جلب الأزرار التابعة لهذه القائمة من قاعدة البيانات
    buttons_data = MenuService.get_menu_buttons(menu_id)
    # 2. جلب إعدادات عرض الصفوف لهذه القائمة
    menu_info = MenuService.get_menu(menu_id)
    row_width = menu_info['row_width'] if menu_info else 2

    keyboard = []
    current_row = []

    for btn in buttons_data:
        text = f"{btn['emoji'] or ''} {btn['text']}".strip()
        # نضع معرف الزر داخل الـ callback_data ليتعرف عليه الـ Router عند الضغط
        callback_data = f"btn_{btn['id']}"
        current_row.append(InlineKeyboardButton(text, callback_data=callback_data))

        if len(current_row) == row_width:
            keyboard.append(current_row)
            current_row = []

    if current_row:
        keyboard.append(current_row)

    # 3. إذا كان المستخدم آدمن، ندمج زر إدارة خاص بهذا القسم أسفل الأزرار مباشرة
    if UserService.is_admin(user_id):
        keyboard.append([InlineKeyboardButton("🛠️ إدارة هذا القسم", callback_data=f"manage_menu_{menu_id}")])

    # 4. إضافة زر عودة تلقائي إذا لم نكن في القائمة الرئيسية (ID = 1)
    if menu_id != 1:
        keyboard.append([InlineKeyboardButton("🔙 عودة للرئيسية", callback_data="btn_back_main")])

    return InlineKeyboardMarkup(keyboard)


# --- معالج الأمر الموحد /start ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # التحقق من القناة (يمكنك ربط دالة فحص القناة هنا مستقبلاً)
    
    # 1. تسجيل أو تحديث بيانات المستخدم في Neon
    UserService.register_or_update_user(user_id, user.username, user.first_name)
    
    # 2. جلب أو تصفير جلسة المستخدم
    SessionService.clear_session_context(user_id)
    
    # 3. جلب رسالة الترحيب الافتراضية من الإعدادات
    welcome_text = SettingService.get_setting("welcome_message", "🏥 مرحباً بك في البوت:")
    
    # 4. بناء الأزرار الديناميكية للقائمة الرئيسية (ID = 1)
    reply_markup = build_keyboard(menu_id=1, user_id=user_id)
    
    # 5. إرسال الرسالة وحفظ الـ message_id الخاص بها لتعديلها لاحقاً
    msg = await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    SessionService.update_session(user_id, message_id=msg.message_id, menu_id=1)


# --- معالج الضغط على أزرار الـ Inline (Callback Queries) ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # لإيقاف علامة التحميل الفوقية في تليجرام
    
    user_id = query.from_user.id
    data = query.data
    session = SessionService.get_session(user_id)

    # 1. زر العودة إلى القائمة الرئيسية
    if data == "btn_back_main":
        welcome_text = SettingService.get_setting("welcome_message", "🏥 مرحباً بك في البوت:")
        reply_markup = build_keyboard(menu_id=1, user_id=user_id)
        
        await query.edit_message_text(text=welcome_text, reply_markup=reply_markup)
        SessionService.update_session(user_id, menu_id=1, state="MAIN_MENU")
        return

    # 2. معالجة الضغط على أزرار التصفح والمحتوى الديناميكية
    if data.startswith("btn_"):
        btn_id = int(data.split("_")[1])
        
        # جلب بيانات الزر المضغوط لمعرفة الأكشن الخاص به
        # (ملاحظة: تحتاج لإضافة دالة get_button في menu_service، سنفترض أنها تجلب السجل)
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM buttons WHERE id = %s", (btn_id,))
        btn = cursor.fetchone()
        cursor.close()
        DatabaseManager.release_connection(conn)

        if not btn:
            await query.answer("❌ هذا الزر لم يعد متوفراً.", show_alert=True)
            return

        # أ. إذا كان الزر يفتح قائمة فرعية (Sub-menu)
        if btn['type'] == 'menu':
            next_menu_id = int(btn['action_value'])
            reply_markup = build_keyboard(menu_id=next_menu_id, user_id=user_id)
            
            # تعديل نفس الرسالة الفوقية
            await query.edit_message_text(text=f"📂 القسم: {btn['text']}", reply_markup=reply_markup)
            SessionService.update_session(user_id, menu_id=next_menu_id)
            
        # ب. إذا كان الزر يعرض محتوى ووسائط (Content & Media Library)
        elif btn['type'] == 'content':
            contents = ContentService.get_button_contents(btn_id)
            
            if not contents:
                no_files_msg = SettingService.get_setting("no_files_message", "❌ لا توجد ملفات هنا.")
                await query.answer(no_files_msg, show_alert=True)
                return
            
            # تنظيف الرسالة الفوقية الرئيسية لتهيئة الشاشة لعرض الميديا
            await query.edit_message_text(text=f"⏳ جاري تحميل محتويات: {btn['text']}...")

            # إرسال المحتويات والوسائط المتعددة بالتوالي للمستخدم
            for content in contents:
                if content['text_content']:
                    await context.bot.send_message(chat_id=user_id, text=content['text_content'])
                
                # جلب الوسائط المرتبطة بهذا المحتوى من مكتبة الوسائط
                media_list = ContentService.get_content_media(content['id'])
                for media in media_list:
                    f_id = media['file_id']
                    f_type = media['type']
                    caption = media['caption']
                    
                    if f_type == 'photo':
                        await context.bot.send_photo(chat_id=user_id, photo=f_id, caption=caption)
                    elif f_type == 'document':
                        await context.bot.send_document(chat_id=user_id, document=f_id, caption=caption)
                    elif f_type == 'video':
                        await context.bot.send_video(chat_id=user_id, video=f_id, caption=caption)
            
            # إعادة إرسال رسالة تحكم جديدة نظيفة لتصبح هي الرسالة الفوقية المعتمدة للعمليات التالية
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة للقائمة السابقة", callback_data=f"btn_back_to_menu_{session['current_menu_id']}")]])
            new_msg = await context.bot.send_message(chat_id=user_id, text="✨ تم عرض كافة الملفات بنجاح.", reply_markup=back_keyboard)
            
            # تحديث الـ message_id في الجلسة ليتم التفاعل مع هذه الرسالة الجديدة في المرات القادمة
            SessionService.update_session(user_id, message_id=new_msg.message_id)

    # 3. زر العودة لقسم فرعي محدد بعد عرض الملفات
    elif data.startswith("btn_back_to_menu_"):
        menu_id = int(data.split("_")[4])
        reply_markup = build_keyboard(menu_id=menu_id, user_id=user_id)
        await query.edit_message_text(text="📂 يرجى اختيار أحد الخيارات:", reply_markup=reply_markup)
        SessionService.update_session(user_id, menu_id=menu_id)


# --- معالج الرسائل النصية المباشرة (Text & Inputs) لإدخال البيانات كـ FSM ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    session = SessionService.get_session(user_id)
    
    # حذف رسالة إدخال المستخدم فوراً للحفاظ على نظافة الشات تماماً
    try:
        await update.message.delete()
    except Exception:
        pass

    # فحص حالة المستخدم الحالية (FSM) لاتخاذ الإجراء المناسب (لوحة التحكم للآدمن مثلاً)
    if session['current_state'] == 'WAITING_FOR_WELCOME_MSG' and UserService.is_admin(user_id):
        # تعديل رسالة الترحيب في قاعدة البيانات فوراً
        SettingService.set_setting("welcome_message", text)
        SessionService.update_session(user_id, state="MAIN_MENU")
        
        # جلب الرسالة الفوقية القديمة وتحديثها بإشعار النجاح
        reply_markup = build_keyboard(menu_id=1, user_id=user_id)
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=session['last_message_id'],
            text=f"✅ تم تغيير رسالة الترحيب بنجاح إلى:\n\n{text}",
            reply_markup=reply_markup
  )
      

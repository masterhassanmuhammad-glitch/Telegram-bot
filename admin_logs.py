from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, OWNER_ID
from config import bot
from database import execute_query

def register_logs_handlers():
    """
    تسجيل جميع معالجات لوحة السجلات (العرض والحذف لـ /start و /ask)
    """

    # 1️⃣ القائمة الرئيسية للوحة التحكم بالسجلات
    # 1. القائمة الرئيسية للوحة السجلات
    @bot.callback_query_handler(func=lambda call: call.data == "admin_logs_menu")
    def cb_admin_logs_menu(call):
        # 🔒 حماية: المالك فقط من يصل لهذه اللوحة
        if call.from_user.id != OWNER_ID:
            bot.answer_callback_query(call.id, "❌ هذه اللوحة مخصصة لمالك البوت فقط!", show_alert=True)
            return

        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📊 سجلات /start", callback_data="view_start_logs"))
        markup.add(InlineKeyboardButton("🤖 سجلات /ask (الأسئلة)", callback_data="view_ask_logs"))
        
        # 🟢 زر العودة للقائمة الرئيسية
        markup.add(InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="⚙️ *لوحة التحكم بالسجلات*\n\nاختر نوع السجلات التي تريد استعراضها أو مسحها من قاعدة البيانات:",
            parse_mode="Markdown",
            reply_markup=markup
        )
        

    # 2️⃣ عرض سجلات /start + زر الحذف
    @bot.callback_query_handler(func=lambda call: call.data == "view_start_logs")
    def cb_view_start_logs(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        
        # جلب إجمالي عدد سجلات start
        count_res = execute_query("SELECT COUNT(*) FROM command_logs WHERE command = '/start';", fetch=True)
        total_count = count_res[0][0] if count_res else 0
        
        # جلب آخر 10 مستخدمين شغلوا /start
        logs = execute_query(
            "SELECT user_id, username, created_at FROM command_logs WHERE command = '/start' ORDER BY id DESC LIMIT 10;",
            fetch=True
        )
        
        text = f"📊 *سجل استخدام /start*\n📦 *إجمالي السجلات المخزنة:* {total_count}\n\n"
        if logs:
            text += "🔻 *آخر 10 مستخدمين:*\n"
            for u_id, u_name, c_at in logs:
                date_str = c_at.strftime("%Y-%m-%d %H:%M") if c_at else "N/A"
                text += f"• `{u_id}` | @{u_name} ({date_str})\n"
        else:
            text += "⚠️ لا توجد سجلات حالياً."
            
        markup = InlineKeyboardMarkup()
        if total_count > 0:
            markup.add(InlineKeyboardButton("🗑️ مسح جميع سجلات /start", callback_data="clear_start_logs"))
        markup.add(InlineKeyboardButton("🔙 العودة", callback_data="admin_logs_menu"))
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=markup
        )

    # 3️⃣ تنفيذ مسح جميع سجلات /start
    @bot.callback_query_handler(func=lambda call: call.data == "clear_start_logs")
    def cb_clear_start_logs(call):
        execute_query("DELETE FROM command_logs WHERE command = '/start';", commit=True)
        bot.answer_callback_query(call.id, "✅ تم مسح جميع سجلات /start بنجاح!", show_alert=True)
        cb_view_start_logs(call)

    # 4️⃣ عرض سجلات /ask (الأسئلة) + زر الحذف
    @bot.callback_query_handler(func=lambda call: call.data == "view_ask_logs")
    def cb_view_ask_logs(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        
        # جلب إجمالي عدد أسئلة الذكاء الاصطناعي
        count_res = execute_query("SELECT COUNT(*) FROM command_logs WHERE command = '/ask';", fetch=True)
        total_count = count_res[0][0] if count_res else 0
        
        # جلب آخر 10 أسئلة مع المحتوى
        logs = execute_query(
            "SELECT user_id, username, prompt, created_at FROM command_logs WHERE command = '/ask' ORDER BY id DESC LIMIT 10;",
            fetch=True
        )
        
        text = f"🤖 *سجل أسئلة /ask*\n📦 *إجمالي الأسئلة المخزنة:* {total_count}\n\n"
        if logs:
            text += "🔻 *آخر 10 أسئلة:*\n\n"
            for u_id, u_name, prompt, c_at in logs:
                date_str = c_at.strftime("%Y-%m-%d %H:%M") if c_at else "N/A"
                p_text = prompt[:70] + "..." if prompt and len(prompt) > 70 else (prompt or "بدون نص")
                text += f"👤 @{u_name} (`{u_id}`) - {date_str}\n❓ `{p_text}`\n──────────────────\n"
        else:
            text += "⚠️ لا توجد سجلات أسئلة حالياً."
            
        markup = InlineKeyboardMarkup()
        if total_count > 0:
            markup.add(InlineKeyboardButton("🗑️ مسح جميع سجلات /ask", callback_data="clear_ask_logs"))
        markup.add(InlineKeyboardButton("🔙 العودة", callback_data="admin_logs_menu"))
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=markup
        )

    # 5️⃣ تنفيذ مسح جميع سجلات /ask
    @bot.callback_query_handler(func=lambda call: call.data == "clear_ask_logs")
    def cb_clear_ask_logs(call):
        execute_query("DELETE FROM command_logs WHERE command = '/ask';", commit=True)
        bot.answer_callback_query(call.id, "✅ تم مسح جميع سجلات /ask بنجاح!", show_alert=True)
        cb_view_ask_logs(call)

def create_logs_table_if_not_exists():
    query = """
    CREATE TABLE IF NOT EXISTS command_logs (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        username VARCHAR(255),
        command VARCHAR(50) NOT NULL,
        prompt TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    execute_query(query, commit=True)
    

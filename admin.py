from telebot.types import Message, CallbackQuery

from config import OWNER_ID
from database import execute, delete_item_recursive
from keyboards import admin_keyboard

# ============================================
# SIMPLE ADMIN STATE (IN MEMORY)
# ============================================
admin_state = {}


# ============================================
# CHECK ADMIN
# ============================================
def is_admin(user_id):
    result = execute(
        "SELECT user_id FROM admins WHERE user_id=%s",
        (user_id,),
        fetchone=True
    )
    return result is not None or user_id == OWNER_ID


# ============================================
# ADMIN PANEL START
# ============================================
def register_admin_handlers(bot):

    # ========================================
    # OPEN ADMIN PANEL
    # ========================================
    @bot.message_handler(commands=['admin'])
    def admin_panel(message: Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ غير مصرح لك")
            return

        bot.send_message(
            message.chat.id,
            "⚙️ لوحة التحكم للادارة:",
            reply_markup=admin_keyboard()
        )


    # ========================================
    # ADD ITEM START (CALLBACK)
    # ========================================
    @bot.callback_query_handler(func=lambda call: call.data == "admin_add_item")
    def add_item_start(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        if not is_admin(call.from_user.id):
            bot.send_message(call.message.chat.id, "❌ غير مصرح لك")
            return

        admin_state[call.from_user.id] = {"action": "add_item"}
        bot.send_message(call.message.chat.id, "📝 أرسل اسم القسم الجديد:")


    # ========================================
    # DELETE ITEM START (CALLBACK)
    # ========================================
    @bot.callback_query_handler(func=lambda call: call.data == "admin_delete_item")
    def delete_item_start(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        if not is_admin(call.from_user.id):
            bot.send_message(call.message.chat.id, "❌ غير مصرح لك")
            return

        items = execute("""
        SELECT id, title FROM menu_items
        ORDER BY id DESC
        LIMIT 20
        """, fetch=True)

        if not items:
            bot.send_message(call.message.chat.id, "❌ لا توجد أقسام لحذفها حالياً.")
            return

        text = "🗑 **قائمة الأقسام الحالية:**\n"
        for i in items:
            text += f"\n🔢 `{i['id']}` - {i['title']}"
        text += "\n\nالرجاء إرسال **رقم القسم** المراد حذفه نهائياً:"

        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
        admin_state[call.from_user.id] = {"action": "delete_item"}


    # ========================================
    # UNIFIED TEXT INPUT HANDLER (المعالج الموحد للنصوص)
    # ========================================
    @bot.message_handler(func=lambda m: m.from_user.id in admin_state)
    def handle_admin_text_inputs(message: Message):
        user_id = message.from_user.id
        state = admin_state.get(user_id)

        if not state:
            return

        action = state.get("action")

        # --- إجراء إضافة قسم ---
        if action == "add_item":
            title = message.text.strip()
            if not title:
                bot.reply_to(message, "❌ اسم القسم لا يمكن أن يكون فارغاً.")
                return

            execute("""
            INSERT INTO menu_items(title, type, parent_id, sort_order)
            VALUES(%s, 'menu', 0, 0)
            """, (title,))

            bot.send_message(message.chat.id, f"✅ تم إضافة القسم بنجاح:\n📂 {title}")
            admin_state.pop(user_id, None) # إنهاء الحالة

        # --- إجراء حذف قسم ---
        elif action == "delete_item":
            try:
                item_id = int(message.text.strip())
                delete_item_recursive(item_id)
                bot.send_message(message.chat.id, f"🗑 تم حذف العنصر ذو الرقم {item_id} وجميع متعلقاته بنجاح.")
            except ValueError:
                bot.send_message(message.chat.id, "❌ يرجى إرسال رقم صحيح (ID) وليس نصاً.")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ خطأ أثناء الحذف: {e}")
            
            admin_state.pop(user_id, None) # إنهاء الحالة


    # ========================================
    # BROADCAST BUTTON
    # ========================================
    @bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
    def broadcast_placeholder(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📢 سنبني ملف broadcast.py لاحقاً.")


    # ========================================
    # USERS BUTTON
    # ========================================
    @bot.callback_query_handler(func=lambda call: call.data == "admin_users")
    def users_placeholder(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        count = execute("SELECT COUNT(*) FROM users", fetchone=True)
        bot.send_message(
            call.message.chat.id,
            f"👥 عدد المستخدمين المسجلين في البوت: {count['count'] if count else 0}"
        )
        

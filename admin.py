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
    return result is not None


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
            "⚙️ لوحة التحكم:",
            reply_markup=admin_keyboard()
        )


    # ========================================
    # ADD ITEM START
    # ========================================

    @bot.callback_query_handler(func=lambda call: call.data == "admin_add_item")
    def add_item_start(call: CallbackQuery):

        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "غير مصرح")
            return

        admin_state[call.from_user.id] = {
            "action": "add_item"
        }

        bot.send_message(
            call.message.chat.id,
            "📝 أرسل اسم القسم الجديد:"
        )


    # ========================================
    # HANDLE TEXT INPUTS
    # ========================================

    @bot.message_handler(func=lambda m: m.from_user.id in admin_state)
    def handle_admin_input(message: Message):

        user_id = message.from_user.id
        state = admin_state.get(user_id)

        if not state:
            return

        # ====================================
        # ADD ITEM STEP 1
        # ====================================

        if state["action"] == "add_item":

            title = message.text

            execute("""
            INSERT INTO menu_items(title, type, parent_id, sort_order)
            VALUES(%s, 'menu', 0, 0)
            """, (title,))

            bot.send_message(
                message.chat.id,
                f"✅ تم إضافة القسم: {title}"
            )

            admin_state.pop(user_id, None)


    # ========================================
    # DELETE ITEM START
    # ========================================

    @bot.callback_query_handler(func=lambda call: call.data == "admin_delete_item")
    def delete_item_start(call: CallbackQuery):

        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "غير مصرح")
            return

        items = execute("""
        SELECT id, title FROM menu_items
        ORDER BY id DESC
        LIMIT 20
        """, fetch=True)

        text = "🗑 اختر القسم للحذف:\n"

        for i in items:
            text += f"\n{i['id']} - {i['title']}"

        bot.send_message(call.message.chat.id, text)

        admin_state[call.from_user.id] = {
            "action": "delete_item"
        }


    # ========================================
    # HANDLE DELETE INPUT
    # ========================================

    @bot.message_handler(func=lambda m: m.from_user.id in admin_state)
    def handle_delete_input(message: Message):

        user_id = message.from_user.id
        state = admin_state.get(user_id)

        if not state:
            return

        if state["action"] == "delete_item":

            try:
                item_id = int(message.text)

                delete_item_recursive(item_id)

                bot.send_message(
                    message.chat.id,
                    f"🗑 تم حذف العنصر {item_id}"
                )

            except Exception as e:
                bot.send_message(
                    message.chat.id,
                    f"❌ خطأ: {e}"
                )

            admin_state.pop(user_id, None)


    # ========================================
    # BROADCAST BUTTON (placeholder)
    # ========================================

    @bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
    def broadcast_placeholder(call: CallbackQuery):

        bot.send_message(
            call.message.chat.id,
            "📢 سنبني broadcast.py لاحقًا"
        )


    # ========================================
    # USERS BUTTON (placeholder)
    # ========================================

    @bot.callback_query_handler(func=lambda call: call.data == "admin_users")
    def users_placeholder(call: CallbackQuery):

        count = execute(
            "SELECT COUNT(*) FROM users",
            fetchone=True
        )

        bot.send_message(
            call.message.chat.id,
            f"👥 عدد المستخدمين: {count['count'] if count else 0}"
        )

# --------------------------------------
    # جميع رسائل الأدمن
    # --------------------------------------
    @bot.message_handler(func=lambda m: get_state(m.from_user.id) is not None)
    def admin_messages(message: Message):

        state = get_state(message.from_user.id)

        if not state:
            return

        current = state["state"]

        # ==============================
        # إضافة قسم جديد
        # ==============================
        if current == AdminState.ADD_ITEM:

            title = message.text.strip()

            if not title:
                bot.reply_to(message, "❌ اسم القسم لا يمكن أن يكون فارغاً.")
                return

            execute("""
                INSERT INTO menu_items(title, type, parent_id, sort_order)
                VALUES(%s, 'menu', 0, 0)
            """, (title,))

            clear_state(message.from_user.id)

            bot.send_message(
                message.chat.id,
                f"✅ تم إنشاء القسم:\n\n📂 {title}"
            )

            return

import asyncio
from psycopg_pool import AsyncConnectionPool
from config import DATABASE_URL
import telebot
from telebot import types
from database import get_db_connection  # يبقى للاستخدام المتزامن في الـ handlers

# إنشاء الـ Pool لإدارة الاتصالات بـ Neon (غير متزامن)
pool = AsyncConnectionPool(conninfo=DATABASE_URL, open=False)

async def init_db():
    """فتح Pool وإنشاء الجداول المطلوبة عند إقلاع البوت."""
    await pool.open()
    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            # 1. جدول الطلاب
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    phone_number VARCHAR(20),
                    is_verified BOOLEAN DEFAULT FALSE,
                    username VARCHAR(100)
                )
            ''')
            # 2. جدول الأزرار الديناميكية والرسائل المرتبطة بها
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS inline_buttons (
                    id SERIAL PRIMARY KEY,
                    text VARCHAR(100) NOT NULL,
                    type VARCHAR(20) NOT NULL, -- 'media' أو 'submenu'
                    parent_id INT REFERENCES inline_buttons(id) ON DELETE CASCADE,
                    sort_order INT DEFAULT 0,
                    message_text TEXT DEFAULT 'اختر من الأقسام التالية:'
                )
            ''')
            # 3. جدول محتويات أزرار الميديا والملفات
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS button_contents (
                    id SERIAL PRIMARY KEY,
                    button_id INT REFERENCES inline_buttons(id) ON DELETE CASCADE,
                    content_type VARCHAR(20),
                    file_id TEXT,
                    text_caption TEXT
                )
            ''')
            await conn.commit()

def register_user_handlers(bot: telebot.TeleBot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith('user_view_'))
    def user_navigation(call):
        btn_id = int(call.data.split('_')[2])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inline_buttons WHERE id = %s", (btn_id,))
        button = cursor.fetchone()

        if not button:
            conn.close()
            return

        if button['type'] == 'submenu':
            cursor.execute("SELECT * FROM inline_buttons WHERE parent_id = %s ORDER BY sort_order ASC", (btn_id,))
            child_buttons = cursor.fetchall()

            markup = types.InlineKeyboardMarkup(row_width=2)
            for cb in child_buttons:
                markup.add(types.InlineKeyboardButton(cb['text'], callback_data=f"user_view_{cb['id']}"))

            if button['parent_id']:
                markup.add(types.InlineKeyboardButton("🔙 عودة للخلف", callback_data=f"user_view_{button['parent_id']}"))
            else:
                markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="user_main_root"))

            bot.edit_message_text(button['message_text'], call.message.chat.id, call.message.message_id,
                                  reply_markup=markup, parse_mode="Markdown")

        elif button['type'] == 'media':
            cursor.execute("SELECT * FROM button_contents WHERE button_id = %s", (btn_id,))
            contents = cursor.fetchall()
            for item in contents:
                if item['content_type'] == 'document':
                    bot.send_document(call.message.chat.id, item['file_id'], caption=item['text_caption'])
        conn.close()

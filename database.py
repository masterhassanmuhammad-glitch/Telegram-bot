import asyncio
from psycopg_pool import AsyncConnectionPool
from config import DATABASE_URL

# إنشاء الـ Pool لإدارة الاتصالات بـ Neon
pool = AsyncConnectionPool(conninfo=DATABASE_URL, open=False)

async def init_db():
    # فتح الـ Pool عند إقلاع البوت
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
          

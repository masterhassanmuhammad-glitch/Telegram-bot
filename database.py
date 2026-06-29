import psycopg2
from psycopg2.extras import RealDictCursor
import os

# جلب رابط قاعدة البيانات من متغيرات البيئة
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """إنشاء اتصال مع PostgreSQL"""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL variable is missing!")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def execute(query, params=None, fetch=False, fetchone=False):
    """دالة موحدة لتنفيذ الاستعلامات متوافقة مع متطلبات مشروعك"""
    conn = get_db_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
        elif fetchone:
            result = cursor.fetchone()
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()
    return result

def init_db():
    """إنشاء كافة الجداول وهيكلتها بناءً على طلبات ملفات المشروع"""
    # 1. جدول المستخدمين
    execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            phone TEXT DEFAULT '---',
            is_blocked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. جدول الاستشارات الطبية (messages)
    execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            username TEXT,
            message_text TEXT,
            status INT DEFAULT 0
        )
    """)
    
    # 3. جدول الأقسام وشجرة القوائم (menu_items)
    execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT DEFAULT 'menu',
            parent_id INT DEFAULT 0,
            sort_order INT DEFAULT 0,
            description TEXT DEFAULT ''
        )
    """)
    
    # 4. جدول ملفات الأقسام (file_attachments)
    execute("""
        CREATE TABLE IF NOT EXISTS file_attachments (
            id SERIAL PRIMARY KEY,
            item_id INT,
            file_id TEXT NOT NULL,
            file_type TEXT NOT NULL,
            caption TEXT DEFAULT ''
        )
    """)
    
    # 5. جدول الإدارة (admins)
    execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id BIGINT PRIMARY KEY
        )
    """)

def init_settings(owner_id):
    """إضافة مالك البوت إلى جدول الأدمن تلقائياً عند الإقلاع"""
    execute("""
        INSERT INTO admins (user_id) 
        VALUES (%s) 
        ON CONFLICT (user_id) DO NOTHING
    """, (owner_id,))

def delete_item_recursive(item_id):
    """حذف القسم والملفات التابعة له برمجياً"""
    # حذف الملفات المرتبطة أولاً
    execute("DELETE FROM file_attachments WHERE item_id = %s", (item_id,))
    # حذف القسم نفسه
    execute("DELETE FROM menu_items WHERE id = %s", (item_id,))
    

import sqlite3
from config import DATABASE_URL

def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات وتفعيل خاصية السجلات كقواميس"""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """إنشاء الجداول الأساسية للبوت إذا لم تكن موجودة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. جدول المستخدمين (يدعم الصلاحيات: user, admin, doctor)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. جدول الاستشارات الطبية
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT,
            answer TEXT DEFAULT NULL,
            doctor_id INTEGER DEFAULT NULL,
            status TEXT DEFAULT 'pending', -- pending, answered
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # 3. جدول إدارة معرفات الملفات (File IDs) لتفادي إعادة الرفع
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_key TEXT PRIMARY KEY,
            file_id TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

# تنفيذ إنشاء الجداول عند استدعاء الملف لأول مرة
if __name__ == "__main__":
    # للتأكد من عمل الملف بشكل مستقل عند التجربة، اجعل DATABASE_URL في الـ .env تساوي "bot.db"
    initialize_db()
    print("Database initialized successfully.")

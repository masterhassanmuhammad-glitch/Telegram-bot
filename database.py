import json
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL

def get_db_connection():
    # الاتصال بقاعدة Neon مع تفعيل حماية SSL الإلزامية لـ Neon
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def execute_query(query, params=(), fetch=False, commit=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    data = None
    try:
        cursor.execute(query, params)
        if fetch:
            data = cursor.fetchall()
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
    return data

def execute_query_dict(query, params=()):
    # مخصصة لإرجاع البيانات كقاموس بايثون (Dict) لسهولة قراءتها
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    data = None
    try:
        cursor.execute(query, params)
        data = cursor.fetchall()
    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()
    return data

def init_db():
    # إنشاء جداول قاعدة البيانات عند التشغيل الأول للبوت
    # database.py (أضف هذا التعريف داخل دالة init_db)

    # 6. جدول المشرفين الفرعيين وصلاحياتهم
    execute_query('''
        CREATE TABLE IF NOT EXISTS admins (
            admin_id BIGINT PRIMARY KEY,
            can_settings BOOLEAN DEFAULT FALSE,
            can_broadcast BOOLEAN DEFAULT FALSE,
            can_feedback BOOLEAN DEFAULT FALSE,
            can_count BOOLEAN DEFAULT FALSE
        );
    ''', commit=True)
    
    # 1. جدول المستخدمين (لإحصاء وحفظ المشتركين للبث الجماعي)
    execute_query('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255)
        );
    ''', commit=True)
    
    # 2. جدول الأزرار الشجرية (ديناميكية بالكامل)
    execute_query('''
        CREATE TABLE IF NOT EXISTS buttons (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            parent_id INTEGER REFERENCES buttons(id) ON DELETE CASCADE,
            message_text TEXT
        );
    ''', commit=True)
    
    # 3. جدول ملفات الأزرار (لتخزين ملفات الميديا المتعددة المرتبطة بالزر)
    execute_query('''
        CREATE TABLE IF NOT EXISTS button_files (
            id SERIAL PRIMARY KEY,
            button_id INTEGER REFERENCES buttons(id) ON DELETE CASCADE,
            file_id VARCHAR(500) NOT NULL,
            file_type VARCHAR(50) NOT NULL
        );
    ''', commit=True)
    
    # 4. جدول الرسائل الواردة من المستخدمين للإدارة
    execute_query('''
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            username VARCHAR(255),
            message_text TEXT,
            status VARCHAR(50) DEFAULT 'pending'
        );
    ''', commit=True)
    
    # 5. جدول إدارة الحالات (FSM) لحماية البيانات من الاختفاء عند رسيت السيرفر
    execute_query('''
        CREATE TABLE IF NOT EXISTS user_states (
            user_id BIGINT PRIMARY KEY,
            state VARCHAR(100) NOT NULL,
            data TEXT DEFAULT '{}'
        );
    ''', commit=True)

# --- دالات آلة الحالة الـ FSM ---

def set_user_state(user_id, state, data_dict=None):
    data_str = json.dumps(data_dict or {})
    query = '''
        INSERT INTO user_states (user_id, state, data)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET state = EXCLUDED.state, data = EXCLUDED.data;
    '''
    execute_query(query, (user_id, state, data_str), commit=True)

def get_user_state(user_id):
    query = 'SELECT state, data FROM user_states WHERE user_id = %s;'
    res = execute_query(query, (user_id,), fetch=True)
    if res:
        state, data_str = res[0]
        try:
            data = json.loads(data_str)
        except:
            data = {}
        return state, data
    return None, {}

def clear_user_state(user_id):
    query = 'DELETE FROM user_states WHERE user_id = %s;'
    execute_query(query, (user_id,), commit=True)
    

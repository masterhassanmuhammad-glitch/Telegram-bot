import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import sqlite3
import html
import os        # لتحديد منفذ السيرفر تلقائياً
import threading # لتشغيل السيرفر في الخلفية
from flask import Flask # لإبقاء البوت حياً على Render

# ========================================================
# ⚙️ إعداد السيرفر الوهمي (Flask) لمنع توقف الخدمة على Render
# ========================================================
app = Flask('')

@app.route('/')
def home():
    return "🚀 البوت الطبي السوداني يعمل بنجاح وبشكل مستمر 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web_server)
    t.start()

# =========================
# إعدادات البوت الأساسية
# =========================
API_TOKEN = '8877531393:AAEQF004W0O_sQn7Ql5PwkXLi-99WpXybNU'
OWNER_ID = 8203001172
DB_NAME = 'medical_bot_v2.db'

bot = telebot.TeleBot(API_TOKEN)

# قاموس لحفظ جلسات الإدارة المؤقتة
admin_states = {}

# دالة مساعدة لإنشاء أزرار كيبورد الإلغاء السريع أسفل الشاشة
def get_cancel_keyboard(text="❌ إلغاء العملية"):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton(text))
    return markup

# =========================
# دالة فحص وإلغاء العمليات
# =========================
def check_cancel(message):
    if message.text in ['إلغاء', 'الغاء', '/cancel', '❌ إلغاء العملية', '❌ إلغاء التعديل', '❌ إلغاء الإرسال']:
        chat_id = message.chat.id
        state = admin_states.get(chat_id, {})
        
        if 'item_id' in state and state.get('is_new'):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM menu_items WHERE id = ?", (state['item_id'],))
            cursor.execute("DELETE FROM file_attachments WHERE item_id = ?", (state['item_id'],))
            conn.commit()
            conn.close()
            
        parent_id = state.get('parent_id', 0)
        if 'edit_id' in state:
            parent_id = state['edit_id']
            
        admin_states.pop(chat_id, None)
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        bot.send_message(chat_id, "❌ تم إلغاء العملية الحالية بنجاح والعودة.", reply_markup=ReplyKeyboardRemove())
        bot.send_message(chat_id, get_main_menu_text(), reply_markup=build_contextual_keyboard(parent_id, chat_id))
        return True
    return False

# =========================
# إدارة قاعدة البيانات
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            type TEXT,
            parent_id INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            description TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            file_id TEXT,
            file_type TEXT,
            caption TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            phone TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message_text TEXT,
            status INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    cursor.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('main_menu_text', 'اختر القسم المناسب من الأسفل:')")
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (OWNER_ID,))
    
    try: cursor.execute("ALTER TABLE menu_items ADD COLUMN sort_order INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE file_attachments ADD COLUMN caption TEXT")
    except: pass
    
    conn.commit()
    conn.close()

def is_admin(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def has_phone(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res and res[0]

def get_main_menu_text():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_settings WHERE key='main_menu_text'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "اختر القسم المناسب من الأسفل:"

def delete_item_recursive(item_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM menu_items WHERE parent_id = ?", (item_id,))
    children = cursor.fetchall()
    for child in children:
        delete_item_recursive(child[0])
    cursor.execute("DELETE FROM file_attachments WHERE item_id = ?", (item_id,))
    cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# =========================
# نظام التصفح والإدارة السياقية
# =========================
def build_contextual_keyboard(parent_id, user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, type FROM menu_items WHERE parent_id = ? ORDER BY sort_order ASC, id ASC", (parent_id,))
    rows = cursor.fetchall()
    
    for db_id, title, item_type in rows:
        icon = "📁 " if item_type == 'category' else "📄 "
        markup.add(InlineKeyboardButton(f"{icon}{title}", callback_data=f"navigate_{db_id}"))
        
    if parent_id == 0:
        markup.add(InlineKeyboardButton("📩 مراسلة الإدارة", callback_data="user_msg_admin"))
        
    if is_admin(user_id):
        markup.add(InlineKeyboardButton("━━━━━━ إدارة هذا القسم ━━━━━━", callback_data="void_click"))
        if parent_id == 0:
            markup.row(
                InlineKeyboardButton("➕ إضافة زر هنا", callback_data=f"adm_add_here_{parent_id}"),
                InlineKeyboardButton("📝 تعديل نص الواجهة", callback_data="adm_edit_main_welcome")
            )
            markup.row(
                InlineKeyboardButton("📢 إذاعة جماعية للمشتركين", callback_data="adm_init_broadcast"),
                InlineKeyboardButton("🔀 ترتيب أزرار القائمة", callback_data=f"adm_open_sort_{parent_id}")
            )
            cursor.execute("SELECT COUNT(*) FROM messages WHERE status = 0")
            pending_count = cursor.fetchone()[0]
            if pending_count > 0:
                markup.add(InlineKeyboardButton(f"📩 رسائل معلقة في الانتظار ({pending_count})", callback_data="adm_review_msgs"))
        else:
            markup.row(
                InlineKeyboardButton("➕ إضافة زر فرعي هنا", callback_data=f"adm_add_here_{parent_id}"),
                InlineKeyboardButton("📝 تعديل نص واجهة القسم", callback_data=f"adm_edit_cat_text_{parent_id}")
            )
            markup.row(
                InlineKeyboardButton("✏️ تعديل محتويات/اسم الزر", callback_data=f"adm_edit_item_{parent_id}"),
                InlineKeyboardButton("🔀 ترتيب أزرار هذا القسم", callback_data=f"adm_open_sort_{parent_id}")
            )
            markup.row(
                InlineKeyboardButton("🔄 نقل هذا القسم", callback_data=f"adm_move_item_{parent_id}"),
                InlineKeyboardButton("🗑️ حذف هذا القسم كلياً", callback_data=f"adm_delete_item_{parent_id}")
            )
            
    if parent_id != 0:
        cursor.execute("SELECT parent_id FROM menu_items WHERE id = ?", (parent_id,))
        parent_row = cursor.fetchone()
        back_id = parent_row[0] if parent_row else 0
        markup.add(InlineKeyboardButton("🔙 عودة للخلف", callback_data=f"navigate_{back_id}"))
        
    conn.close()
    return markup

def build_sorting_keyboard(parent_id):
    markup = InlineKeyboardMarkup(row_width=1)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM menu_items WHERE parent_id = ? ORDER BY sort_order ASC, id ASC", (parent_id,))
    rows = cursor.fetchall()
    conn.close()
    
    for item_id, title in rows:
        markup.row(
            InlineKeyboardButton("🔼", callback_data=f"sort_up_{item_id}_{parent_id}"),
            InlineKeyboardButton(f"{title}", callback_data="void_click"),
            InlineKeyboardButton("🔽", callback_data=f"sort_down_{item_id}_{parent_id}")
        )
    markup.add(InlineKeyboardButton("✅ إنهاء الترتيب والعودة", callback_data=f"navigate_{parent_id}"))
    return markup

# =========================
# أوامر البدء والتحقق
# =========================
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    bot.clear_step_handler_by_chat_id(chat_id=user_id)
    admin_states.pop(user_id, None)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                   (user_id, message.from_user.username or f"user_{user_id}"))
    conn.commit()
    conn.close()
    
    if not is_admin(user_id) and not has_phone(user_id):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("📱 مشاركة رقم الهاتف", request_contact=True))
        bot.send_message(user_id, "📌 يجب مشاركة رقم الهاتف أولاً لاستخدام البوت المخصص للاستشارات الطبية:", reply_markup=markup)
        return
        
    bot.send_message(user_id, "📚 أهلاً بك في البوت الطبي وموسوعة الأقسام المعرفية:", reply_markup=ReplyKeyboardRemove())
    bot.send_message(user_id, get_main_menu_text(), reply_markup=build_contextual_keyboard(0, user_id))

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.chat.id
    if message.contact.user_id != user_id:
        bot.send_message(user_id, "❌ الرجاء إرسال رقمك الشخصي فقط من خلال الزر المخصص.")
        return
    phone = message.contact.phone_number
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone=? WHERE user_id=?", (phone, user_id))
    conn.commit()
    conn.close()
    bot.send_message(user_id, "✅ تم تسجيل رقمك بنجاح ومزامنة حسابك!", reply_markup=ReplyKeyboardRemove())
    bot.send_message(user_id, get_main_menu_text(), reply_markup=build_contextual_keyboard(0, user_id))

# =========================
# معالجة ضغطات الأزرار (Callbacks)
# =========================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)
    
    if data == "void_click":
        return
        
    if data.startswith("navigate_"):
        pid = int(data.split("_")[1])
        bot.send_message(chat_id, "⏳ جاري العودة والتحميل...", reply_markup=ReplyKeyboardRemove())
        if pid == 0:
            msg_text = get_main_menu_text()
            attachments = []
            is_category = True
        else:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT type, description FROM menu_items WHERE id = ?", (pid,))
            item_row = cursor.fetchone()
            is_category = item_row[0] == 'category' if item_row else False
            msg_text = item_row[1] if (item_row and item_row[1]) else "لا يوجد وصف متوفر لهذا القسم."
            cursor.execute("SELECT file_id, file_type, caption FROM file_attachments WHERE item_id = ?", (pid,))
            attachments = cursor.fetchall()
            conn.close()

        # إرسال المرفقات إن وجدت
        if attachments:
            for file_id, file_type, caption in attachments:
                try:
                    cap = caption if caption else ""
                    if file_type == 'photo':
                        bot.send_photo(chat_id, file_id, caption=cap)
                    elif file_type == 'document':
                        bot.send_document(chat_id, file_id, caption=cap)
                    elif file_type == 'video':
                        bot.send_video(chat_id, file_id, caption=cap)
                except Exception as e:
                    print(f"Error sending file: {e}")

        # إرسال الرسالة النصية مع لوحة التحكم السياقية المتوافقة
        bot.send_message(chat_id, msg_text, reply_markup=build_contextual_keyboard(pid, call.from_user.id))

# ========================================================
# 🚀 نقطة الانطلاق والتشغيل الأساسية للمشروع
# ========================================================
if __name__ == '__main__':
    # 1. تهيئة جداول قاعدة البيانات
    init_db()
    
    # 2. تشغيل سيرفر ويب Flask في مسار مستقل لاستقبال اتصالات Render الفاحصة للـ Port
    keep_alive()
    
    print("⚡ تم تشغيل البوت الطبي بنجاح تام وهو جاهز الآن لخدمة المستخدمين 24/7...")
    
    # 3. تشغيل استقبال رسائل التليجرام بشكل لانهائي
    bot.infinity_polling()
            

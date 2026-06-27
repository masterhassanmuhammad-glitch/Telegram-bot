import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import psycopg2
import os
from flask import Flask, request

# ========================================================
# ⚙️ إعدادات البيئة والأمان (Environment Variables)
# ========================================================
API_TOKEN = os.environ.get('API_TOKEN', '8877531393:AAEQF004W0O_sQn7Ql5PwkXLi-99WpXybNU')
OWNER_ID = int(os.environ.get('OWNER_ID', 8203001172))
DATABASE_URL = os.environ.get('DATABASE_URL')

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# قاموس لحفظ جلسات الإدارة المؤقتة للخطوات المتتالية
admin_states = {}

# ========================================================
# 🌐 إعداد مسارات الـ Webhook لسيرفر Flask
# ========================================================

@app.route('/')
def home():
    return "🚀 البوت الطبي يعمل بكفاءة كاملة مع لوحة التحكم السحابية!", 200

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# =========================
# أزرار الإلغاء السريع أسفل الشاشة
# =========================
def get_cancel_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("❌ إلغاء العملية"))
    return markup

def check_cancel(message):
    if message.text in ['إلغاء', 'الغاء', '/cancel', '❌ إلغاء العملية']:
        chat_id = message.chat.id
        admin_states.pop(chat_id, None)
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        bot.send_message(chat_id, "❌ تم إلغاء العملية والعودة للقائمة الرئيسية.", reply_markup=ReplyKeyboardRemove())
        bot.send_message(chat_id, get_main_menu_text(), reply_markup=build_contextual_keyboard(0, chat_id))
        return True
    return False

# =========================
# تهيئة وإدارة قاعدة البيانات
# =========================
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id SERIAL PRIMARY KEY,
            title TEXT,
            type TEXT,
            parent_id INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            description TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_attachments (
            id SERIAL PRIMARY KEY,
            item_id INTEGER,
            file_id TEXT,
            file_type TEXT,
            caption TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id BIGINT PRIMARY KEY
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            phone TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
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
    
    cursor.execute("INSERT INTO bot_settings (key, value) VALUES ('main_menu_text', 'اختر القسم المناسب من الأسفل:') ON CONFLICT (key) DO NOTHING")
    cursor.execute("INSERT INTO admins (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (OWNER_ID,))
    
    conn.commit()
    conn.close()

def is_admin(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = %s", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def has_phone(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM users WHERE user_id=%s", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res and res[0]

def get_main_menu_text():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_settings WHERE key='main_menu_text'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "اختر القسم المناسب من الأسفل:"

def delete_item_recursive(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM menu_items WHERE parent_id = %s", (item_id,))
    children = cursor.fetchall()
    for child in children:
        delete_item_recursive(child[0])
    cursor.execute("DELETE FROM file_attachments WHERE item_id = %s", (item_id,))
    cursor.execute("DELETE FROM menu_items WHERE id = %s", (item_id,))
    conn.commit()
    conn.close()

# =========================
# بناء القوائم والأزرار الديناميكية
# =========================
def build_contextual_keyboard(parent_id, user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, type FROM menu_items WHERE parent_id = %s ORDER BY sort_order ASC, id ASC", (parent_id,))
    rows = cursor.fetchall()
    
    for db_id, title, item_type in rows:
        icon = "📁 " if item_type == 'category' else "📄 "
        markup.add(InlineKeyboardButton(f"{icon}{title}", callback_data=f"navigate_{db_id}"))
        
    if parent_id == 0:
        markup.add(InlineKeyboardButton("📩 مراسلة الإدارة والاستشارات", callback_data="user_msg_admin"))
        
    if is_admin(user_id):
        markup.add(InlineKeyboardButton("━━━━━━ أدوات الإدارة ━━━━━━", callback_data="void_click"))
        if parent_id == 0:
            markup.row(
                InlineKeyboardButton("➕ إضافة زر هنا", callback_data=f"adm_add_here_{parent_id}"),
                InlineKeyboardButton("📝 تعديل نص الواجهة", callback_data="adm_edit_main_welcome")
            )
            markup.row(
                InlineKeyboardButton("📢 إذاعة جماعية", callback_data="adm_init_broadcast"),
                InlineKeyboardButton("🔀 ترتيب الأزرار", callback_data=f"adm_open_sort_{parent_id}")
            )
        else:
            markup.row(
                InlineKeyboardButton("➕ إضافة زر فرعي هنا", callback_data=f"adm_add_here_{parent_id}"),
                InlineKeyboardButton("🗑️ حذف هذا القسم", callback_data=f"adm_delete_item_{parent_id}")
            )
            markup.row(
                InlineKeyboardButton("🔀 ترتيب الأزرار بالداخل", callback_data=f"adm_open_sort_{parent_id}")
            )
            
    if parent_id != 0:
        cursor.execute("SELECT parent_id FROM menu_items WHERE id = %s", (parent_id,))
        parent_row = cursor.fetchone()
        back_id = parent_row[0] if parent_row else 0
        markup.add(InlineKeyboardButton("🔙 عودة للخلف", callback_data=f"navigate_{back_id}"))
        
    conn.close()
    return markup

def build_sorting_keyboard(parent_id):
    markup = InlineKeyboardMarkup(row_width=1)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM menu_items WHERE parent_id = %s ORDER BY sort_order ASC, id ASC", (parent_id,))
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
# استقبال تفاعل الأوامر الأساسية
# =========================
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    bot.clear_step_handler_by_chat_id(chat_id=user_id)
    admin_states.pop(user_id, None)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING",
                   (user_id, message.from_user.username or f"user_{user_id}"))
    conn.commit()
    conn.close()
    
    if not is_admin(user_id) and not has_phone(user_id):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("📱 مشاركة رقم الهاتف", request_contact=True))
        bot.send_message(user_id, "📌 يجب مشاركة رقم الهاتف أولاً لتفعيل ميزات البوت الطبي الاستشاري الاستخدام البوت:", reply_markup=markup)
        return
        
    bot.send_message(user_id, "📚 أهلاً بك في البوت الطبي السوداني:", reply_markup=ReplyKeyboardRemove())
    bot.send_message(user_id, get_main_menu_text(), reply_markup=build_contextual_keyboard(0, user_id))

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.chat.id
    if message.contact.user_id != user_id:
        bot.send_message(user_id, "❌ الرجاء مشاركة رقمك الشخصي من خلال الزر فقط.")
        return
    phone = message.contact.phone_number
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone=%s WHERE user_id=%s", (phone, user_id))
    conn.commit()
    conn.close()
    bot.send_message(user_id, "✅ تم تسجيل حسابك والتحقق بنجاح!", reply_markup=ReplyKeyboardRemove())
    bot.send_message(user_id, get_main_menu_text(), reply_markup=build_contextual_keyboard(0, user_id))

# ========================================================
# 🎮 معالجة ضغطات الأزرار (Callbacks) وتنفيذ المهام كاملة
# ========================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)
    
    if data == "void_click":
        return
        
    # 1️⃣ التنقل والتصفح عبر الأقسام
    if data.startswith("navigate_"):
        pid = int(data.split("_")[1])
        if pid == 0:
            msg_text = get_main_menu_text()
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT description FROM menu_items WHERE id = %s", (pid,))
            item_row = cursor.fetchone()
            msg_text = item_row[0] if (item_row and item_row[0]) else "لا يوجد تفاصيل حالياً في هذا القسم."
            conn.close()

        bot.send_message(chat_id, msg_text, reply_markup=build_contextual_keyboard(pid, call.from_user.id))
        return

    # 2️⃣ إضافة زر جديد للوحة التحكم
    if data.startswith("adm_add_here_"):
        pid = int(data.split("_")[3])
        if not is_admin(chat_id): return
        admin_states[chat_id] = {'action': 'add_item', 'parent_id': pid}
        msg = bot.send_message(chat_id, "📝 أرسل الآن الاسم المقترح للزر الجديد:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, process_add_title)
        return

    # 3️⃣ تعديل النص الترحيبي الرئيسي للبوت
    if data == "adm_edit_main_welcome":
        if not is_admin(chat_id): return
        admin_states[chat_id] = {'action': 'edit_main_text'}
        msg = bot.send_message(chat_id, "📝 أرسل النص الجديد لواجهة الترحيب الأساسية:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, process_edit_main_text)
        return

    # 4️⃣ حذف قسم وزر برمجي
    if data.startswith("adm_delete_item_"):
        item_id = int(data.split("_")[3])
        if not is_admin(chat_id): return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT parent_id FROM menu_items WHERE id = %s", (item_id,))
        row = cursor.fetchone()
        parent_id = row[0] if row else 0
        conn.close()
        
        delete_item_recursive(item_id)
        bot.send_message(chat_id, "🗑️ تم حذف الزر وكافة تفريعاته الداخلية بنجاح!")
        bot.send_message(chat_id, get_main_menu_text() if parent_id == 0 else "تم التحديث:", reply_markup=build_contextual_keyboard(parent_id, chat_id))
        return

    # 5️⃣ لوحة ترتيب الأزرار وأوامر الأسهم
    if data.startswith("adm_open_sort_"):
        pid = int(data.split("_")[3])
        if not is_admin(chat_id): return
        bot.send_message(chat_id, "🔀 لوحة ترتيب الأزرار (اضغط الأسهم للتحريك):", reply_markup=build_sorting_keyboard(pid))
        return
        
    if data.startswith("sort_up_") or data.startswith("sort_down_"):
        parts = data.split("_")
        direction = parts[1]
        item_id = int(parts[2])
        pid = int(parts[3])
        if not is_admin(chat_id): return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM menu_items WHERE parent_id = %s ORDER BY sort_order ASC, id ASC", (pid,))
        items = [r[0] for r in cursor.fetchall()]
        
        if item_id in items:
            idx = items.index(item_id)
            if direction == "up" and idx > 0:
                items[idx], items[idx-1] = items[idx-1], items[idx]
            elif direction == "down" and idx < len(items) - 1:
                items[idx], items[idx+1] = items[idx+1], items[idx]
                
            for sort_order, id_ in enumerate(items):
                cursor.execute("UPDATE menu_items SET sort_order = %s WHERE id = %s", (sort_order, id_))
            conn.commit()
        conn.close()
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=build_sorting_keyboard(pid))
        return

    # 6️⃣ إذاعة رسالة لجميع المشتركين
    if data == "adm_init_broadcast":
        if not is_admin(chat_id): return
        admin_states[chat_id] = {'action': 'broadcast'}
        msg = bot.send_message(chat_id, "📢 أرسل الرسالة النصية التي تود إذاعتها للجميع:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, process_broadcast)
        return

    # 7️⃣ استقبال استفسارات ومراسلات المستخدمين للإدارة
    if data == "user_msg_admin":
        admin_states[chat_id] = {'action': 'user_msg'}
        msg = bot.send_message(chat_id, "📩 أرسل الآن استشارتك الطبية أو رسالتك وسيتم عرضها على الإدارة الطبية فوراً:", reply_markup=get_cancel_keyboard())
        bot.register_next_step_handler(msg, process_user_msg)
        return

# =========================
# معالجة الخطوات المتتالية (Step Handlers)
# =========================
def process_add_title(message):
    if check_cancel(message): return
    chat_id = message.chat.id
    title = message.text
    if not title:
        msg = bot.send_message(chat_id, "⚠️ يرجى كتابة اسم صحيح للزر:")
        bot.register_next_step_handler(msg, process_add_title)
        return
    admin_states[chat_id]['title'] = title
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📁 قسم فرعي (يضم أزراراً بداخلة)"), KeyboardButton("📄 صفحة معلومات (نصوص تفصيلية)"))
    markup.add(KeyboardButton("❌ إلغاء العملية"))
    msg = bot.send_message(chat_id, f"حدد نوع الزر الجديد [{title}]:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_add_type)

def process_add_type(message):
    if check_cancel(message): return
    chat_id = message.chat.id
    text = message.text
    if "قسم فرعي" in text:
        item_type = 'category'
    elif "صفحة معلومات" in text:
        item_type = 'text'
    else:
        msg = bot.send_message(chat_id, "⚠️ يرجى الاختيار من الأزرار المتاحة بالأسفل:")
        bot.register_next_step_handler(msg, process_add_type)
        return
        
    admin_states[chat_id]['type'] = item_type
    msg = bot.send_message(chat_id, "📝 أرسل الآن الشرح أو النص التفصيلي الذي سيظهر للمستخدم عند نقر هذا الزر:", reply_markup=get_cancel_keyboard())
    bot.register_next_step_handler(msg, process_add_content)

def process_add_content(message):
    if check_cancel(message): return
    chat_id = message.chat.id
    description = message.text
    if not description:
        msg = bot.send_message(chat_id, "⚠️ يرجى إرسال نص الشرح كاملاً:")
        bot.register_next_step_handler(msg, process_add_content)
        return
        
    state = admin_states[chat_id]
    parent_id = state['parent_id']
    title = state['title']
    item_type = state['type']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO menu_items (title, type, parent_id, description) VALUES (%s, %s, %s, %s)",
        (title, item_type, parent_id, description)
    )
    conn.commit()
    conn.close()
    
    admin_states.pop(chat_id, None)
    bot.send_message(chat_id, "✅ تم إنشاء الزر بنجاح وحفظه سحابياً للعمل فوراً!", reply_markup=ReplyKeyboardRemove())
    bot.send_message(chat_id, get_main_menu_text() if parent_id == 0 else "تم تحديث القائمة الحالي:", reply_markup=build_contextual_keyboard(parent_id, chat_id))

def process_edit_main_text(message):
    if check_cancel(message): return
    chat_id = message.chat.id
    new_text = message.text
    if not new_text:
        msg = bot.send_message(chat_id, "⚠️ يرجى إرسال نص صالح للتعديل:")
        bot.register_next_step_handler(msg, process_edit_main_text)
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bot_settings (key, value) VALUES ('main_menu_text', %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (new_text,))
    conn.commit()
    conn.close()
    
    admin_states.pop(chat_id, None)
    bot.send_message(chat_id, "✅ تم تعديل وحفظ نص الواجهة الترحيبية بنجاح!", reply_markup=ReplyKeyboardRemove())
    bot.send_message(chat_id, new_text, reply_markup=build_contextual_keyboard(0, chat_id))

def process_broadcast(message):
    if check_cancel(message): return
    chat_id = message.chat.id
    b_text = message.text
    if not b_text:
        msg = bot.send_message(chat_id, "⚠️ يرجى إرسال رسالة نصية لبثها:")
        bot.register_next_step_handler(msg, process_broadcast)
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    bot.send_message(chat_id, f"⏳ جاري بث وإرسال الرسالة إلى {len(users)} مشترك...", reply_markup=ReplyKeyboardRemove())
    success = 0
    for u in users:
        try:
            bot.send_message(u[0], b_text)
            success += 1
        except Exception:
            pass
            
    admin_states.pop(chat_id, None)
    bot.send_message(chat_id, f"✅ اكتمل البث! تم توصيل الإذاعة بنجاح لـ {success} مستخدم.")
    bot.send_message(chat_id, get_main_menu_text(), reply_markup=build_contextual_keyboard(0, chat_id))

def process_user_msg(message):
    if check_cancel(message): return
    chat_id = message.chat.id
    u_text = message.text
    if not u_text:
        msg = bot.send_message(chat_id, "⚠️ يرجى كتابة استشارتك نصياً:")
        bot.register_next_step_handler(msg, process_user_msg)
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (user_id, username, message_text) VALUES (%s, %s, %s)",
                   (chat_id, message.from_user.username or f"user_{chat_id}", u_text))
    conn.commit()
    conn.close()
    
    admin_states.pop(chat_id, None)
    bot.send_message(chat_id, "✅ تم إرسال استشارتك للإدارة الطبية بنجاح، ستصلك الإجابة هنا فور المراجعة.", reply_markup=ReplyKeyboardRemove())
    bot.send_message(chat_id, get_main_menu_text(), reply_markup=build_contextual_keyboard(0, chat_id))

# ========================================================
# 🚀 تشغيل خادم الـ Webhook
# ========================================================
# ========================================================
# 🚀 تشغيل خادم الـ Webhook
# ========================================================
if __name__ == '__main__':
    if not DATABASE_URL:
        print("❌ خطأ: لم يتم ضبط متغير البيئة DATABASE_URL")
        exit(1)
        
    init_db()
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')
    
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{API_TOKEN}")
        print(f"✅ Webhook configured online at: {RENDER_URL}")
    else:
        bot.remove_webhook()
        print("⚠️ Running locally for development.")
        
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    

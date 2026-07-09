# handlers/user.py
import telebot
from telebot import types
from database import get_db_connection

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
            
            # هنا يتم عرض الرسالة المرتبطة بالزر والتي تم تعديلها بواسطة الآدمن
            bot.edit_message_text(button['message_text'], call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            
        elif button['type'] == 'media':
            cursor.execute("SELECT * FROM button_contents WHERE button_id = %s", (btn_id,))
            contents = cursor.fetchall()
            # إرسال مستندات وصور هذا الزر دون حد ...
            for item in contents:
                if item['content_type'] == 'document':
                    bot.send_document(call.message.chat.id, item['file_id'], caption=item['text_caption'])
        conn.close()
                                      

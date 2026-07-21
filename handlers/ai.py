import config
from groq import Groq
import os

# تهيئة عميل Groq باستخدام المفتاح من متغيرات البيئة حصرياً
client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

def register_ai_handlers():
    @config.bot.message_handler(commands=['ask'])
    def ask_medical_ai(message):
        chat_id = message.chat.id
        query = message.text.replace('/ask', '', 1).strip()
        
        if not query:
            config.bot.reply_to(
                message, 
                "❌ أرجو كتابة سؤالك بعد الأمر، مثال:\n<code>/ask ما هي أسباب ارتفاع ضغط الدم؟</code>\n<code>/ask What are the causes of hypertension?</code>", 
                parse_mode="HTML"
            )
            return
            
        processing_msg = config.bot.reply_to(
            message, 
            "🤖 <b>جاري تحليل السؤال... / Analyzing query...</b>", 
            parse_mode="HTML"
        )
        
        try:
            # إرسال الطلب مع تعليمات صارمة للغة ووسوم HTML
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an intelligent and professional academic assistant for medical students. "
                            "CRITICAL RULE 1 (Language): You MUST reply in the EXACT SAME language as the user's query. If the user's query is in English, reply entirely in English. If it is in Arabic, reply entirely in Arabic.\n"
                            "CRITICAL RULE 2 (Formatting): Do NOT use Markdown asterisks like ** or *. Instead, use strict HTML tags for formatting (e.g., <b>bold text</b>, <i>italic text</i>) because the output will be parsed as HTML. Keep formatting clean, structured, and professional without any messy artifacts."
                        )
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=0.3, # تقليل درجة الحرارة لمنع تداخل الحروف والأخطاء الإملائية
            )
            
            answer = completion.choices[0].message.content
            
            config.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=answer,
                parse_mode="HTML"
            )
            
        except Exception as e:
            print(f"[Groq AI Error] {e}")
            try:
                config.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_msg.message_id,
                    text="⚠️ عذراً، حدث خطأ أثناء الاتصال بخدمة الذكاء الاصطناعي.\n⚠️ Sorry, an error occurred."
                )
            except:
                pass
                

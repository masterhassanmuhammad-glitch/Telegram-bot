# handlers/ai.py
import config
from groq import Groq

# تهيئة عميل Groq باستخدام المفتاح
client = Groq(api_key=getattr(config, 'GROQ_API_KEY', None))

def register_ai_handlers():
    @config.bot.message_handler(commands=['ask'])
    def ask_medical_ai(message):
        chat_id = message.chat.id
        query = message.text.replace('/ask', '').strip()
        
        if not query:
            config.bot.reply_to(
                message, 
                "❌ أرجو كتابة سؤالك الطبي أو العلمي بعد الأمر، مثال:\n`/ask ما هي أسباب ارتفاع ضغط الدم؟`", 
                parse_mode="Markdown"
            )
            return
            
        processing_msg = config.bot.reply_to(
            message, 
            "🩺 **جاري تحليل السؤال، يرجى الإنتظار**", 
            parse_mode="Markdown"
        )
        
        try:
            # إرسال الطلب باستخدام نموذج Llama 3.3 القوي
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "أنت مساعد أكاديمي ذكي لطلاب كلية الطب. قدم إجابة علمية دقيقة، منظمة، وواضحة تماماً باللغة العربية."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=0.7,
            )
            
            answer = completion.choices[0].message.content
            
            config.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=f"🤖 **إجابة المساعد الطبي:**\n\n{answer}",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            print(f"[Groq AI Error] {e}")
            config.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text="⚠️ عذراً، حدث خطأ أثناء الاتصال بخدمة الذكاء الاصطناعي. حاول مرة أخرى لاحقاً."
            )
            

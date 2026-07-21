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
            "🤖 <b>جاري تحليل السؤال وصياغة الإجابة... / Analyzing query...</b>", 
            parse_mode="HTML"
        )
        
        try:
            # إرسال الطلب مع تعليمات مطابقة اللغة والتنسيق المجمل
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "أنت مساعد أكاديمي ذكي ومرن لطلاب كلية الطب. "
                            "قاعدة اللغة الصارمة: أجب حصرياً بنفس لغة سؤال المستخدم (إذا كان السؤال باللغة العربية أجب باللغة العربية الفصحى، وإذا كان بالإنجليزية أجب بالإنجليزية). "
                            "تعليمات التنسيق: قدم إجابات علمية دقيقة، منسقة بشكل احترافي وجميل جداً، باستخدام العناوين البارزة ورموز التعداد الأنيقة (▪️ أو 🔹) لتسهيل القراءة عبر تيليجرام."
                        )
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
                text=f"{answer}",
                parse_mode="HTML"
            )
            
        except Exception as e:
            print(f"[Groq AI Error] {e}")
            try:
                config.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_msg.message_id,
                    text="⚠️ عذراً، حدث خطأ أثناء الاتصال بخدمة الذكاء الاصطناعي. حاول مرة أخرى لاحقاً.\n⚠️ Sorry, an error occurred. Please try again later."
                )
            except:
                pass
                

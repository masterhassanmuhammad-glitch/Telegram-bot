import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from config import GEMINI_API_KEY

# تهيئة نموذج الذكاء الاصطناعي
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def register_ai_handlers(bot):

    @bot.message_handler(commands=['ask'])
    def ask_medical_ai(message):
        chat_id = message.chat.id
        query = message.text.replace('/ask', '').strip()
        
        if not query:
            bot.reply_to(
                message, 
                "❌ أرجو كتابة سؤالك بعد الأمر، مثال:\n`/ask ما هي أسباب ارتفاع ضغط الدم؟`", 
                parse_mode="Markdown"
            )
            return
            
        processing_msg = bot.reply_to(
            message, 
            "🩺 **جاري تحليل السؤال وإعداد الإجابة العلمية...**", 
            parse_mode="Markdown"
        )
        
        try:
            prompt = (
                "أنت مساعد أكاديمي ذكي لطلاب كلية الطب. "
                "قدم إجابة علمية دقيقة، منظمة، وواضحة باللغة العربية بناءً على السؤال التالي:\n\n"
                f"{query}"
            )
            
            response = ai_model.generate_content(prompt)
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=f"🤖 **إجابة المساعد الذكي:**\n\n{response.text}",
                parse_mode="Markdown"
            )
            
        except ResourceExhausted:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text="⏳ عذراً، الضغط على خدمة الذكاء الاصطناعي مرتفع جداً الآن. يرجى المحاولة بعد قليل."
            )
        except Exception as e:
            print(f"[AI Error] {e}")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text="⚠️ عذراً، حدث خطأ أثناء الاتصال بخدمة الذكاء الاصطناعي. حاول مرة أخرى لاحقاً."
            )
            

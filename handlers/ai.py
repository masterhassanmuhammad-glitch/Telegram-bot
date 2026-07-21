import config
from groq import Groq
import os
import re

# تهيئة عميل Groq باستخدام المفتاح من متغيرات البيئة حصرياً
client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

def clean_markdown_to_telegram_html(text):
    """دالة لضمان تحويل أي ترميز Markdown قد يكتبه الذكاء الاصطناعي إلى وسوم ورموز تيليجرام المتوافقة"""
    # 1. تحويل **النص العريض** إلى وسوم HTML الصحيحة <b>النص العريض</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # 2. استبدال علامات التعداد النجمية أو الشرطات بـ ▪️ بشكل إجباري
    text = re.sub(r'^\s*[\*\-]\s+', '▪️ ', text, flags=re.MULTILINE)
    
    return text

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
            "🤖 <b>جاري التفكير، يرجى الإنتظار... / Generating detailed response...</b>", 
            parse_mode="HTML"
        )
        
        try:
            # إرسال الطلب مع تنبيه صارم للنموذج بعدم استخدام النجوم
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an exhaustive, highly detailed, and professional academic assistant for medical students. "
                            "CRITICAL INSTRUCTION: Provide deep, comprehensive, and thoroughly detailed explanations with maximum depth. "
                            "CRITICAL RULE 1 (Language): You MUST reply in the EXACT SAME language as the user's query.\n"
                            "CRITICAL RULE 2 (Strict HTML Formatting - NO MARKDOWN ALLOWED): "
                            "- NEVER use Markdown asterisks like ** for bold text. Use HTML tags <b>text</b> instead. "
                            "- NEVER use * or - for bullet points. You MUST use '▪️' or '▫️' for all lists. "
                            "- Use HTML blockquote tags <blockquote>Your text here</blockquote> for important notes or core summaries."
                        )
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=0.3,
                max_tokens=8192,  # أقصى مساحة ممكنة للإجابة المفصلة
            )
            
            answer = completion.choices[0].message.content
            
            # تطبيق الفلتر البرمجي لتنظيف واستبدال أي علامات بقيت بالخطأ
            cleaned_answer = clean_markdown_to_telegram_html(answer)
            
            # التأكد من عدم تجاوز حدود تيليجرام للرسالة الواحدة (4000 حرف)
            final_text = cleaned_answer[:4000] if len(cleaned_answer) <= 4000 else cleaned_answer[:3997] + "..."
            
            config.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=final_text,
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
                

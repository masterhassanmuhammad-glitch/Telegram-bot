import config
from groq import Groq
import os
import re

# تهيئة عميل Groq باستخدام المفتاح من متغيرات البيئة حصرياً
client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

def clean_markdown_to_telegram_html(text):
    """دالة لضمان تنظيف وإغلاق أي وسوم HTML تفادياً لأخطاء تيليجرام 400"""
    # 1. تحويل **النص العريض** إلى وسوم HTML الصحيحة <b>النص العريض</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # 2. تحويل الاقتباسات الفردية (> نص) إلى صندوق اقتباس
    text = re.sub(r'^\s*>\s+(.*)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
    
    # 3. التأكد البرمجي من إغلاق أي وسم blockquote مفتوحة لم يغلقها النموذج
    open_quotes = text.count('<blockquote>')
    close_quotes = text.count('</blockquote>')
    if open_quotes > close_quotes:
        text += '</blockquote>' * (open_quotes - close_quotes)
        
    # 4. التأكد البرمجي من إغلاق أي وسم <b> مفتوح
    open_b = text.count('<b>')
    close_b = text.count('</b>')
    if open_b > close_b:
        text += '</b>' * (open_b - close_b)
    
    # 5. استبدال علامات التعداد النجمية أو الشرطات بـ ▪️ بشكل إجباري
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
                "❌ أرجو كتابة سؤالك بعد الأمر، مثال:\n<code>/ask ما هو ضغط الدم الطبيعي؟</code>\n<code>/ask What is normal blood pressure?</code>", 
                parse_mode="HTML"
            )
            return
            
        processing_msg = config.bot.reply_to(
            message, 
            "🤖 <b>جاري صياغة الإجابة المباشرة... / Generating response...</b>", 
            parse_mode="HTML"
        )
        
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a concise, direct, and precise academic assistant for medical students. "
                            "CRITICAL INSTRUCTION: Provide short, focused, and precise answers that match the exact scope and length of the user's question without unnecessary verbosity or fluff.\n"
                            "CRITICAL RULE 1 (Language): You MUST reply in the EXACT SAME language as the user's query.\n"
                            "CRITICAL RULE 2 (Strict HTML Formatting - NO MARKDOWN ALLOWED): "
                            "- NEVER use Markdown asterisks like ** for bold text. Use HTML tags <b>text</b> instead. "
                            "- NEVER use * or - for bullet points. You MUST use '▪️' or '▫️' for all lists. "
                            "- Use HTML blockquote tags <blockquote>Your text here</blockquote> for key takeaways if needed."
                        )
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=0.3,
                max_tokens=1000,  # تم تقليلها لتلائم الإجابات القصيرة وتحافظ على الرصيد اليومي
            )
            
            answer = completion.choices[0].message.content
            
            # تطبيق الفلتر الذكي لإغلاق وتصحيح أي وسوم ناقصة تلقائياً
            cleaned_answer = clean_markdown_to_telegram_html(answer)
            
            final_text = cleaned_answer[:4000] if len(cleaned_answer) <= 4000 else cleaned_answer[:3997] + "..."
            
            config.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=final_text,
                parse_mode="HTML"
            )
            
        except Exception as e:
            error_str = str(e)
            print(f"[Groq AI Error] {error_str}")
            
            if "429" in error_str or "rate_limit_exceeded" in error_str:
                error_text = "⚠️ <b>عذراً، لقد وصلت إلى الحد الأقصى المسموح به من الطلبات اليومية (Rate Limit). يرجى المحاولة لاحقاً.</b>"
            else:
                error_text = "⚠️ عذراً، حدث خطأ أثناء الاتصال بخدمة الذكاء الاصطناعي."
                
            try:
                config.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_msg.message_id,
                    text=error_text,
                    parse_mode="HTML"
                )
            except:
                pass
            

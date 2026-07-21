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
                "❌ أرجو كتابة سؤالك بعد الأمر، مثال:\n<code>/ask ما هي أسباب ارتفاع ضغط الدم وتفاصيل الفيزيولوجيا المرضية؟</code>\n<code>/ask Explain the detailed pathophysiology of hypertension.</code>", 
                parse_mode="HTML"
            )
            return
            
        processing_msg = config.bot.reply_to(
            message, 
            "🤖 <b>جاري إعداد إجابة علمية مفصلة وشاملة... / Generating detailed comprehensive response...</b>", 
            parse_mode="HTML"
        )
        
        try:
            # إرسال الطلب مع تعليمات دقيقة لتفعيل الصناديق، الإيموجي، والمساحة الكاملة
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an exhaustive, highly detailed, and professional academic assistant for medical students. "
                            "CRITICAL INSTRUCTION: Provide deep, comprehensive, and thoroughly detailed explanations with maximum depth. Do not summarize or omit important medical and scientific mechanisms, classifications, or clinical details.\n"
                            "CRITICAL RULE 1 (Language): You MUST reply in the EXACT SAME language as the user's query. If the user's query is in English, reply entirely in English. If it is in Arabic, reply entirely in Arabic.\n"
                            "CRITICAL RULE 2 (Formatting & Styling): "
                            "- Use rich and professional emojis (e.g., 🔹, 📌, 💡, ✨, 🩺, 🔬) for headings and lists. "
                            "- Use HTML tags for formatting since parse_mode='HTML' is active (e.g., <b>bold text</b>, <i>italic text</i>). "
                            "- Crucially, use Telegram's HTML blockquote tag <blockquote>Your text here</blockquote> for important notes, core summaries, or clinical pearls (this creates the distinct quote box with a vertical line seen in Telegram). "
                            "- Organize the comprehensive response cleanly using professional headings and structured bullet points."
                        )
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=0.4,
                max_tokens=8192,  # أقصى مساحة ممكنة للإجابة المفصلة
            )
            
            answer = completion.choices[0].message.content
            
            # التأكد من عدم تجاوز حدود تيليجرام للرسالة الواحدة (4000 حرف)
            final_text = answer[:4000] if len(answer) <= 4000 else answer[:3997] + "..."
            
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
                

import time
from telebot import types
import config
from groq import Groq
import os
from gemini import ask_gemini

# تهيئة عميل Groq الاحتياطي
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

def register_ai_handlers():
    @config.bot.message_handler(commands=['ask'])
    def ask_command(message):
        chat_id = message.chat.id
        query = message.text.replace('/ask', '', 1).strip()
        
        if not query:
            config.bot.reply_to(
                message, 
                "❌ أرجو كتابة سؤالك بعد الأمر، مثال:\n`/ask ما هي أسباب ارتفاع ضغط الدم؟`", 
                parse_mode="Markdown"
            )
            return
            
        processing_msg = config.bot.reply_to(
            message, 
            "🤖 <b>جاري تحليل السؤال، يرجى الإنتظار...</b>", 
            parse_mode="HTML"
        )
        
        # 1. المحاولة الأساسية: استخدام Gemini أولاً
        try:
            answer = ask_gemini(query)
            
            cleaned_text = (
                answer.replace("<p>", "")
                      .replace("</p>", "\n")
                      .replace("<br>", "\n")
                      .replace("<br/>", "\n")
            )[:4000]
            
            config.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=cleaned_text if cleaned_text else "⚠️ لم يتم استلام أي نص.",
                parse_mode='HTML'
            )
            return  # تمت الإجابة بنجاح عبر Gemini
            
        except Exception as gemini_error:
            error_str = str(gemini_error)
            print(f"[Gemini Error] {error_str} -> جاري التحويل إلى النظام الاحتياطي (Groq)...")
            
            # 2. التحويل التلقائي: إذا انتهت حصة Gemini (خطأ 429 أو RESOURCE_EXHAUSTED) أو حدثت مشكلة، ننتقل لـ Groq
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str or "UNAVAILABLE" in error_str:
                try:
                    completion = groq_client.chat.completions.create(
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
                        text=f"🤖 <b>إجابة المساعد (عبر النظام الاحتياطي):</b>\n\n{answer}",
                        parse_mode="HTML"
                    )
                    return  # تمت الإجابة بنجاح عبر Groq الاحتياطي
                    
                except Exception as groq_error:
                    print(f"[Groq AI Error] {groq_error}")
            
            # إذا فشلت كل المحاولات
            try:
                config.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_msg.message_id,
                    text="⚠️ عذراً، خوادم الذكاء الاصطناعي مشغولة حالياً أو تم استنفاد الحصص بالكامل. حاول مرة أخرى لاحقاً."
                )
            except:
                pass
                

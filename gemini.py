import os
import time
from google import genai
import config

# تهيئة عميل Google GenAI
client = genai.Client(api_key=config.GEMINI_API_KEY)

def ask_gemini(question):
    max_retries = 3
    delay = 2
    
    # تعليمات صارمة لمنع النجوم وتفعيل الرموز الأنيقة
    system_instruction = (
        "أنت مساعد ذكي ومحترف، متخصص في تقديم الشرح العميق، الشامل، والمفصل للغاية. "
        "استفد بالكامل من المساحة المتاحة لتقديم إجابات متكاملة تغطي كافة الجوانب بدقة واحترافية. "
        "تعليمات التنسيق الصارمة لتليجرام (HTML): "
        "1. ممنوع منعاً باتاً استخدام رمز النجمة (*) أو أي رموز تنسيق ماركدون (مثل ** أو #) نهائياً، حتى لا تظهر كرموز نصية مزعجة. "
        "2. استخدم حصرياً رموز تعداد أنيقة ومميزة في بداية النقاط مثل (▪️ أو 🔹) بدلاً من النجوم والنقاط العادية. "
        "3. استخدم <b>العناوين البارزة</b> مدمجة مع رموز تعبيرية معبرة (مثل 📌، 🩺، 💡) لتقسيم الموضوع بوضوح. "
        "4. استخدم وسوم الاقتباس <blockquote>للملاحظات الجوهرية أو التنبيهات الأساسية</blockquote> لتظهر بصندوق جانبي أنيق. "
        "5. استخدم <code>للمصطلحات العلمية أو الرموز</code> لتمييزها. "
        "6. ممنوع استخدام وسوم الفقرات مثل <p> أو </p> أو وسوم الأسطر مثل <br>."
    )
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=question,
                config={
                    'system_instruction': system_instruction,
                    'max_output_tokens': 8192,
                    'temperature': 0.7,
                }
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if ("503" in error_str or "UNAVAILABLE" in error_str) and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise e
            

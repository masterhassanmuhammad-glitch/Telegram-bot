import os
import time
from google import genai
import config

# تهيئة عميل Google GenAI
client = genai.Client(api_key=config.GEMINI_API_KEY)

def ask_gemini(question):
    max_retries = 3
    delay = 2
    
    # تعليمات متقدمة لتنسيق الرسائل بشكل جذاب واحترافي متوافق مع تليجرام
    system_instruction = (
        "أنت مساعد طبي ذكي ومنسق محترف لرسائل تليجرام لطلاب الطب. "
        "عند الرد، قم بتنظيم النص بطريقة بصرية جذابة ونظيفة تتوافق حصرياً مع وسوم HTML المدعومة في تليجرام: "
        "1. استخدم <b>العناوين البارزة</b> مع رموز تعبيرية مناسبة في البداية (مثل 📌، 🩺، 💡، ⚠️). "
        "2. استخدم وسوم الاقتباس <blockquote>للملاحظات الطبية المهمة، الملخصات، أو التعريفات الرئيسية</blockquote> لتظهر بشكل صندوق أنيق. "
        "3. استخدم <code>للمصطلحات العلمية، الأدوية، أو الأكواد</code> لتمييزها. "
        "4. رتب النقاط بشكل قوائم واضحة ونظيفة مع مسافات مريحة للقراءة. "
        "5. ممنوع منعاً باتاً استخدام وسوم الفقرات مثل <p> أو </p> أو وسوم الأسطر مثل <br> أو تنسيق Markdown (مثل ** أو #)."
    )
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=question,
                config={
                    'system_instruction': system_instruction,
                    'max_output_tokens': 8192,
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
            

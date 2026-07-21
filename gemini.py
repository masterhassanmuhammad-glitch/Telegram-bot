import os
import time
from google import genai
import config

# تهيئة عميل Google GenAI
client = genai.Client(api_key=config.GEMINI_API_KEY)

def ask_gemini(question):
    max_retries = 3
    delay = 2
    
    # تعليمات النظام لضمان الشرح الشامل والمستفيض مع أقصى درجات التنسيق الجمالي
    system_instruction = (
        "أنت مساعد ذكي ومحترف، متخصص في تقديم الشرح العميق، الشامل، والمفصل للغاية دون أي إيجاز مخل. "
        "استفد بالكامل من المساحة المتاحة لتقديم إجابات متكاملة تغطي كافة الجوانب بدقة واحترافية. "
        "قم بتنسيق إجاباتك حصرياً وبأعلى معايير الجمال البصري باستخدام وسوم HTML المدعومة في تليجرام فقط: "
        "1. استخدم <b>العناوين البارزة</b> مدمجة مع رموز تعبيرية معبرة ومرتبة (مثل 📌، 🩺، 💡، ✨، 🔬) لتقسيم الموضوع بوضوح. "
        "2. استخدم وسوم الاقتباس <blockquote>للملاحظات الجوهرية، الملخصات المركزية، أو التنبيهات الأساسية</blockquote> لتظهر بصندوق جانبي أنيق. "
        "3. استخدم <code>للمصطلحات العلمية، الأسماء، أو الرموز</code> لتمييزها بوضوح تام. "
        "4. نظم الفقرات في قوائم ونقاط واضحة ومتباعدة بشكل مريح جداً للقراءة على الهواتف. "
        "5. ممنوع منعاً باتاً استخدام وسوم الفقرات مثل <p> أو </p> أو وسوم الأسطر مثل <br> أو <br/> أو أي تنسيق يتبع Markdown (مثل ** أو #)."
    )
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=question,
                config={
                    'system_instruction': system_instruction,
                    'max_output_tokens': 8192,  # أقصى حد مسموح به لعدد الرموز لضمان إجابات مطولة وعميقة
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
            

import os
import random
import time
from google import genai
import config

# قراءة المفاتيح من متغيرات البيئة أو استخدام المفاتيح مباشرة كاحتياطي
env_keys = os.getenv("GEMINI_API_KEYS", "")
if env_keys:
    API_KEYS = [k.strip() for k in env_keys.split(",") if k.strip()]
else:
    API_KEYS = [
        getattr(config, "GEMINI_API_KEY", ""),
        "AIzaSyCWdDVAJ0D-dksIBX9o5fu_hWV5HLYpBBU",
        "AIzaSyCDCIGDaZzGVf6OnI4D2pLJI_va8aPaNU0",
        "AIzaSyBjP4RqtdALOOLfhL-TGjuDllzLVwa9CKM",
        "AIzaSyB7iPW1bWioXW4JuMn6v2oQ3RcMY367SII"
    ]
    API_KEYS = [k for k in API_KEYS if k] # تصفية أي مفتاح فارغ

def get_random_client():
    if not API_KEYS:
        raise ValueError("❌ لم يتم العثور على أي مفتاح API صالح!")
    selected_key = random.choice(API_KEYS)
    return genai.Client(api_key=selected_key)

# تعليمات النظام الموحدة
SYSTEM_INSTRUCTION = (
    "أنت مساعد ذكي ومحترف. قدم إجابات مركزة، مختصرة، ومباشرة جداً دون إطالة أو حشو مبالغ فيه. "
    "تعليمات التنسيق الصارمة لتليجرام (HTML): "
    "1. ممنوع منعاً باتاً استخدام رمز النجمة (*) أو أي رموز تنسيق ماركدون (مثل ** أو #) نهائياً. "
    "2. استخدم حصرياً رموز تعداد أنيقة ومميزة في بداية النقاط مثل (▪️ أو 🔹). "
    "3. استخدم <b>العناوين البارزة</b> مدمجة مع رموز تعبيرية معبرة (مثل 📌، 🩺، 💡). "
    "4. استخدم وسوم الاقتباس <blockquote>للملاحظات الأساسية باختصار</blockquote>. "
    "5. استخدم <code>للمصطلحات العلمية أو الرموز</code>. "
    "6. ممنوع استخدام وسوم الفقرات مثل <p> أو </p> أو وسوم الأسطر مثل <br>."
)

def ask_gemini(question):
    max_retries = 3
    delay = 25
    for attempt in range(max_retries):
        try:
            client = get_random_client()
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=question,
                config={
                    'system_instruction': SYSTEM_INSTRUCTION,
                    'max_output_tokens': 2000,
                    'temperature': 0.7,
                }
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str) and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise e

def ask_gemini_stream(question):
    max_retries = 3
    delay = 25
    for attempt in range(max_retries):
        try:
            client = get_random_client()
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=question,
                config={
                    'system_instruction': SYSTEM_INSTRUCTION,
                    'max_output_tokens': 2000,
                    'temperature': 0.7,
                }
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            return
        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str) and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise e
            

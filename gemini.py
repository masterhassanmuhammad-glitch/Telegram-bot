import os
import time
import itertools
from google import genai

# 1. جلب المفاتيح الـ 5 من متغيرات البيئة بمرونة
api_keys = []

# البحث عن GEMINI_API_KEY_1 إلى GEMINI_API_KEY_5
for i in range(1, 6):
    key = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
    if key:
        api_keys.append(key)

# في حال عدم وجود مفاتيح مرقمة، نتحقق من المفتاح الرئيسي (سواء مفرد أو مفصول بفاصلة)
if not api_keys:
    raw_keys = os.getenv("GEMINI_API_KEY", "").strip()
    if raw_keys:
        api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

if not api_keys:
    raise ValueError("❌ خطأ أمني: لم يتم العثور على أي مفاتيح API في متغيرات البيئة.")

# 2. إنشاء عميل (Client) مستقل لكل مفتاح وتجهيز الحلقة الدائرية
clients = [genai.Client(api_key=key) for key in api_keys]
client_cycle = itertools.cycle(clients)

def get_next_client():
    return next(client_cycle)

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
    max_rounds = 3  # عدد محاولات المرور على جميع المفاتيح
    delay = 5       # وقت الانتظار المبدئي في حال استنفاد كل المفاتيح
    
    for round_num in range(max_rounds):
        # المحاولة باستخدام كافة المفاتيح المتاحة مفتاحاً تلو الآخر
        for _ in range(len(clients)):
            client = get_next_client()
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=question,
                    config={
                        'system_instruction': SYSTEM_INSTRUCTION,
                        'max_output_tokens': 500,
                        'temperature': 0.7,
                    }
                )
                return response.text
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # عند استنفاد حدود المفتاح الحالي، ننتقل مباشرة للمفتاح التالي دون انتظار
                    continue
                raise e

        # إذا كانت جميع المفاتيح مستنفدة (429)، ننتظر قليلاً ثم نعيد المحاولة
        if round_num < max_rounds - 1:
            time.sleep(delay)
            delay *= 2

    raise Exception("❌ جميع مفاتيح API مستنفدة حالياً (429 Resource Exhausted).")

def ask_gemini_stream(question):
    max_rounds = 3
    delay = 5
    
    for round_num in range(max_rounds):
        for _ in range(len(clients)):
            client = get_next_client()
            try:
                response = client.models.generate_content_stream(
                    model="gemini-3.5-flash-lite",
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
                return  # تم النجاح، الخروج من الدالة
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # الانتقال للمفتاح التالي
                    continue
                raise e

        if round_num < max_rounds - 1:
            time.sleep(delay)
            delay *= 2

    raise Exception("❌ جميع مفاتيح API مستنفدة حالياً (429 Resource Exhausted).")
    

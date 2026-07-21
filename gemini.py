from google import genai
import config

client = genai.Client(api_key=config.GEMINI_API_KEY)

def ask_gemini(question):
    max_retries = 3
    delay = 2
    
    # تعليمات النظام لضمان إخراج الردود بتنسيق HTML متوافق مع تليجرام
    system_instruction = (
        "أنت مساعد ذكي ومفيد لطلاب الطب. "
        "قم بتنسيق إجاباتك حصرياً باستخدام وسوم HTML المدعومة في تليجرام مثل "
        "<b>النص العريض</b>، <i>النص المائل</i>، <code>الكود القصير</code>، و <pre><code>كتلة الكود البرمجي</code>> "
        "مع استخدام الرموز التعبيرية (الإيموجي) بشكل منظم وجميل، ولا تستخدم تنسيق Markdown التقليدي."
    )
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=question,
                config={
                    'system_instruction': system_instruction
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
            

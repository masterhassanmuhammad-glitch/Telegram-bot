import os
import time
from google import genai
import config

# تهيئة عميل Google GenAI
client = genai.Client(api_key=config.GEMINI_API_KEY)

def ask_gemini_stream(question):
    # تعليمات جديدة تركز على الاختصار والإيجاز مع الحفاظ على التنسيق الأنيق
    system_instruction = (
        "أنت مساعد ذكي ومحترف. قدم إجابات مركزة، مختصرة، ومباشرة جداً دون إطالة أو حشو مبالغ فيه. "
        "تعليمات التنسيق الصارمة لتليجرام (HTML): "
        "1. ممنوع منعاً باتاً استخدام رمز النجمة (*) أو أي رموز تنسيق ماركدون (مثل ** أو #) نهائياً. "
        "2. استخدم حصرياً رموز تعداد أنيقة ومميزة في بداية النقاط مثل (▪️ أو 🔹). "
        "3. استخدم <b>العناوين البارزة</b> مدمجة مع رموز تعبيرية معبرة (مثل 📌، 🩺، 💡). "
        "4. استخدم وسوم الاقتباس <blockquote>للملاحظات الأساسية باختصار</blockquote>. "
        "5. استخدم <code>للمصطلحات العلمية أو الرموز</code>. "
        "6. ممنوع استخدام وسوم الفقرات مثل <p> أو </p> أو وسوم الأسطر مثل <br>."
    )
    
    # تقليل عدد الرموز المخرجة (max_output_tokens) لتكون الإجابات قصيرة ومختصرة تلقائياً
    response = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=question,
        config={
            'system_instruction': system_instruction,
            'max_output_tokens': 2000,  
            'temperature': 0.7,
        }
    )
    
    for chunk in response:
        if chunk.text:
            yield chunk.text
            

import os
from google import genai

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def ask_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    if hasattr(response, "text") and response.text:
        return response.text

    return "لم يتمكن Gemini من إنشاء رد."

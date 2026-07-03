import re
from datetime import datetime


# ============================================
# CLEAN TEXT
# ============================================

def clean_text(text: str) -> str:
    """
    إزالة المسافات الزائدة وتنسيق النص
    """
    if not text:
        return ""

    return text.strip()


# ============================================
# VALIDATE USER ID
# ============================================

def is_valid_user_id(user_id):
    try:
        return isinstance(int(user_id), int)
    except:
        return False


# ============================================
# EXTRACT COMMAND ARGS
# ============================================

def parse_command_args(text):
    """
    /reply 123 hello world
    => (123, "hello world")
    """
    parts = text.split(" ", 2)

    if len(parts) < 3:
        return None, None

    try:
        user_id = int(parts[1])
    except:
        return None, None

    return user_id, parts[2]


# ============================================
# FORMAT DATE
# ============================================

def format_date(dt=None):
    """
    تحويل التاريخ لصيغة جميلة
    """
    if not dt:
        dt = datetime.now()

    return dt.strftime("%Y-%m-%d %H:%M")


# ============================================
# SHORT TEXT LIMIT
# ============================================

def shorten_text(text, limit=50):
    """
    تقصير النصوص الطويلة
    """
    if not text:
        return ""

    if len(text) <= limit:
        return text

    return text[:limit] + "..."


# ============================================
# CHECK PHONE NUMBER (optional use)
# ============================================

def is_phone_number(text):
    """
    تحقق بسيط من رقم الهاتف
    """
    pattern = r"^\+?[0-9]{7,15}$"
    return bool(re.match(pattern, text))


# ============================================
# ESCAPE MARKDOWN (if needed later)
# ============================================

def escape_markdown(text):
    """
    حماية النصوص لو استخدمت Markdown لاحقًا
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")

    return text

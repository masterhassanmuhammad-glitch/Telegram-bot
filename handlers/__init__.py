# handlers/__init__.py
from .admin import register_admin_handlers  # استدعي الإدارة أولاً
from .user import register_user_handlers
from .owner import register_owner_handlers
from .fallback import register_fallback_handlers
from .ai import register_ai_handlers  # استيراد ملف الذكاء الاصطناعي

def init_handlers():
    # الترتيب مهم جداً
    register_admin_handlers() 
    register_user_handlers()
    register_owner_handlers()
    register_fallback_handlers()
    register_ai_handlers()  # تسجيل معالجات الذكاء الاصطناعي

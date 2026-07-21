# handlers/__init__.py
from .admin import register_admin_handlers  
from .user import register_user_handlers
from .owner import register_owner_handlers
from .fallback import register_fallback_handlers  # الـ fallback يكون في النهاية

def init_handlers():
    # الترتيب الصحيح: الأوامر المخصصة أولاً، والـ Fallback في النهاية تماماً
    register_admin_handlers() 
    register_user_handlers()
    register_owner_handlers()
    register_fallback_handlers()  # الـ Fallback يلتقط الباقي فقط

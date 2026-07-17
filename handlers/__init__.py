from .users import register_user_handlers
from .admin import register_admin_handlers
from .owner import register_owner_handlers
from .fallback import register_fallback_handlers

def init_handlers():
    # ⚠️ الترتيب هنا في غاية الأهمية!
    # نسجل أولاً المعالجات ذات الشروط الصارمة لكي يتم استدعاؤها في البداية عند التطابق
    register_user_handlers()
    register_admin_handlers()
    register_owner_handlers()
    
    # نترك معالج الطوارئ في النهاية تماماً ليلتقط أي رسالة لم تجد لها حلاً مسبقاً
    register_fallback_handlers()
  

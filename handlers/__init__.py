from .admin import register_admin_handlers  
from .owner import register_owner_handlers
from .user import register_user_handlers      
from admin_logs import register_logs_handlers

def init_handlers():
    # تسجيل معالجات الإدارة والمستخدمين والمالك والسجلات
    register_admin_handlers() 
    register_owner_handlers()
    register_user_handlers()
    register_logs_handlers()
    

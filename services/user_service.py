from database import DatabaseManager
from config import OWNER_ID
import json

class UserService:
    @staticmethod
    def register_or_update_user(user_id: int, username: str, first_name: str, phone: str = '---'):
        """تسجيل المستخدم أو تحديث بياناته فوراً"""
        query = """
            INSERT INTO users (user_id, username, first_name, phone_number, is_admin)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET username = EXCLUDED.username, first_name = EXCLUDED.first_name, phone_number = EXCLUDED.phone_number
        """
        is_admin = (user_id == OWNER_ID)
        DatabaseManager.execute_query(query, (user_id, username, first_name, phone, is_admin))

    @staticmethod
    def is_user_registered(user_id: int) -> bool:
        """التحقق مما إذا كان المستخدم يمتلك رقماً مسجلاً في النظام"""
        query = "SELECT phone_number FROM users WHERE user_id = %s"
        res = DatabaseManager.execute_query(query, (user_id,), fetch='one')
        return res is not None and res['phone_number'] != '---'

    @staticmethod
    def is_admin(user_id: int) -> bool:
        """التحقق من صلاحية الإدارة (المالك أو المشرف المضاف)"""
        if user_id == OWNER_ID:
            return True
        query = "SELECT is_admin FROM users WHERE user_id = %s"
        res = DatabaseManager.execute_query(query, (user_id,), fetch='one')
        return res['is_admin'] if res else False

    @staticmethod
    def set_admin_permissions(user_id: int, permissions: dict):
        """تحديث صلاحيات المشرفين بشكل ديناميكي كامل JSONB"""
        query = "UPDATE users SET is_admin = True, permissions = %s WHERE user_id = %s"
        DatabaseManager.execute_query(query, (json.dumps(permissions), user_id))
      

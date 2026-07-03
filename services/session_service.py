import json
from database import DatabaseManager

class SessionService:
    @staticmethod
    def get_session(user_id: int) -> dict:
        """جلب جلسة المستخدم الحالية، وإن لم توجد يتم إنشاؤها تلقائياً بالقيم الافتراضية"""
        query = "SELECT * FROM sessions WHERE user_id = %s"
        res = DatabaseManager.execute_query(query, (user_id,), fetch='one')
        
        if not res:
            # إنشاء جلسة افتراضية جديدة عند أول تفاعل للبوت مع المستخدم
            insert_query = """
                INSERT INTO sessions (user_id, current_state, current_menu_id, last_message_id, context_data)
                VALUES (%s, 'MAIN_MENU', 1, NULL, '{}'::jsonb)
                ON CONFLICT (user_id) DO NOTHING
            """
            DatabaseManager.execute_query(insert_query, (user_id,))
            return {
                "user_id": user_id, 
                "current_state": "MAIN_MENU", 
                "current_menu_id": 1, 
                "last_message_id": None, 
                "context_data": {}
            }
        
        # التأكد من تحويل حقل الـ JSONB المخزن في PostgreSQL إلى قاموس بايثون (dict)
        if res['context_data'] and isinstance(res['context_data'], str):
            res['context_data'] = json.loads(res['context_data'])
        return res

    @staticmethod
    def update_session(user_id: int, state: str = None, menu_id: int = None, message_id: int = None, context_data: dict = None):
        """تحديث بيانات تتبع المستخدم الفورية (حالة التنقل، القائمة الحالية، والرسالة الفوقية لتعديلها/حذفها)"""
        session = SessionService.get_session(user_id)
        
        # إذا لم يتم تمرير متغير، نحتفظ بالقيمة القديمة الموجودة في الجلسة
        new_state = state if state is not None else session['current_state']
        new_menu_id = menu_id if menu_id is not None else session['current_menu_id']
        new_msg_id = message_id if message_id is not None else session['last_message_id']
        new_context = context_data if context_data is not None else session['context_data']

        query = """
            INSERT INTO sessions (user_id, current_state, current_menu_id, last_message_id, context_data)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE 
            SET current_state = EXCLUDED.current_state, 
                current_menu_id = EXCLUDED.current_menu_id, 
                last_message_id = EXCLUDED.last_message_id, 
                context_data = EXCLUDED.context_data
        """
        DatabaseManager.execute_query(query, (user_id, new_state, new_menu_id, new_msg_id, json.dumps(new_context)))

    @staticmethod
    def clear_session_context(user_id: int):
        """تصفير بيانات السياق المؤقتة مع الإبقاء على القائمة الرئيسية لحفظ الذاكرة"""
        query = "UPDATE sessions SET current_state = 'MAIN_MENU', context_data = '{}'::jsonb WHERE user_id = %s"
        DatabaseManager.execute_query(query, (user_id,))
      

from database import DatabaseManager

class ContentService:
    # --- إدارة مكتبة الوسائط المشتركة (Media Library) ---
    @staticmethod
    def add_to_media_library(file_id: str, file_unique_id: str, media_type: str, file_name: str = None, caption: str = None) -> int:
        """إضافة ملف إلى مكتبة الوسائط المركزية؛ إذا كان موجوداً مسبقاً يعود بمعرفه الحالي لمنع التكرار"""
        query = """
            INSERT INTO media (file_id, file_unique_id, type, file_name, caption)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (file_unique_id) DO UPDATE SET file_id = EXCLUDED.file_id
            RETURNING id
        """
        res = DatabaseManager.execute_query(query, (file_id, file_unique_id, media_type, file_name, caption), fetch='one')
        return res['id']

    # --- إدارة المحتويات (Contents) ---
    @staticmethod
    def create_content(title: str, text_content: str = None) -> int:
        """إنشاء وعاء محتوى جديد (يمكن أن يربط بنصوص أو ملفات لاحقاً)"""
        query = "INSERT INTO contents (title, text_content) VALUES (%s, %s) RETURNING id"
        res = DatabaseManager.execute_query(query, (title, text_content), fetch='one')
        return res['id']

    # --- ربط العلاقات (Many-to-Many Connections) ---
    @staticmethod
    def link_content_to_button(button_id: int, content_id: int):
        """ربط محتوى معين بزر محدد مع حساب الترتيب"""
        max_order_query = "SELECT COALESCE(MAX(sort_order), 0) as max_order FROM button_contents WHERE button_id = %s"
        max_res = DatabaseManager.execute_query(max_order_query, (button_id,), fetch='one')
        next_order = max_res['max_order'] + 1

        query = "INSERT INTO button_contents (button_id, content_id, sort_order) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
        DatabaseManager.execute_query(query, (button_id, content_id, next_order))

    @staticmethod
    def link_media_to_content(content_id: int, media_id: int):
        """ربط ملف ميديا من المكتبة بوعاء محتوى معين"""
        max_order_query = "SELECT COALESCE(MAX(sort_order), 0) as max_order FROM content_media WHERE content_id = %s"
        max_res = DatabaseManager.execute_query(max_order_query, (content_id,), fetch='one')
        next_order = max_res['max_order'] + 1

        query = "INSERT INTO content_media (content_id, media_id, sort_order) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
        DatabaseManager.execute_query(query, (content_id, media_id, next_order))

    # --- جلب البيانات للاستعراض والعرض الفوري ---
    @staticmethod
    def get_button_contents(button_id: int) -> list:
        """جلب كافة المحتويات المرتبطة بزر معين بالترتيب المحدد من قاعدة البيانات"""
        query = """
            SELECT c.* FROM contents c
            JOIN button_contents bc ON c.id = bc.content_id
            WHERE bc.button_id = %s
            ORDER BY bc.sort_order ASC
        """
        return DatabaseManager.execute_query(query, (button_id,), fetch='all')

    @staticmethod
    def get_content_media(content_id: int) -> list:
        """جلب كافة الوسائط (الصور، الملفات، الفيديوهات) المرتبطة بمحتوى معين لعرضها بالتوالي"""
        query = """
            SELECT m.* FROM media m
            JOIN content_media cm ON m.id = cm.media_id
            WHERE cm.content_id = %s
            ORDER BY cm.sort_order ASC
        """
        return DatabaseManager.execute_query(query, (content_id,), fetch='all')
      

from database import DatabaseManager

class MenuService:
    @staticmethod
    def create_menu(name: str, title: str, row_width: int = 2) -> int:
        """إنشاء قائمة (Menu) جديدة تعود بمعرفها الخاص"""
        query = "INSERT INTO menus (name, title, row_width) VALUES (%s, %s, %s) RETURNING id"
        res = DatabaseManager.execute_query(query, (name, title, row_width), fetch='one')
        return res['id']

    @staticmethod
    def get_menu(menu_id: int) -> dict:
        """جلب تفاصيل القائمة (مثل العنوان وعدد الصفوف)"""
        query = "SELECT * FROM menus WHERE id = %s"
        return DatabaseManager.execute_query(query, (menu_id,), fetch='one')

    @staticmethod
    def create_button(menu_id: int, text: str, emoji: str, btn_type: str, action_value: str, is_visible: bool = True) -> int:
        """إنشاء زر جديد داخل قائمة معينة مع حساب الترتيب التلقائي ليكون في آخر القائمة"""
        # جلب أعلى ترتيب حالي في هذه القائمة
        max_order_query = "SELECT COALESCE(MAX(sort_order), 0) as max_order FROM buttons WHERE menu_id = %s"
        max_res = DatabaseManager.execute_query(max_order_query, (menu_id,), fetch='one')
        next_order = max_res['max_order'] + 1

        query = """
            INSERT INTO buttons (menu_id, text, emoji, type, action_value, sort_order, is_visible)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        res = DatabaseManager.execute_query(query, (menu_id, text, emoji, btn_type, action_value, next_order, is_visible), fetch='one')
        return res['id']

    @staticmethod
    def get_menu_buttons(menu_id: int) -> list:
        """جلب كافة الأزرار التابعة لقائمة معينة مرتبة تصاعدياً ليتم عرضها للمستخدم"""
        query = "SELECT * FROM buttons WHERE menu_id = %s AND is_visible = True ORDER BY sort_order ASC"
        return DatabaseManager.execute_query(query, (menu_id,), fetch='all')

    @staticmethod
    def move_button_order(button_id: int, direction: str) -> bool:
        """تبديل ترتيب الزر حركياً للأعلى (↑) أو الأسفل (↓) داخل البوت"""
        current_query = "SELECT menu_id, sort_order FROM buttons WHERE id = %s"
        current = DatabaseManager.execute_query(current_query, (button_id,), fetch='one')
        if not current:
            return False

        menu_id = current['menu_id']
        current_order = current['sort_order']
        
        # البحث عن الزر المجاور الذي سيتم التبديل معه
        if direction == "up":
            swap_query = "SELECT id, sort_order FROM buttons WHERE menu_id = %s AND sort_order < %s ORDER BY sort_order DESC"
        else:
            swap_query = "SELECT id, sort_order FROM buttons WHERE menu_id = %s AND sort_order > %s ORDER BY sort_order ASC"
            
        target = DatabaseManager.execute_query(swap_query, (menu_id, current_order), fetch='one')
        if target:
            # عملية التبديل الفورية في قاعدة البيانات
            DatabaseManager.execute_query("UPDATE buttons SET sort_order = %s WHERE id = %s", (target['sort_order'], button_id))
            DatabaseManager.execute_query("UPDATE buttons SET sort_order = %s WHERE id = %s", (current_order, target['id']))
            return True
        return False

    @staticmethod
    def set_row_width(menu_id: int, width: int):
        """تعديل مظهر عدد الأزرار في الصف الواحد تلقائياً من داخل لوحة التحكم"""
        query = "UPDATE menus SET row_width = %s WHERE id = %s"
        DatabaseManager.execute_query(query, (width, menu_id))

    @staticmethod
    def delete_button(button_id: int):
        """حذف زر نهائياً"""
        query = "DELETE FROM buttons WHERE id = %s"
        DatabaseManager.execute_query(query, (button_id,))
          

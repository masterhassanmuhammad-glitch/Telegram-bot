from database import DatabaseManager

class MenuService:
    @staticmethod
    def create_menu(name: str, title: str, row_width: int = 2) -> int:
        """إنشاء قائمة جديدة"""
        query = "INSERT INTO menus (name, title, row_width) VALUES (%s, %s, %s) RETURNING id"
        res = DatabaseManager.execute_query(query, (name, title, row_width), fetch='one')
        return res['id']

    @staticmethod
    def get_menu_buttons(menu_id: int) -> list:
        """جلب كافة الأزرار التابعة لقائمة معينة مرتبة تصاعدياً"""
        query = "SELECT * FROM buttons WHERE menu_id = %s AND is_visible = True ORDER BY sort_order ASC"
        return DatabaseManager.execute_query(query, (menu_id,), fetch='all')

    @staticmethod
    def update_button_order(button_id: int, direction: str):
        """تحريك ترتيب الزر للأعلى أو الأسفل من داخل البوت"""
        current_query = "SELECT menu_id, sort_order FROM buttons WHERE id = %s"
        current = DatabaseManager.execute_query(current_query, (button_id,), fetch='one')
        if not current:
            return

        menu_id = current['menu_id']
        current_order = current['sort_order']
        
        if direction == "up":
            swap_query = "SELECT id, sort_order FROM buttons WHERE menu_id = %s AND sort_order < %s ORDER BY sort_order DESC"
        else:
            swap_query = "SELECT id, sort_order FROM buttons WHERE menu_id = %s AND sort_order > %s ORDER BY sort_order ASC"
            
        target = DatabaseManager.execute_query(swap_query, (menu_id, current_order), fetch='one')
        if target:
            # تبديل قيم الـ sort_order في قاعدة البيانات لحظياً
            DatabaseManager.execute_query("UPDATE buttons SET sort_order = %s WHERE id = %s", (target['sort_order'], button_id))
            DatabaseManager.execute_query("UPDATE buttons SET sort_order = %s WHERE id = %s", (current_order, target['id']))

    @staticmethod
    def set_row_width(menu_id: int, width: int):
        """تعديل عدد الأزرار في الصف الواحد تلقائياً للقسم"""
        query = "UPDATE menus SET row_width = %s WHERE id = %s"
        DatabaseManager.execute_query(query, (width, menu_id))
      

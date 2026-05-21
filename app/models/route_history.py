from app.models import get_db
import json

class RouteHistoryModel:
    """
    歷史紀錄與最愛路線的模型，封裝 route_history 表的 CRUD 操作。
    """
    @staticmethod
    def create(user_id, start_point, end_point, details=None, is_favorite=0, db=None):
        """
        建立一筆新的搜尋歷史或常用路線。
        details 可傳入 dict 或 list，寫入時會自動序列化為 JSON 字串。
        """
        if db is None:
            db = get_db()
        
        # 序列化 JSON 資料
        details_str = json.dumps(details, ensure_ascii=False) if details is not None else None
        
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO route_history (user_id, start_point, end_point, details, is_favorite) VALUES (?, ?, ?, ?, ?)",
            (user_id, start_point, end_point, details_str, 1 if is_favorite else 0)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_id(history_id, db=None):
        """
        查詢單筆路線紀錄。
        會自動將 details 反序列化回 Python dict 或 list。
        """
        if db is None:
            db = get_db()
        row = db.execute(
            "SELECT id, user_id, start_point, end_point, details, is_favorite, created_at FROM route_history WHERE id = ?",
            (history_id,)
        ).fetchone()
        
        if not row:
            return None
            
        data = dict(row)
        if data.get('details'):
            try:
                data['details'] = json.loads(data['details'])
            except json.JSONDecodeError:
                pass
        return data

    @staticmethod
    def get_by_user_id(user_id, only_favorites=False, db=None):
        """
        根據 user_id 獲取該使用者的所有搜尋歷史紀錄或僅獲取最愛路線。
        """
        if db is None:
            db = get_db()
        
        if only_favorites:
            rows = db.execute(
                "SELECT id, user_id, start_point, end_point, details, is_favorite, created_at "
                "FROM route_history WHERE user_id = ? AND is_favorite = 1 ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT id, user_id, start_point, end_point, details, is_favorite, created_at "
                "FROM route_history WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()
            
        result = []
        for row in rows:
            data = dict(row)
            if data.get('details'):
                try:
                    data['details'] = json.loads(data['details'])
                except json.JSONDecodeError:
                    pass
            result.append(data)
        return result

    @staticmethod
    def get_all(db=None):
        """
        獲取資料庫內所有使用者的所有路線紀錄。
        """
        if db is None:
            db = get_db()
        rows = db.execute(
            "SELECT id, user_id, start_point, end_point, details, is_favorite, created_at "
            "FROM route_history ORDER BY created_at DESC"
        ).fetchall()
        
        result = []
        for row in rows:
            data = dict(row)
            if data.get('details'):
                try:
                    data['details'] = json.loads(data['details'])
                except json.JSONDecodeError:
                    pass
            result.append(data)
        return result

    @staticmethod
    def update(history_id, start_point, end_point, details=None, is_favorite=0, db=None):
        """
        更新指定的路線紀錄資訊。
        """
        if db is None:
            db = get_db()
        
        details_str = json.dumps(details, ensure_ascii=False) if details is not None else None
        db.execute(
            "UPDATE route_history SET start_point = ?, end_point = ?, details = ?, is_favorite = ? WHERE id = ?",
            (start_point, end_point, details_str, 1 if is_favorite else 0, history_id)
        )
        db.commit()
        return True

    @staticmethod
    def update_favorite(history_id, is_favorite, db=None):
        """
        快速更新路線紀錄的收藏狀態（is_favorite 為 True 或 False）。
        """
        if db is None:
            db = get_db()
        db.execute(
            "UPDATE route_history SET is_favorite = ? WHERE id = ?",
            (1 if is_favorite else 0, history_id)
        )
        db.commit()
        return True

    @staticmethod
    def delete(history_id, db=None):
        """
        刪除指定 id 的路線紀錄。
        """
        if db is None:
            db = get_db()
        db.execute(
            "DELETE FROM route_history WHERE id = ?",
            (history_id,)
        )
        db.commit()
        return True

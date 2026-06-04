import sqlite3

class FavoriteRoute:
    def __init__(self, id, start_point, end_point, preferences, created_at):
        self.id = id
        self.start_point = start_point
        self.end_point = end_point
        self.preferences = preferences  # 逗號分隔的字串，例如 "mrt,bus"
        self.created_at = created_at

    @staticmethod
    def get_db_connection(db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def create(cls, db_path, start_point, end_point, preferences=None):
        """新增常用收藏路線"""
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO favorite_routes (start_point, end_point, preferences) VALUES (?, ?, ?)",
            (start_point, end_point, preferences)
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    @classmethod
    def get_all(cls, db_path):
        """獲取所有收藏路線列表"""
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM favorite_routes ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        routes = []
        for row in rows:
            routes.append(cls(
                id=row['id'],
                start_point=row['start_point'],
                end_point=row['end_point'],
                preferences=row['preferences'],
                created_at=row['created_at']
            ))
        return routes

    @classmethod
    def get_by_id(cls, db_path, route_id):
        """依 ID 查詢收藏路線"""
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM favorite_routes WHERE id = ?", (route_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls(
                id=row['id'],
                start_point=row['start_point'],
                end_point=row['end_point'],
                preferences=row['preferences'],
                created_at=row['created_at']
            )
        return None

    @classmethod
    def delete(cls, db_path, route_id):
        """刪除特定收藏路線"""
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favorite_routes WHERE id = ?", (route_id,))
        conn.commit()
        conn.close()
        return True

from app.models import get_db
import sqlite3

class UserModel:
    """
    使用者資料模型，封裝 user 表的所有 CRUD 操作。
    """
    @staticmethod
    def create(username, password_hash, email, db=None):
        """
        建立新使用者。
        若 username 或 email 已存在，將拋出 sqlite3.IntegrityError。
        回傳值為新使用者的自增 id。
        """
        if db is None:
            db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO user (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_id(user_id, db=None):
        """
        根據 id 查詢使用者。
        回傳包含使用者欄位資料的字典，若不存在則回傳 None。
        """
        if db is None:
            db = get_db()
        row = db.execute(
            "SELECT id, username, password_hash, email, created_at FROM user WHERE id = ?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_username(username, db=None):
        """
        根據使用者帳號 (username) 查詢使用者。
        常用於登入驗證與重名檢查。
        """
        if db is None:
            db = get_db()
        row = db.execute(
            "SELECT id, username, password_hash, email, created_at FROM user WHERE username = ?",
            (username,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_all(db=None):
        """
        獲取所有使用者列表。
        """
        if db is None:
            db = get_db()
        rows = db.execute("SELECT id, username, email, created_at FROM user").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def update(user_id, username, email, db=None):
        """
        更新使用者的帳號或電子郵件。
        """
        if db is None:
            db = get_db()
        db.execute(
            "UPDATE user SET username = ?, email = ? WHERE id = ?",
            (username, email, user_id)
        )
        db.commit()
        return True

    @staticmethod
    def delete(user_id, db=None):
        """
        刪除指定 id 的使用者。
        由於設定了 FOREIGN KEY ON DELETE CASCADE，此操作將自動刪除該使用者的所有歷史與最愛紀錄。
        """
        if db is None:
            db = get_db()
        db.execute(
            "DELETE FROM user WHERE id = ?",
            (user_id,)
        )
        db.commit()
        return True

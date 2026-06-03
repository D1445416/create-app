import sqlite3
import os
from flask import g, current_app

# 預設資料庫檔案路徑，位於 instance/database.db
DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../instance/database.db'))

def get_db():
    """
    獲取 SQLite 資料庫連線。
    如果處於 Flask 應用上下文中，會將連線綁定在 flask.g 上以重複使用，並在請求結束時自動關閉；
    如果不在 Flask 上下文（如單機測試、遷移腳本），則直接返回一個新的連線。
    """
    try:
        # 試圖存取 flask.g，若處於 Flask 請求上下文中
        if 'db' not in g:
            db_path = current_app.config.get('DATABASE', DEFAULT_DB_PATH)
            # 確保資料庫目錄存在
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
            # 啟用 SQLite 的外鍵（Foreign Key）約束
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db
    except RuntimeError:
        # 若不在 Flask 應用上下文中（例如直接執行測試腳本）
        os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        conn.row_factory = sqlite3.Row
        # 啟用外鍵約束
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def init_db(db=None):
    """
    讀取 database/schema.sql 並執行以初始化資料表。
    """
    close_after = False
    if db is None:
        db = get_db()
        # 如果是在 Flask 外取得獨立連線，記得在初始化後關閉它
        try:
            g
        except RuntimeError:
            close_after = True
            
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../database/schema.sql'))
    with open(schema_path, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()
    
    if close_after:
        db.close()

import os
import sqlite3
from datetime import datetime

# 預設資料庫路徑為專案根目錄下的 instance/database.db
DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'instance',
        'database.db'
    )
)

# 預設 Schema 檔案路徑
DEFAULT_SCHEMA_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'database',
        'schema.sql'
    )
)

def get_db_connection(db_path=None):
    """
    建立 SQLite 資料庫連接，並啟用外鍵約束。
    若資料庫檔案或資料表不存在，則會自動進行初始化。
    """
    path = db_path or DEFAULT_DB_PATH
    db_dir = os.path.dirname(path)
    
    # 自動建立 instance 資料夾
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # 允許使用欄位名稱存取欄位資料
    conn.execute("PRAGMA foreign_keys = ON;")  # 啟用外鍵約束
    
    # 檢查是否需要初始化資料表
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stations';")
    if not cursor.fetchone():
        init_db(conn)
        
    return conn

def init_db(conn):
    """
    讀取 schema.sql 並初始化資料庫表結構。
    """
    if os.path.exists(DEFAULT_SCHEMA_PATH):
        with open(DEFAULT_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
    else:
        # 若找不到外部 schema 檔案，使用備用內嵌 SQL
        backup_schema = """
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('metro', 'bus')),
            route_name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS crowdedness_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT UNIQUE NOT NULL,
            level TEXT NOT NULL CHECK(level IN ('green', 'orange', 'red')),
            passenger_count INTEGER DEFAULT 0,
            last_updated TEXT NOT NULL,
            FOREIGN KEY(station_id) REFERENCES stations(station_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_stations_type ON stations(type);
        CREATE INDEX IF NOT EXISTS idx_stations_route ON stations(route_name);
        """
        conn.executescript(backup_schema)
        conn.commit()


class Station:
    """
    大眾運輸站點 (stations) 的資料模型與 CRUD 存取邏輯
    """
    def __init__(self, id, station_id, name, lat, lng, type, route_name, created_at=None):
        self.id = id
        self.station_id = station_id
        self.name = name
        self.lat = lat
        self.lng = lng
        self.type = type
        self.route_name = route_name
        self.created_at = created_at

    @classmethod
    def from_row(cls, row):
        """將 SQLite Row 轉成 Station 物件"""
        if not row:
            return None
        return cls(
            id=row['id'],
            station_id=row['station_id'],
            name=row['name'],
            lat=row['lat'],
            lng=row['lng'],
            type=row['type'],
            route_name=row['route_name'],
            created_at=row['created_at']
        )

    # ==================== CRUD 方法 ====================

    @classmethod
    def create(cls, station_id, name, lat, lng, type, route_name, db_path=None):
        """
        C: 新增一個大眾運輸站點
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO stations (station_id, name, lat, lng, type, route_name)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (station_id, name, lat, lng, type, route_name)
            )
            conn.commit()
            inserted_id = cursor.lastrowid
            return cls(inserted_id, station_id, name, lat, lng, type, route_name)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"站點 ID '{station_id}' 已經存在或不符合約束: {e}")
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, station_id, db_path=None):
        """
        R: 根據 station_id 取得特定站點資料
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stations WHERE station_id = ?", (station_id,))
        row = cursor.fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def get_all(cls, db_path=None):
        """
        R: 取得所有站點資料
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stations ORDER BY type, station_id")
        rows = cursor.fetchall()
        conn.close()
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_all_with_crowdedness(cls, db_path=None):
        """
        R: 取得所有站點，並合併其擁擠度快取資料 (LEFT JOIN)
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.*, c.level, c.passenger_count, c.last_updated
            FROM stations s
            LEFT JOIN crowdedness_cache c ON s.station_id = c.station_id
            ORDER BY s.type, s.station_id
            """
        )
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            station_data = cls.from_row(row)
            # 將 crowdedness_cache 資料作為屬性動態綁定至 Station 物件
            station_data.level = row['level'] if row['level'] else 'green' # 預設為綠色(通暢)
            station_data.passenger_count = row['passenger_count'] if row['passenger_count'] is not None else 0
            station_data.last_updated = row['last_updated']
            results.append(station_data)
        return results

    @classmethod
    def get_nearby(cls, user_lat, user_lng, limit=5, db_path=None):
        """
        R: 使用者位置周邊站點推薦 (依距離排序)
        在 SQLite 中使用簡單的歐幾里得距離平方來計算最近距離
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        # 使用 SQLite 計算 (lat - user_lat)^2 + (lng - user_lng)^2 來排序
        cursor.execute(
            """
            SELECT s.*, c.level, c.passenger_count, c.last_updated,
                   ((s.lat - ?) * (s.lat - ?) + (s.lng - ?) * (s.lng - ?)) AS distance_sq
            FROM stations s
            LEFT JOIN crowdedness_cache c ON s.station_id = c.station_id
            ORDER BY distance_sq ASC
            LIMIT ?
            """,
            (user_lat, user_lat, user_lng, user_lng, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            station_data = cls.from_row(row)
            station_data.level = row['level'] if row['level'] else 'green'
            station_data.passenger_count = row['passenger_count'] if row['passenger_count'] is not None else 0
            station_data.last_updated = row['last_updated']
            station_data.distance_sq = row['distance_sq']
            results.append(station_data)
        return results

    @classmethod
    def update(cls, station_id, name=None, lat=None, lng=None, type=None, route_name=None, db_path=None):
        """
        U: 更新站點基本資料
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # 動態組合 SET 語句
        fields = []
        params = []
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if lat is not None:
            fields.append("lat = ?")
            params.append(lat)
        if lng is not None:
            fields.append("lng = ?")
            params.append(lng)
        if type is not None:
            if type not in ('metro', 'bus'):
                raise ValueError("類型必須為 'metro' 或 'bus'")
            fields.append("type = ?")
            params.append(type)
        if route_name is not None:
            fields.append("route_name = ?")
            params.append(route_name)
            
        if not fields:
            conn.close()
            return False  # 沒有提供要更新的欄位
            
        params.append(station_id)
        sql = f"UPDATE stations SET {', '.join(fields)} WHERE station_id = ?"
        
        try:
            cursor.execute(sql, params)
            conn.commit()
            success = cursor.rowcount > 0
            return success
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"更新站點失敗: {e}")
        finally:
            conn.close()

    @classmethod
    def delete(cls, station_id, db_path=None):
        """
        D: 刪除站點 (由於外鍵設置 ON DELETE CASCADE，將一併刪除該站點的擁擠度快取)
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM stations WHERE station_id = ?", (station_id,))
            conn.commit()
            success = cursor.rowcount > 0
            return success
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"刪除站點失敗: {e}")
        finally:
            conn.close()


class CrowdednessCache:
    """
    即時擁擠度資料快取 (crowdedness_cache) 的資料模型與 CRUD 存取邏輯
    """
    def __init__(self, id, station_id, level, passenger_count, last_updated):
        self.id = id
        self.station_id = station_id
        self.level = level
        self.passenger_count = passenger_count
        self.last_updated = last_updated

    @classmethod
    def from_row(cls, row):
        """將 SQLite Row 轉成 CrowdednessCache 物件"""
        if not row:
            return None
        return cls(
            id=row['id'],
            station_id=row['station_id'],
            level=row['level'],
            passenger_count=row['passenger_count'],
            last_updated=row['last_updated']
        )

    # ==================== CRUD 方法 ====================

    @classmethod
    def create_or_update(cls, station_id, level, passenger_count=0, last_updated=None, db_path=None):
        """
        C & U: 新增或更新某站點的擁擠度快取資料 (Upsert 機制)
        """
        if level not in ('green', 'orange', 'red'):
            raise ValueError("擁擠度等級必須是 'green', 'orange' 或 'red'")
            
        update_time = last_updated or datetime.now().isoformat()
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        try:
            # 檢查 stations 表中是否有此 station_id (符合外鍵約束)
            cursor.execute("SELECT 1 FROM stations WHERE station_id = ?", (station_id,))
            if not cursor.fetchone():
                raise ValueError(f"無法為不存在的站點 ID '{station_id}' 建立擁擠度快取。")

            # SQLite UPSERT 語法 (INSERT ... ON CONFLICT(station_id) DO UPDATE)
            cursor.execute(
                """
                INSERT INTO crowdedness_cache (station_id, level, passenger_count, last_updated)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(station_id) DO UPDATE SET
                    level = excluded.level,
                    passenger_count = excluded.passenger_count,
                    last_updated = excluded.last_updated
                """,
                (station_id, level, passenger_count, update_time)
            )
            conn.commit()
            
            # 取得該紀錄
            cursor.execute("SELECT * FROM crowdedness_cache WHERE station_id = ?", (station_id,))
            row = cursor.fetchone()
            return cls.from_row(row)
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"寫入擁擠度快取失敗: {e}")
        finally:
            conn.close()

    @classmethod
    def get_by_station_id(cls, station_id, db_path=None):
        """
        R: 取得特定站點的擁擠度快取
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crowdedness_cache WHERE station_id = ?", (station_id,))
        row = cursor.fetchone()
        conn.close()
        return cls.from_row(row)

    @classmethod
    def is_cache_valid(cls, station_id, cache_duration_seconds=60, db_path=None):
        """
        判斷特定站點的快取是否依然有效 (在指定的秒數內)
        """
        cache = cls.get_by_station_id(station_id, db_path)
        if not cache:
            return False
            
        try:
            last_updated_dt = datetime.fromisoformat(cache.last_updated)
            time_diff = (datetime.now() - last_updated_dt).total_seconds()
            return time_diff < cache_duration_seconds
        except Exception:
            return False

    @classmethod
    def delete(cls, station_id, db_path=None):
        """
        D: 刪除特定站點的擁擠度快取
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM crowdedness_cache WHERE station_id = ?", (station_id,))
            conn.commit()
            success = cursor.rowcount > 0
            return success
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"刪除快取失敗: {e}")
        finally:
            conn.close()

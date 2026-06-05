-- 啟用外鍵約束
PRAGMA foreign_keys = ON;

-- 建立使用者資料表
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 建立路線歷史與最愛資料表
CREATE TABLE IF NOT EXISTS route_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    start_point TEXT NOT NULL,
    end_point TEXT NOT NULL,
    is_favorite INTEGER NOT NULL DEFAULT 0 CHECK(is_favorite IN (0, 1)),
    details TEXT, -- 存儲 JSON 格式路線詳細資料
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 建立大眾運輸站點資料表
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

-- 建立即時擁擠度快取資料表
CREATE TABLE IF NOT EXISTS crowdedness_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT UNIQUE NOT NULL,
    level TEXT NOT NULL CHECK(level IN ('green', 'orange', 'red')),
    passenger_count INTEGER DEFAULT 0,
    last_updated TEXT NOT NULL,
    FOREIGN KEY(station_id) REFERENCES stations(station_id) ON DELETE CASCADE
);

-- 建立收藏站點資料表
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT UNIQUE NOT NULL,
    added_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(station_id) REFERENCES stations(station_id) ON DELETE CASCADE
);

-- 建立收藏路線資料表
CREATE TABLE IF NOT EXISTS favorite_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_point TEXT NOT NULL,
    end_point TEXT NOT NULL,
    preferences TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 建立索引以優化查詢
CREATE INDEX IF NOT EXISTS idx_route_history_user_id ON route_history(user_id);
CREATE INDEX IF NOT EXISTS idx_route_history_favorite ON route_history(user_id, is_favorite);
CREATE INDEX IF NOT EXISTS idx_stations_type ON stations(type);
CREATE INDEX IF NOT EXISTS idx_stations_route ON stations(route_name);

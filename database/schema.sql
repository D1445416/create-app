-- 台中大眾運輸站點狀態與擁擠度顯示系統 - SQLite 資料表結構 Schema
-- 檔案路徑: database/schema.sql

-- 啟用外鍵約束 (需要在連接 SQLite 時執行 PRAGMA foreign_keys = ON)
PRAGMA foreign_keys = ON;

-- 1. 站點基本資料表 (stations)
CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT UNIQUE NOT NULL,               -- 站點唯一代碼 (例如: 'BL01', '300_1')
    name TEXT NOT NULL,                            -- 站點中文名稱 (例如: '台中車站')
    lat REAL NOT NULL,                             -- 站點緯度 (Latitude)
    lng REAL NOT NULL,                             -- 站點經度 (Longitude)
    type TEXT NOT NULL CHECK(type IN ('metro', 'bus')), -- 站點類型 ('metro' 表示捷運, 'bus' 表示公車)
    route_name TEXT NOT NULL,                      -- 所屬路線名稱 (例如: '捷運綠線', '300路公車')
    created_at TEXT DEFAULT (datetime('now', 'localtime')) -- 建立時間
);

-- 2. 擁擠度資料快取表 (crowdedness_cache)
CREATE TABLE IF NOT EXISTS crowdedness_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT UNIQUE NOT NULL,               -- 關聯至 stations.station_id
    level TEXT NOT NULL CHECK(level IN ('green', 'orange', 'red')), -- 擁擠度等級 (green: 通暢, orange: 普通, red: 擁擠)
    passenger_count INTEGER DEFAULT 0,             -- 即時或累計乘客人數
    last_updated TEXT NOT NULL,                    -- 快取最後更新時間 (ISO 8601 格式，如 '2026-05-21T08:24:57')
    FOREIGN KEY(station_id) REFERENCES stations(station_id) ON DELETE CASCADE
);

-- 建立索引以提升搜尋效能
CREATE INDEX IF NOT EXISTS idx_stations_type ON stations(type);
CREATE INDEX IF NOT EXISTS idx_stations_route ON stations(route_name);
CREATE INDEX IF NOT EXISTS idx_stations_coords ON stations(lat, lng);

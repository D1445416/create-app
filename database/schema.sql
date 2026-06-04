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

-- 建立索引以優化查詢
CREATE INDEX IF NOT EXISTS idx_route_history_user_id ON route_history(user_id);
CREATE INDEX IF NOT EXISTS idx_route_history_favorite ON route_history(user_id, is_favorite);

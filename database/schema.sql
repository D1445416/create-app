-- SQLite 建表語法

-- 建立常用路線收藏表 (F-03/F-05)
CREATE TABLE IF NOT EXISTS favorite_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_point TEXT NOT NULL,
    end_point TEXT NOT NULL,
    preferences TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

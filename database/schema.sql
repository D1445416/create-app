CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT UNIQUE NOT NULL,
    station_name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    transport_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES stations (station_id)
);

-- Seed initial stations
INSERT OR IGNORE INTO stations (station_id, station_name, lat, lon, transport_type) VALUES
('BUS_01', '台中車站(民族路口)', 24.1373, 120.6856, 'Bus'),
('MRT_01', '市政府站', 24.1628, 120.6439, 'MRT'),
('BUS_02', '新光/遠東', 24.1645, 120.6433, 'Bus');

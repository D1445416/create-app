import os
import sqlite3
import requests
from dotenv import load_dotenv

def get_token(client_id, client_secret):
    url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Token error {response.status_code}: {response.text}")
    except Exception as e:
        print("Failed to request token:", e)
    return None

def fetch_and_seed_all():
    # Load .env
    load_dotenv()
    
    client_id = os.getenv("TDX_CLIENT_ID")
    client_secret = os.getenv("TDX_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Error: TDX_CLIENT_ID or TDX_CLIENT_SECRET is missing in .env")
        return False
        
    print("Authenticating with TDX...")
    token = get_token(client_id, client_secret)
    if not token:
        print("Error: Could not retrieve TDX token.")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Fetch MRT Stations
    print("Fetching TMRT Stations...")
    mrt_url = "https://tdx.transportdata.tw/api/basic/v2/Rail/Metro/Station/TMRT?$format=JSON"
    mrt_stations = []
    try:
        res = requests.get(mrt_url, headers=headers, timeout=10)
        if res.status_code == 200:
            mrt_stations = res.json()
            print(f"Successfully fetched {len(mrt_stations)} TMRT Stations.")
        else:
            print(f"Failed to fetch TMRT Stations: {res.status_code}")
    except Exception as e:
        print("Error fetching TMRT Stations:", e)
        
    # 2. Fetch Taichung Bus Stops
    print("Fetching Taichung Bus Stops (up to 600)...")
    bus_url = "https://tdx.transportdata.tw/api/basic/v2/Bus/Stop/City/Taichung?$top=600&$format=JSON"
    bus_stops = []
    try:
        res = requests.get(bus_url, headers=headers, timeout=15)
        if res.status_code == 200:
            bus_stops = res.json()
            print(f"Successfully fetched {len(bus_stops)} Bus Stops.")
        else:
            print(f"Failed to fetch Bus Stops: {res.status_code}")
    except Exception as e:
        print("Error fetching Bus Stops:", e)
        
    if not mrt_stations and not bus_stops:
        print("No stations or stops fetched. Seeding aborted.")
        return False
        
    # Database operations
    db_path = os.path.join(os.getcwd(), 'instance', 'database.db')
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
        
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    
    # Create tables if not exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stations (
        station_id TEXT PRIMARY KEY,
        station_name TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        transport_type TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id TEXT NOT NULL,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (station_id) REFERENCES stations (station_id)
    )
    """)
    db.commit()
    
    # Clear existing stations
    cursor.execute("DELETE FROM stations")
    
    # Track 市政府捷運站 coordinates for transfer hub
    gov_lat = 24.1628
    gov_lon = 120.6439
    
    # Track 台中車站 coordinates for transfer hub
    tc_lat = 24.1373
    tc_lon = 120.6856
    
    # Seed MRT stations
    mrt_count = 0
    for station in mrt_stations:
        s_id = station.get("StationID")
        name = station.get("StationName", {}).get("Zh_tw", "")
        pos = station.get("StationPosition", {})
        lat = pos.get("PositionLat")
        lon = pos.get("PositionLon")
        
        if s_id and name and lat is not None and lon is not None:
            # Normalize ID as MRT_XX
            mrt_id = f"MRT_{s_id}"
            cursor.execute(
                "INSERT INTO stations (station_id, station_name, lat, lon, transport_type) VALUES (?, ?, ?, ?, ?)",
                (mrt_id, name, lat, lon, "mrt")
            )
            mrt_count += 1
            if "市政府" in name:
                gov_lat = lat
                gov_lon = lon
                
    print(f"Seeded {mrt_count} MRT stations to database.")
    
    # Seed Bus stops (with de-duplication by name)
    seen_names = set()
    bus_count = 0
    for stop in bus_stops:
        s_uid = stop.get("StopUID")
        name = stop.get("StopName", {}).get("Zh_tw", "")
        pos = stop.get("StopPosition", {})
        lat = pos.get("PositionLat")
        lon = pos.get("PositionLon")
        
        if name and lat is not None and lon is not None:
            # Skip if name already added or matches pure garbled text
            if name in seen_names:
                continue
            if not name.strip():
                continue
                
            seen_names.add(name)
            # Normalize ID as BUS_XX
            bus_id = f"BUS_{s_uid}"
            cursor.execute(
                "INSERT INTO stations (station_id, station_name, lat, lon, transport_type) VALUES (?, ?, ?, ?, ?)",
                (bus_id, name, lat, lon, "bus")
            )
            bus_count += 1
            if "台中車站" in name and ("台灣大道" in name or "復興路" in name or "東站" in name):
                tc_lat = lat
                tc_lon = lon
                
    print(f"Seeded {bus_count} unique Bus stops to database.")
    
    # Seed 2 major Transfer Hubs
    cursor.execute(
        "INSERT INTO stations (station_id, station_name, lat, lon, transport_type) VALUES (?, ?, ?, ?, ?)",
        ("HUB_01", "市政府站轉乘樞紐", gov_lat, gov_lon, "transfer")
    )
    cursor.execute(
        "INSERT INTO stations (station_id, station_name, lat, lon, transport_type) VALUES (?, ?, ?, ?, ?)",
        ("HUB_02", "台中車站轉乘樞紐", tc_lat, tc_lon, "transfer")
    )
    db.commit()
    db.close()
    
    print("Transfer hubs seeded successfully.")
    print("Database seeding completed!")
    return True

if __name__ == "__main__":
    fetch_and_seed_all()

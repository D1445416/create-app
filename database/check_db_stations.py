import sqlite3
import requests
import json

def verify():
    # 1. Verify Database
    db_path = "instance/database.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM stations")
    count = cursor.fetchone()[0]
    print(f"Total stations in DB: {count}")
    
    cursor.execute("SELECT * FROM stations WHERE transport_type = 'mrt' LIMIT 3")
    mrt_rows = [dict(r) for r in cursor.fetchall()]
    print("\nSample MRT Stations in DB:")
    print(json.dumps(mrt_rows, indent=2, ensure_ascii=False))
    
    cursor.execute("SELECT * FROM stations WHERE transport_type = 'bus' LIMIT 3")
    bus_rows = [dict(r) for r in cursor.fetchall()]
    print("\nSample Bus Stops in DB:")
    print(json.dumps(bus_rows, indent=2, ensure_ascii=False))
    
    cursor.execute("SELECT * FROM stations WHERE transport_type = 'transfer'")
    transfer_rows = [dict(r) for r in cursor.fetchall()]
    print("\nTransfer Hubs in DB:")
    print(json.dumps(transfer_rows, indent=2, ensure_ascii=False))
    
    conn.close()
    
    # 2. Verify Flask App API Endpoints
    print("\n--- Verifying Flask App APIs ---")
    base_url = "http://127.0.0.1:5000"
    
    # Test /api/stations
    try:
        res = requests.get(f"{base_url}/api/stations")
        print(f"GET /api/stations -> Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"  Returned {len(data['data'])} stations in JSON.")
    except Exception as e:
        print("  Error calling /api/stations:", e)
        
    # Test /api/station/HUB_01 (Transfer Hub)
    try:
        res = requests.get(f"{base_url}/api/station/HUB_01")
        print(f"GET /api/station/HUB_01 -> Status: {res.status_code}")
        if res.status_code == 200:
            print("  Response (HUB_01):")
            print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print("  Error calling /api/station/HUB_01:", e)

    # Test /api/station/MRT_110 (市政府捷運站)
    try:
        res = requests.get(f"{base_url}/api/station/MRT_110")
        print(f"GET /api/station/MRT_110 -> Status: {res.status_code}")
        if res.status_code == 200:
            print("  Response (MRT_110):")
            print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print("  Error calling /api/station/MRT_110:", e)

    # Test a Bus Station
    if bus_rows:
        sample_bus_id = bus_rows[0]["station_id"]
        try:
            res = requests.get(f"{base_url}/api/station/{sample_bus_id}")
            print(f"GET /api/station/{sample_bus_id} -> Status: {res.status_code}")
            if res.status_code == 200:
                print(f"  Response ({sample_bus_id}):")
                print(json.dumps(res.json(), indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"  Error calling /api/station/{sample_bus_id}:", e)

if __name__ == "__main__":
    verify()

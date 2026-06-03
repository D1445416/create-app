import os
from app import create_app
from app.models import Station, CrowdednessCache, get_db_connection, init_db
from app.services import tdx_service

def seed_database():
    print("=== 開始進行台中大眾運輸站點資料初始化 (Seeding) ===")
    
    # 1. 建立 Flask app 與初始化資料庫結構
    app = create_app()
    db_path = app.config['DATABASE']
    
    # 清理舊的資料庫以確保乾淨的 Seed
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"已清理既有資料庫: {db_path}")

    conn = get_db_connection(db_path)
    init_db(conn)
    conn.close()
    print("資料庫結構初始化成功！")

    # 2. 定義首批精緻測試站點資料
    seed_stations = [
        # 台中捷運綠線主要站點
        {"station_id": "BL01", "name": "市政府捷運站", "lat": 24.1627, "lng": 120.6479, "type": "metro", "route_name": "捷運綠線"},
        {"station_id": "BL02", "name": "水安宮捷運站", "lat": 24.1537, "lng": 120.6444, "type": "metro", "route_name": "捷運綠線"},
        {"station_id": "BL03", "name": "文心森林公園捷運站", "lat": 24.1437, "lng": 120.6436, "type": "metro", "route_name": "捷運綠線"},
        {"station_id": "BL04", "name": "松竹捷運站", "lat": 24.1802, "lng": 120.7011, "type": "metro", "route_name": "捷運綠線"},
        {"station_id": "BL05", "name": "高鐵台中捷運站", "lat": 24.1121, "lng": 120.6146, "type": "metro", "route_name": "捷運綠線"},
        
        # 台中台灣大道幹線 300路 重要公車站點
        {"station_id": "300_1", "name": "台中車站(台灣大道)", "lat": 24.1373, "lng": 120.6868, "type": "bus", "route_name": "300路公車"},
        {"station_id": "300_2", "name": "第二市場公車站", "lat": 24.1424, "lng": 120.6784, "type": "bus", "route_name": "300路公車"},
        {"station_id": "300_3", "name": "科博館公車站", "lat": 24.1561, "lng": 120.6622, "type": "bus", "route_name": "300路公車"},
        {"station_id": "300_4", "name": "秋紅谷公車站", "lat": 24.1673, "lng": 120.6397, "type": "bus", "route_name": "300路公車"},
    ]

    # 3. 寫入站點至資料庫
    print("\n[第一階段] 寫入大眾運輸站點靜態基本資料...")
    inserted_count = 0
    for s in seed_stations:
        try:
            Station.create(
                s["station_id"],
                s["name"],
                s["lat"],
                s["lng"],
                s["type"],
                s["route_name"],
                db_path=db_path
            )
            print(f" -> OK: {s['name']} ({s['station_id']})")
            inserted_count += 1
        except Exception as e:
            print(f" [!] Error {s['name']}: {str(e)}")

    print(f"第一階段完成：成功載入 {inserted_count} 筆基礎站點。")

    # 4. 初始化即時人潮快取 (Seeding initial cache)
    print("\n[第二階段] 初始化各站點即時擁擠度快取 (TDX API 預熱)...")
    cached_count = 0
    for s in seed_stations:
        try:
            # 呼叫 TDX 服務取得資料 (若無 credentials 則使用高仿真模擬)
            realtime_data = tdx_service.get_realtime_crowdedness(
                s["station_id"],
                s["name"],
                s["type"]
            )
            CrowdednessCache.create_or_update(
                s["station_id"],
                realtime_data["level"],
                realtime_data["passenger_count"],
                realtime_data["last_updated"],
                db_path=db_path
            )
            print(f" -> Cache: {s['name']} | level={realtime_data['level']} | pax={realtime_data['passenger_count']}")
            cached_count += 1
        except Exception as e:
            print(f" [!] Cache Error {s['name']}: {str(e)}")

    print(f"第二階段完成：成功預熱 {cached_count} 筆擁擠度快取資料。")
    print("\n=======================================================")
    print(" 台中大眾運輸站點擁擠度顯示系統資料庫 Seed 初始化完畢！")
    print(f" 資料庫檔案儲存於: {db_path}")
    print("=======================================================")

if __name__ == '__main__':
    seed_database()

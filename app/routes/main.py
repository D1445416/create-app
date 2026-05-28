from flask import Blueprint, jsonify, render_template, request, current_app, redirect, url_for
import sqlite3
import math
from utils.tdx import TDXClient
from utils.pricing import calculate_total_fare
from utils.tdx_time import get_estimated_time

main_bp = Blueprint('main', __name__)
tdx = TDXClient()

def get_db():
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def get_distance(lat1, lon1, lat2, lon2):
    # Haversine formula to calculate distance in km
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/favorites')
def favorites_page():
    # 渲染收藏頁面
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.station_id, s.station_name, s.lat, s.lon, s.transport_type, f.added_at
        FROM favorites f
        JOIN stations s ON f.station_id = s.station_id
        ORDER BY f.added_at DESC
    """)
    rows = cursor.fetchall()
    favorites_list = [dict(row) for row in rows]
    db.close()
    return render_template('favorites.html', favorites=favorites_list)

@main_bp.route('/api/stations')
def get_all_stations():
    # 回傳所有站點，供地圖初始化標記使用
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM stations")
    rows = cursor.fetchall()
    stations_list = [dict(row) for row in rows]
    db.close()
    return jsonify({
        "status": "success",
        "data": stations_list
    })

@main_bp.route('/api/station/<station_id>')
def get_station_info(station_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM stations WHERE station_id = ?", (station_id,))
    row = cursor.fetchone()
    db.close()
    
    if not row:
        return jsonify({"status": "error", "message": "Station not found"}), 404
        
    station = dict(row)
    t_type = station['transport_type']
    
    # 根據運具類型獲取動態數據
    # 轉乘樞紐 (transfer) 同時獲取公車與捷運數據，實現「併列呈現」
    bus_data = []
    mrt_data = []
    
    if t_type == 'bus' or t_type == 'transfer':
        bus_data = tdx.get_bus_arrival(station_id, station['station_name'])
    if t_type == 'mrt' or t_type == 'transfer':
        mrt_data = tdx.get_mrt_arrival(station_id, station['station_name'])
        
    return jsonify({
        "status": "success",
        "data": {
            "station_id": station['station_id'],
            "station_name": station['station_name'],
            "lat": station['lat'],
            "lon": station['lon'],
            "transport_type": t_type,
            "bus": bus_data,
            "mrt": mrt_data
        }
    })

@main_bp.route('/api/v1/calculate_trip', methods=['POST'])
def calculate_trip():
    # 對應 test_app.py，進行多運具票價與時間演算
    data = request.get_json() or {}
    segments = data.get("segments", [])
    
    fare_res = calculate_total_fare(segments)
    time_res = get_estimated_time(segments)
    
    return jsonify({
        "status": "success",
        "total_fare": fare_res["total_fare"],
        "total_minutes": time_res["total_minutes"],
        "details": {
            "fare": fare_res["details"],
            "duration": time_res["details"]
        }
    })

@main_bp.route('/api/v1/route_plans')
def get_route_plans():
    start_id = request.args.get('start')
    end_id = request.args.get('end')
    
    if not start_id or not end_id:
        return jsonify({"status": "error", "message": "Missing start or end station"}), 400
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM stations WHERE station_id = ?", (start_id,))
    start_row = cursor.fetchone()
    cursor.execute("SELECT * FROM stations WHERE station_id = ?", (end_id,))
    end_row = cursor.fetchone()
    db.close()
    
    if not start_row or not end_row:
        return jsonify({"status": "error", "message": "Start or end station not found"}), 404
        
    start_sta = dict(start_row)
    end_sta = dict(end_row)
    
    # 計算起終點直線距離 (Haversine km)
    distance = get_distance(start_sta['lat'], start_sta['lon'], end_sta['lat'], end_sta['lon'])
    if distance < 0.05:
        distance = 0.5
        
    # 智慧路網匹配：根據起訖站地理位置，動態過濾推薦最真實的台中公車
    bus_route = "73" # 預設路線
    start_name = start_sta['station_name']
    end_name = end_sta['station_name']
    
    if "逢甲" in start_name or "逢甲" in end_name or "僑光" in start_name or "僑光" in end_name:
        bus_route = "35" # 35, 25 經過逢甲與僑光
    elif "台中車站" in start_name or "台中車站" in end_name:
        if "市政府" in start_name or "市政府" in end_name or "秋紅谷" in start_name or "秋紅谷" in end_name:
            bus_route = "300" # 台灣大道幹線公車
        else:
            bus_route = "81" # 往車站的區域公車
    elif "科博館" in start_name or "秋紅谷" in start_name or "市政府" in start_name:
        bus_route = "300"

    # 判斷是否適合連結捷運線 (距離 >= 2.0 km 且起訖點附近有捷運站點)
    has_mrt_access = (start_sta['transport_type'] in ['mrt', 'transfer'] or end_sta['transport_type'] in ['mrt', 'transfer'])
    
    plans = []
    
    # 情況 A：短途移動 (距離 < 2.0 公里，例如逢甲 ➔ 僑光) ➔ 全程不需要硬塞捷運與幹線300公車！
    if distance < 2.0:
        # 1. YouBike 綠能方案
        seg_bike = [
            {"type": "youbike", "minutes": max(3, int(distance * 5)), "distance_km": distance}
        ]
        res_bike_fare = calculate_total_fare(seg_bike)
        res_bike_time = get_estimated_time(seg_bike)
        
        # 2. 區域短途公車
        seg_bus = [
            {"type": "bus", "route_id": bus_route, "distance_km": distance}
        ]
        res_bus_fare = calculate_total_fare(seg_bus)
        res_bus_time = get_estimated_time(seg_bus)
        
        # 3. 步行舒活方案
        seg_walk = [
            {"type": "walking", "distance_km": distance}
        ]
        res_walk_fare = calculate_total_fare(seg_walk)
        res_walk_time = get_estimated_time(seg_walk)
        
        plans = [
            {
                "id": "plan_green", # 保持前端對應 ID 避免繪圖損壞
                "name": "綠能環保 YouBike",
                "description": "短距離移動最佳首選，低碳環保又健康",
                "total_fare": res_bike_fare["total_fare"],
                "total_minutes": res_bike_time["total_minutes"],
                "segments": [
                    {"type": "youbike", "desc": "騎乘 YouBike 2.0", "value": f"直達 {distance} km", "minutes": res_bike_time["details"][0]["estimated_minutes"], "fare": res_bike_fare["details"][0]["fare"]}
                ],
                "path": [
                    [start_sta['lat'], start_sta['lon']],
                    [end_sta['lat'], end_sta['lon']]
                ]
            },
            {
                "id": "plan_bus",
                "name": "區域公車方案",
                "description": f"搭乘台中市 {bus_route} 路區域公車，享市民雙十優惠",
                "total_fare": res_bus_fare["total_fare"],
                "total_minutes": res_bus_time["total_minutes"],
                "segments": [
                    {"type": "bus", "desc": f"搭乘 {bus_route} 路常規公車", "value": f"直達 {distance} km", "minutes": res_bus_time["details"][0]["estimated_minutes"], "fare": res_bus_fare["details"][0]["fare"]}
                ],
                "path": [
                    [start_sta['lat'], start_sta['lon']],
                    [end_sta['lat'], end_sta['lon']]
                ]
            },
            {
                "id": "plan_mrt", # 映射為全程步行方案，保持 ID 完整以相容地圖繪圖
                "name": "全程步行舒活方案",
                "description": "短途悠閒散步，享受中台灣陽光，免任何花費",
                "total_fare": res_walk_fare["total_fare"],
                "total_minutes": res_walk_time["total_minutes"],
                "segments": [
                    {"type": "walking", "desc": "沿著步行街道直行", "value": f"直達 {distance} km", "minutes": res_walk_time["details"][0]["estimated_minutes"], "fare": res_walk_fare["details"][0]["fare"]}
                ],
                "path": [
                    [start_sta['lat'], start_sta['lon']],
                    [end_sta['lat'], end_sta['lon']]
                ]
            }
        ]
        
    # 情況 B：長途移動且有捷運連結
    elif has_mrt_access and distance >= 2.0:
        seg1 = [
            {"type": "walking", "distance_km": 0.3},
            {"type": "mrt", "start_station": "MRT_08", "end_station": "MRT_09"},
            {"type": "bus", "route_id": bus_route, "distance_km": round(distance * 0.7, 2)}
        ]
        res1_fare = calculate_total_fare(seg1)
        res1_time = get_estimated_time(seg1)
        
        seg2 = [
            {"type": "bus", "route_id": bus_route, "distance_km": distance}
        ]
        res2_fare = calculate_total_fare(seg2)
        res2_time = get_estimated_time(seg2)
        
        seg3 = [
            {"type": "youbike", "minutes": min(50, int(distance * 5)), "distance_km": distance * 0.9},
            {"type": "walking", "distance_km": 0.3}
        ]
        res3_fare = calculate_total_fare(seg3)
        res3_time = get_estimated_time(seg3)
        
        plans = [
            {
                "id": "plan_mrt",
                "name": "捷運優先方案",
                "description": "速度快，路況穩定不受塞車影響",
                "total_fare": res1_fare["total_fare"],
                "total_minutes": res1_time["total_minutes"],
                "segments": [
                    {"type": "walking", "desc": "步行至捷運站", "value": "0.3 km", "minutes": res1_time["details"][0]["estimated_minutes"], "fare": res1_fare["details"][0]["fare"]},
                    {"type": "mrt", "desc": "搭乘捷運綠線", "value": "市政府站 ➔ 水安宮站", "minutes": res1_time["details"][1]["estimated_minutes"], "fare": res1_fare["details"][1]["fare"]},
                    {"type": "bus", "desc": f"轉乘 {bus_route} 路接駁公車", "value": f"{round(distance * 0.7, 1)} km", "minutes": res1_time["details"][2]["estimated_minutes"], "fare": res1_fare["details"][2]["fare"]}
                ],
                "path": [
                    [start_sta['lat'], start_sta['lon']],
                    [start_sta['lat'] + (end_sta['lat'] - start_sta['lat'])*0.1, start_sta['lon'] + (end_sta['lon'] - start_sta['lon'])*0.1],
                    [start_sta['lat'] + (end_sta['lat'] - start_sta['lat'])*0.8, start_sta['lon'] + (end_sta['lon'] - start_sta['lon'])*0.8],
                    [end_sta['lat'], end_sta['lon']]
                ]
            },
            {
                "id": "plan_bus",
                "name": "公車雙十省錢方案",
                "description": "台中市民專屬雙十優惠，單趟票價上限 10 元",
                "total_fare": res2_fare["total_fare"],
                "total_minutes": res2_time["total_minutes"],
                "segments": [
                    {"type": "bus", "desc": f"搭乘 {bus_route} 路直達公車", "value": f"直達 {distance} km", "minutes": res2_time["details"][0]["estimated_minutes"], "fare": res2_fare["details"][0]["fare"]}
                ],
                "path": [
                    [start_sta['lat'], start_sta['lon']],
                    [end_sta['lat'], end_sta['lon']]
                ]
            },
            {
                "id": "plan_green",
                "name": "綠能環保 YouBike",
                "description": "綠色低碳，強身健體，短途移動最佳首選",
                "total_fare": res3_fare["total_fare"],
                "total_minutes": res3_time["total_minutes"],
                "segments": [
                    {"type": "youbike", "desc": "騎乘 YouBike 2.0", "value": f"{round(distance * 0.9, 1)} km", "minutes": res3_time["details"][0]["estimated_minutes"], "fare": res3_fare["details"][0]["fare"]},
                    {"type": "walking", "desc": "步行至目的地", "value": "0.3 km", "minutes": res3_time["details"][1]["estimated_minutes"], "fare": res3_fare["details"][1]["fare"]}
                ],
                "path": [
                    [start_sta['lat'], start_sta['lon']],
                    [end_sta['lat'] - (end_sta['lat'] - start_sta['lat'])*0.05, end_sta['lon'] - (end_sta['lon'] - start_sta['lon'])*0.05],
                    [end_sta['lat'], end_sta['lon']]
                ]
            }
        ]
        
    # 情況 C：長途移動但完全無捷運 (如：台中車站 ➔ 秋紅谷/科博館) ➔ 捷運優先改為「快捷幹線公車」！
    else:
        seg1 = [
            {"type": "walking", "distance_km": 0.2},
            {"type": "bus", "route_id": "300", "distance_km": round(distance * 0.9, 2)},
            {"type": "walking", "distance_km": 0.3}
        ]
        res1_fare = calculate_total_fare(seg1)
        res1_time = get_estimated_time(seg1)
        
        seg2 = [
            {"type": "bus", "route_id": bus_route, "distance_km": distance}
        ]
        res2_fare = calculate_total_fare(seg2)
        res2_time = get_estimated_time(seg2)
        
        seg3 = [
            {"type": "youbike", "minutes": min(60, int(distance * 6)), "distance_km": distance}
        ]
        res3_fare = calculate_total_fare(seg3)
        res3_time = get_estimated_time(seg3)
        
        plans = [
            {
                "id": "plan_mrt", # 映射為快捷公車，保持 ID 相容地圖繪圖
                "name": "台灣大道快捷幹線方案",
                "description": "走公車專用道，班次極密集且路況穩定不受塞車影響",
                "total_fare": res1_fare["total_fare"],
                "total_minutes": res1_time["total_minutes"],
                "segments": [
                    {"type": "walking", "desc": "步行至快捷專用道站牌", "value": "0.2 km", "minutes": res1_time["details"][0]["estimated_minutes"], "fare": res1_fare["details"][0]["fare"]},
                    {"type": "bus", "desc": "搭乘 300 路快捷雙節公車", "value": f"{round(distance * 0.9, 1)} km", "minutes": res1_time["details"][1]["estimated_minutes"], "fare": res1_fare["details"][1]["fare"]},
                    {"type": "walking", "desc": "步行至目的地", "value": "0.3 km", "minutes": res1_time["details"][2]["estimated_minutes"], "fare": res1_fare["details"][2]["fare"]}
                ],
                "path": [
                    [start_sta['lat'], start_sta['lon']],
                    [start_sta['lat'] + (end_sta['lat'] - start_sta['lat'])*0.05, start_sta['lon'] + (end_sta['lon'] - start_sta['lon'])*0.05],
                    [end_sta['lat'] - (end_sta['lat'] - start_sta['lat'])*0.05, end_sta['lon'] - (end_sta['lon'] - start_sta['lon'])*0.05],
                    [end_sta['lat'], end_sta['lon']]
                ]
            },
            {
                "id": "plan_bus",
                "name": "公車雙十省錢方案",
                "description": "台中市民專屬雙十優惠，單趟票價上限 10 元",
                "total_fare": res2_fare["total_fare"],
                "total_minutes": res2_time["total_minutes"],
                "segments": [
                    {"type": "bus", "desc": f"搭乘 {bus_route} 路常規公車", "value": f"直達 {distance} km", "minutes": res2_time["details"][0]["estimated_minutes"], "fare": res2_fare["details"][0]["fare"]}
                ],
                "path": [
                    [start_sta['lat'], start_sta['lon']],
                    [end_sta['lat'], end_sta['lon']]
                ]
            },
            {
                "id": "plan_green",
                "name": "綠能環保 YouBike",
                "description": "綠色低碳，強身健體，短途移動最佳首選",
                "total_fare": res3_fare["total_fare"],
                "total_minutes": res3_time["total_minutes"],
                "segments": [
                    {"type": "youbike", "desc": "騎乘 YouBike 2.0", "value": f"直達 {distance} km", "minutes": res3_time["details"][0]["estimated_minutes"], "fare": res3_fare["details"][0]["fare"]}
                ],
                "path": [
                    [start_sta['lat'], start_sta['lon']],
                    [end_sta['lat'], end_sta['lon']]
                ]
            }
        ]
        
    return jsonify({
        "status": "success",
        "start_station": start_sta,
        "end_station": end_sta,
        "plans": plans
    })

@main_bp.route('/favorites/add', methods=['POST'])
def add_favorite():
    # 接收 JSON 或 Form
    if request.is_json:
        data = request.get_json() or {}
        station_id = data.get("station_id")
    else:
        station_id = request.form.get("station_id")
        
    if not station_id:
        return jsonify({"status": "error", "message": "Missing station_id"}), 400
        
    db = get_db()
    cursor = db.cursor()
    # 檢查是否已存在
    cursor.execute("SELECT 1 FROM favorites WHERE station_id = ?", (station_id,))
    if cursor.fetchone():
        db.close()
        return jsonify({"status": "success", "message": "Already favorited"})
        
    try:
        cursor.execute("INSERT INTO favorites (station_id) VALUES (?)", (station_id,))
        db.commit()
        db.close()
        return jsonify({"status": "success", "message": "Added to favorites"})
    except Exception as e:
        db.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@main_bp.route('/favorites/delete/<station_id>', methods=['POST'])
def delete_favorite(station_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM favorites WHERE station_id = ?", (station_id,))
        db.commit()
        db.close()
        # 判斷是否為 AJAX 請求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({"status": "success", "message": "Deleted from favorites"})
        return redirect(url_for('main.favorites_page'))
    except Exception as e:
        db.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@main_bp.route('/api/favorites')
def api_get_favorites():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT station_id FROM favorites")
    rows = cursor.fetchall()
    favs = [row['station_id'] for row in rows]
    db.close()
    return jsonify({
        "status": "success",
        "data": favs
    })

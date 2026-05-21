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
    
    # 計算兩站直線距離 (Haversine km)
    distance = get_distance(start_sta['lat'], start_sta['lon'], end_sta['lat'], end_sta['lon'])
    # 如果起終點一樣
    if distance < 0.05:
        distance = 0.5
        
    # 生成 3 種替代方案
    # 方案 1：捷運優先 (MRT + Bus)
    seg1 = [
        {"type": "walking", "distance_km": 0.3},
        {"type": "mrt", "start_station": "MRT_01", "end_station": "MRT_02"},
        {"type": "bus", "route_id": "300", "distance_km": round(distance * 0.8, 2)}
    ]
    # 方案 2：公車雙十優惠 (Bus Only)
    seg2 = [
        {"type": "bus", "route_id": "300", "distance_km": distance}
    ]
    # 方案 3：綠色環保 (YouBike + Walking)
    seg3 = [
        {"type": "youbike", "minutes": int(distance * 6), "distance_km": distance},
        {"type": "walking", "distance_km": 0.2}
    ]
    
    # 演算費用與時間
    res1_fare = calculate_total_fare(seg1)
    res1_time = get_estimated_time(seg1)
    
    res2_fare = calculate_total_fare(seg2)
    res2_time = get_estimated_time(seg2)
    
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
                {"type": "walking", "desc": "步行至捷運站", "value": "0.3 km", "minutes": res1_time["details"][0]["estimated_minutes"]},
                {"type": "mrt", "desc": "搭乘捷運綠線", "value": "市政府站 ➔ 水安宮站", "minutes": res1_time["details"][1]["estimated_minutes"]},
                {"type": "bus", "desc": "轉乘 300 路公車", "value": f"{round(distance * 0.8, 1)} km", "minutes": res1_time["details"][2]["estimated_minutes"]}
            ],
            # 傳遞經緯度段落以便前端繪圖
            "path": [
                [start_sta['lat'], start_sta['lon']],
                [start_sta['lat'] + (end_sta['lat'] - start_sta['lat'])*0.1, start_sta['lon'] + (end_sta['lon'] - start_sta['lon'])*0.1], # 步行段
                [start_sta['lat'] + (end_sta['lat'] - start_sta['lat'])*0.8, start_sta['lon'] + (end_sta['lon'] - start_sta['lon'])*0.8], # 捷運段
                [end_sta['lat'], end_sta['lon']] # 公車段
            ]
        },
        {
            "id": "plan_bus",
            "name": "公車雙十省錢方案",
            "description": "台中市民專屬雙十優惠，單趟票價上限 10 元",
            "total_fare": res2_fare["total_fare"],
            "total_minutes": res2_time["total_minutes"],
            "segments": [
                {"type": "bus", "desc": "搭乘 300/301 路台灣大道公車", "value": f"直達 {distance} km", "minutes": res2_time["details"][0]["estimated_minutes"]}
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
                {"type": "youbike", "desc": "騎乘 YouBike 2.0", "value": f"{distance} km", "minutes": res3_time["details"][0]["estimated_minutes"]},
                {"type": "walking", "desc": "步行至目的地", "value": "0.2 km", "minutes": res3_time["details"][1]["estimated_minutes"]}
            ],
            "path": [
                [start_sta['lat'], start_sta['lon']],
                [end_sta['lat'] - (end_sta['lat'] - start_sta['lat'])*0.05, end_sta['lon'] - (end_sta['lon'] - start_sta['lon'])*0.05], # Youbike
                [end_sta['lat'], end_sta['lon']] # Walking
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

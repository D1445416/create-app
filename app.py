from flask import Flask
import sqlite3
import os

from app.routes.main import main_bp
from utils.pricing import calculate_total_fare
from utils.tdx_time import get_estimated_time

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['DATABASE'] = os.path.join(os.getcwd(), 'instance', 'database.db')
app.register_blueprint(main_bp)

def init_db():
    """Initialize and seed the SQLite database."""
    if not os.path.exists('instance'):
        os.makedirs('instance')
    db = sqlite3.connect(app.config['DATABASE'])
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        db.cursor().executescript(f.read())
    
    # Check if stations table is empty or has mock stations only
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM stations")
    count = cursor.fetchone()[0]
    db.close()
    
    if count < 50:
        print("Stations count is low. Attempting to seed real stations from TDX...")
        success = False
        try:
            from database.fetch_tdx_stations import fetch_and_seed_all
            success = fetch_and_seed_all()
        except Exception as e:
            print("Failed to run real stations seeding:", e)
            
        if not success:
            print("Falling back to local mock seeding...")
            db = sqlite3.connect(app.config['DATABASE'])
            cursor = db.cursor()
            seed_stations = [
                ('HUB_01', '市政府站轉乘樞紐', 24.1628, 120.6439, 'transfer'),
                ('HUB_02', '台中車站轉乘樞紐', 24.1373, 120.6856, 'transfer'),
                ('MRT_01', '市政府捷運站', 24.1628, 120.6439, 'mrt'),
                ('MRT_02', '水安宮捷運站', 24.1508, 120.6473, 'mrt'),
                ('MRT_03', '文心森林公園捷運站', 24.1437, 120.6444, 'mrt'),
                ('MRT_04', '豐樂公園捷運站', 24.1317, 120.6465, 'mrt'),
                ('BUS_01', '台中車站(台灣大道)', 24.1380, 120.6850, 'bus'),
                ('BUS_02', '科博館公車站', 24.1558, 120.6631, 'bus'),
                ('BUS_03', '秋紅谷公車站', 24.1663, 120.6375, 'bus'),
                ('BUS_04', '逢甲大學公車站', 24.1788, 120.6466, 'bus')
            ]
            cursor.executemany(
                "INSERT OR REPLACE INTO stations (station_id, station_name, lat, lon, transport_type) VALUES (?, ?, ?, ?, ?)",
                seed_stations
            )
            db.commit()
            db.close()

@app.route('/api/v1/calculate_trip', methods=['POST'])
def calculate_trip():
    """
    接收前端的行程規劃分段資訊，整合預估時間與計算總價格。
    
    預期 JSON 格式:
    {
        "segments": [
            {
                "type": "bus",
                "route_id": "300",
                "distance_km": 12.5,
                "start_stop": "A",
                "end_stop": "B"
            },
            {
                "type": "mrt",
                "start_station": "103",
                "end_station": "110"
            },
            {
                "type": "youbike",
                "minutes": 15,
                "distance_km": 2.5
            }
        ]
    }
    """
    data = request.get_json()
    
    if not data or 'segments' not in data:
        return jsonify({
            "status": "error",
            "message": "Invalid request. 'segments' list is required."
        }), 400
        
    segments = data['segments']
    
    try:
        # 計算各段交通工具的預估時間
        time_result = get_estimated_time(segments)
        
        # 計算各段交通工具的費率
        fare_result = calculate_total_fare(segments)
        
        # 將結果合併回傳給前端，加入詳細的分項明細
        response = {
            "status": "success",
            "data": {
                "summary": {
                    "total_minutes": time_result["total_minutes"],
                    "total_fare": fare_result["total_fare"]
                },
                "fare_breakdown": {
                    "bus_fare": fare_result["bus_fare"],
                    "mrt_fare": fare_result["mrt_fare"],
                    "youbike_fare": fare_result["youbike_fare"],
                    "transfer_discount": fare_result["total_discount"]
                },
                "time_breakdown": {
                    "total_ride_time": time_result["total_ride_time"],
                    "total_walk_time": time_result["total_walk_time"],
                    "total_wait_time": time_result["total_wait_time"]
                },
                "fare_details": fare_result["details"],
                "time_details": time_result["details"]
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        # 捕捉無法預期的系統錯誤
        return jsonify({
            "status": "error",
            "message": f"Internal Server Error: {str(e)}"
        }), 500

# Initialize DB if it doesn't exist yet (works for both python app.py and flask run)
if not os.path.exists(app.config['DATABASE']):
    init_db()

# Auto-initialize SQLite database if it doesn't exist
if not os.path.exists(app.config['DATABASE']):
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5000)

from flask import Flask, request, jsonify
from utils.pricing import calculate_total_fare
from utils.tdx_time import get_estimated_time

app = Flask(__name__)

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
        
        # 將結果合併回傳給前端
        response = {
            "status": "success",
            "data": {
                "total_minutes": time_result["total_minutes"],
                "total_fare": fare_result["total_fare"],
                "time_details": time_result["details"],
                "fare_details": fare_result["details"]
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

from flask import Blueprint, jsonify
from utils.tdx import TDXClient

main_bp = Blueprint('main', __name__)
tdx = TDXClient()

@main_bp.route('/api/station/<station_id>')
def get_station_info(station_id):
    # 實際邏輯會先查 DB 獲取站點位置，再查 TDX 獲取動態數據
    # 這裡回傳整合後的數據，滿足「併列呈現」的需求
    bus_data = tdx.get_bus_arrival(station_id)
    mrt_data = tdx.get_mrt_arrival(station_id)
    
    return jsonify({
        "status": "success",
        "data": {
            "bus": bus_data,
            "mrt": mrt_data
        }
    })

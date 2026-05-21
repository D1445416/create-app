import traceback
from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from app.models import Station, CrowdednessCache
from app.services import tdx_service

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """
    【首頁路由 - 站點與擁擠度列表】
    
    HTTP 方法: GET
    支援篩選參數:
    - `search` (str): 站點名稱模糊搜尋。
    - `type` (str): 運輸工具類型篩選 ('metro' 或 'bus')。
    - `level` (str): 擁擠度顏色篩選 ('green', 'orange', 'red')。
    """
    try:
        # 1. 取得所有站點基本資料與其擁擠度快取
        stations = Station.get_all_with_crowdedness()
        
        # 2. 自動重整過期的站點快取 (效期 60 秒)
        # 為了避免初次載入頁面過慢，僅對目前在列表中的站點，若快取失效則順便向 TDX 更新
        for station in stations:
            # 若從未更新過，或快取已失效
            if not station.last_updated or not CrowdednessCache.is_cache_valid(station.station_id, cache_duration_seconds=60):
                try:
                    # 向 TDX API 取得即時資料 (若金鑰未設則會自動返回仿真模擬數據)
                    realtime_data = tdx_service.get_realtime_crowdedness(
                        station.station_id, 
                        station.name, 
                        station.type
                    )
                    # 更新至 SQLite 資料庫快取
                    cache_item = CrowdednessCache.create_or_update(
                        station.station_id,
                        realtime_data["level"],
                        realtime_data["passenger_count"],
                        realtime_data["last_updated"]
                    )
                    # 動態更新目前顯示物件之快取值
                    station.level = cache_item.level
                    station.passenger_count = cache_item.passenger_count
                    station.last_updated = cache_item.last_updated
                except Exception as ex:
                    print(f"自動更新站點 {station.name} 快取失敗: {ex}")
                    # 降級處理：若更新失敗則沿用舊快取，不影響頁面載入

        # 3. 接收 Query 篩選參數
        search_query = request.args.get('search', '').strip()
        type_filter = request.args.get('type', '').strip()
        level_filter = request.args.get('level', '').strip()

        # 4. 在記憶體中進行篩選過濾 (亦可於 SQL 層處理，但在記憶體處理便於快取重新整理)
        filtered_stations = []
        for s in stations:
            # 搜尋過濾
            if search_query and search_query not in s.name:
                continue
            # 類型過濾
            if type_filter and s.type != type_filter:
                continue
            # 擁擠度過濾
            if level_filter and s.level != level_filter:
                continue
            filtered_stations.append(s)

        # 5. 渲染首頁並帶入篩選狀態以便表單維持原值 (提升 UX)
        return render_template(
            'index.html',
            stations=filtered_stations,
            search=search_query,
            type=type_filter,
            level=level_filter
        )
    except Exception as e:
        traceback.print_exc()
        flash("讀取大眾運輸資料庫時發生未知異常，請稍後再試。", "error")
        return render_template('index.html', stations=[], search='', type='', level='')


@views_bp.route('/station/<string:station_id>')
def station_detail(station_id):
    """
    【站點詳情頁路由】
    
    HTTP 方法: GET
    - 點擊特定站點後，進入本頁面顯示極致美學詳情、人潮指標與 Google Maps 導引。
    """
    try:
        # 1. 取得站點基本資料
        station = Station.get_by_id(station_id)
        if not station:
            # 站點不存在，導向 404
            abort(404)
            
        # 2. 驗證快取是否依然有效
        is_valid = CrowdednessCache.is_cache_valid(station_id, cache_duration_seconds=60)
        
        # 3. 若快取過期，強制重新向外部 TDX API 請求並更新
        if not is_valid:
            try:
                realtime_data = tdx_service.get_realtime_crowdedness(
                    station.station_id, 
                    station.name, 
                    station.type
                )
                CrowdednessCache.create_or_update(
                    station.station_id,
                    realtime_data["level"],
                    realtime_data["passenger_count"],
                    realtime_data["last_updated"]
                )
            except Exception as ex:
                print(f"詳情頁即時更新快取失敗: {ex}")
                flash("目前無法連線至交通部 TDX，為您呈現最後一次快取成功的歷史人潮資料。", "warning")

        # 4. 取得最新快取資訊
        cache = CrowdednessCache.get_by_station_id(station_id)
        
        return render_template(
            'detail.html',
            station=station,
            cache=cache
        )
    except Exception as e:
        if isinstance(e, abort) or (hasattr(e, 'code') and e.code == 404):
            raise e
        traceback.print_exc()
        flash("讀取站點詳細資訊時發生異常，請回首頁重試。", "error")
        return redirect(url_for('views.index'))


@views_bp.route('/api/stations/nearby', methods=['GET'])
def api_nearby_stations():
    """
    【API 路由 - GPS 定位周邊推薦站點】
    
    HTTP 方法: GET
    Query 參數 (必填): `lat` (緯度), `lng` (經度)
    Query 參數 (選填): `limit` (最大數量，預設 5)
    """
    lat_str = request.args.get('lat')
    lng_str = request.args.get('lng')
    limit_str = request.args.get('limit', '5')

    # 1. 必填校驗
    if not lat_str or not lng_str:
        return jsonify({"error": "缺少經度(lng)或緯度(lat)參數。"}), 400

    # 2. 格式轉換與校驗
    try:
        lat = float(lat_str)
        lng = float(lng_str)
        limit = int(limit_str)
    except ValueError:
        return jsonify({"error": "經緯度參數格式錯誤，必須為浮點數。"}), 400

    try:
        # 3. 呼叫周邊定位運算 Model
        nearby_stations = Station.get_nearby(lat, lng, limit=limit)
        
        # 4. 轉換為 JSON 格式
        results = []
        for s in nearby_stations:
            results.append({
                "station_id": s.station_id,
                "name": s.name,
                "type": s.type,
                "route_name": s.route_name,
                "lat": s.lat,
                "lng": s.lng,
                "level": s.level,
                "passenger_count": s.passenger_count,
                "last_updated": s.last_updated
            })
            
        return jsonify(results), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"後端空間定位推薦計算異常: {str(e)}"}), 500


@views_bp.route('/api/stations/refresh', methods=['POST'])
def api_refresh_cache():
    """
    【API 路由 - 強制更新擁擠度快取】
    
    HTTP 方法: POST
    JSON 參數 (選填): `station_id`
    """
    try:
        req_data = request.get_json(silent=True) or {}
        station_id = req_data.get('station_id')

        if station_id:
            # A. 僅更新單一指定站點
            station = Station.get_by_id(station_id)
            if not station:
                return jsonify({"error": f"找不到指定代碼 '{station_id}' 的站點。"}), 404
                
            realtime_data = tdx_service.get_realtime_crowdedness(
                station.station_id, 
                station.name, 
                station.type
            )
            cache_item = CrowdednessCache.create_or_update(
                station.station_id,
                realtime_data["level"],
                realtime_data["passenger_count"],
                realtime_data["last_updated"]
            )
            return jsonify({
                "success": True,
                "updated_count": 1,
                "station": {
                    "station_id": cache_item.station_id,
                    "level": cache_item.level,
                    "passenger_count": cache_item.passenger_count,
                    "last_updated": cache_item.last_updated
                }
            }), 200
        else:
            # B. 更新資料庫中的所有站點快取
            stations = Station.get_all()
            updated_count = 0
            for s in stations:
                try:
                    realtime_data = tdx_service.get_realtime_crowdedness(s.station_id, s.name, s.type)
                    CrowdednessCache.create_or_update(
                        s.station_id,
                        realtime_data["level"],
                        realtime_data["passenger_count"],
                        realtime_data["last_updated"]
                    )
                    updated_count += 1
                except Exception as ex:
                    print(f"批量刷新站點 {s.name} 快取失敗: {ex}")
                    
            return jsonify({
                "success": True,
                "updated_count": updated_count
            }), 200
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"強制刷新快取失敗: {str(e)}"}), 500

# 自訂 404 錯誤處理渲染
@views_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

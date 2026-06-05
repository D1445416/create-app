from flask import Blueprint, render_template, session, request, jsonify, flash, redirect, url_for
from app.models import RouteHistoryModel, Station, CrowdednessCache, Favorite
from app.services import tdx_service
from app.services.route_calculator import LANDMARKS

# 建立主頁面 Blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    首頁路由看板。
    GET:
        - 檢查當前登入狀態 (session['user_id'])。
        - 撈取該使用者的歷史路線與收藏常用路線。
        - 撈取大眾運輸站點資訊，並進行人潮擁擠度更新與篩選。
        - 渲染並返回 'index.html'。
    """
    user_id = session.get('user_id')
    favorite_list = []
    history_list = []

    # 1. 撈取使用者的收藏常用路線與搜尋歷史紀錄
    if user_id:
        try:
            favorite_list = RouteHistoryModel.get_by_user_id(user_id, only_favorites=True)
            history_list = RouteHistoryModel.get_by_user_id(user_id, only_favorites=False)
        except Exception as e:
            print(f"Error fetching history or favorites: {str(e)}")

    # 2. 取得大眾運輸站點資訊與即時擁擠度 (F-07 / F-02)
    stations_list = []
    try:
        stations_list = Station.get_all_with_crowdedness()
        # 自動重整過期的站點快取 (效期 60 秒)
        for station in stations_list:
            if not station.last_updated or not CrowdednessCache.is_cache_valid(station.station_id, cache_duration_seconds=60):
                try:
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
                    station.level = cache_item.level
                    station.passenger_count = cache_item.passenger_count
                    station.last_updated = cache_item.last_updated
                except Exception as ex:
                    print(f"自動更新站點 {station.name} 快取失敗: {ex}")
    except Exception as e:
        print(f"Error loading stations: {e}")

    # 3. 接收 Query 篩選參數
    search_query = request.args.get('search', '').strip()
    type_filter = request.args.get('type', '').strip()
    level_filter = request.args.get('level', '').strip()

    # 4. 在記憶體中進行篩選過濾
    filtered_stations = []
    for s in stations_list:
        if search_query and search_query not in s.name:
            continue
        if type_filter and s.type != type_filter:
            continue
        if level_filter and s.level != level_filter:
            continue
        filtered_stations.append(s)

    # 5. 排序地標清單
    landmark_list = sorted(list(LANDMARKS.keys()))

    return render_template(
        'index.html',
        favorite_list=favorite_list,
        history_list=history_list,
        stations=filtered_stations,
        search=search_query,
        type=type_filter,
        level=level_filter,
        landmarks=landmark_list
    )

@main_bp.route('/map')
def transit_map():
    """
    大眾運輸檢視圖（地圖）路由。
    GET:
        - 接收選填的起點經緯度參數 (lat, lng)。
        - 渲染並返回 'map.html'。
    """
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    return render_template('map.html', lat=lat, lng=lng)

# --- 常用最愛站點管理 (F-05) ---

@main_bp.route('/favorites')
def show_favorites():
    """
    獲取使用者收藏的所有站點列表。
    """
    try:
        fav_list = Favorite.get_all()
        return render_template('favorites.html', favorites=fav_list)
    except Exception as e:
        print(f"Error fetching favorites: {e}")
        return render_template('favorites.html', favorites=[])

@main_bp.route('/favorites/add/<string:station_id>', methods=['POST'])
def add_station_favorite(station_id):
    """
    將某個站點加入收藏列表。
    """
    try:
        # 檢查該站點是否存在於 stations 表中
        station = Station.get_by_id(station_id)
        if not station:
            return jsonify({'status': 'error', 'message': '找不到該指定站點'}), 404
        
        # 建立收藏
        fav_id = Favorite.create(station_id)
        if fav_id:
            return jsonify({'status': 'success', 'message': '站點收藏成功'}), 200
        else:
            return jsonify({'status': 'error', 'message': '該站點已被收藏'}), 400
    except Exception as e:
        print(f"Error adding favorite: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/favorites/delete/<string:station_id>', methods=['POST'])
def delete_station_favorite(station_id):
    """
    將某個站點移出收藏列表。
    """
    try:
        success = Favorite.delete_by_station_id(station_id)
        if success:
            return jsonify({'status': 'success', 'message': '已成功取消收藏'}), 200
        else:
            return jsonify({'status': 'error', 'message': '取消收藏失敗，或該站點本就未收藏'}), 400
    except Exception as e:
        print(f"Error deleting favorite: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

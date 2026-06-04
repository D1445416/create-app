from flask import Blueprint, render_template, session, request
from app.models.route_history import RouteHistoryModel

# 建立主頁面 Blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    首頁路由。
    GET:
        - 檢查當前登入狀態 (session['user_id'])。
        - 若已登入，撈取該使用者的歷史路線與收藏常用路線。
        - 渲染並返回 'index.html'。
    """
    user_id = session.get('user_id')
    favorite_list = []
    history_list = []

    if user_id:
        try:
            # 撈取該使用者的收藏常用路線 (is_favorite = 1)
            favorite_list = RouteHistoryModel.get_by_user_id(user_id, only_favorites=True)
            # 撈取該使用者的所有搜尋歷史紀錄
            history_list = RouteHistoryModel.get_by_user_id(user_id, only_favorites=False)
        except Exception as e:
            # 即使資料庫讀取失敗也優雅處理，不直接崩潰
            print(f"Error fetching history or favorites: {str(e)}")

    return render_template(
        'index.html',
        favorite_list=favorite_list,
        history_list=history_list
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

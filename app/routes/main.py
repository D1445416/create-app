from flask import Blueprint

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
    pass

@main_bp.route('/map')
def transit_map():
    """
    大眾運輸檢視圖（地圖）路由。
    GET:
        - 接收選填的起點經緯度參數 (lat, lng)。
        - 渲染並返回 'map.html'。
    """
    pass

from flask import Blueprint

# 建立交通與歷史紀錄 Blueprint
transit_bp = Blueprint('transit', __name__, url_prefix='/transit')

@transit_bp.route('/search', methods=['POST'])
def search_route():
    """
    執行路線規劃搜尋。
    POST:
        - 接收表單起點與終點 (start_point, end_point)。
        - 呼叫外部 TDX 交通 API 計算轉乘規劃、車資、替代路線。
        - 若使用者已登入，將搜尋紀錄寫入 DB (route_history 表)。
        - 將計算結果存入 session['search_result']。
        - 302 重導向至 '/transit/result'。
    """
    pass

@transit_bp.route('/result')
def show_result():
    """
    顯示路線規劃結果頁面。
    GET:
        - 自 session 中讀取 'search_result'。
        - 渲染並返回 'result.html'。
    """
    pass

@transit_bp.route('/arrival')
def show_arrival():
    """
    即時到站預估查詢路由。
    GET:
        - 接收查詢參數 (route_name)。
        - 呼叫外部 TDX API 查詢該路線或該站牌即時到站預估時間。
        - 渲染並返回 'arrival.html'。
    """
    pass

@transit_bp.route('/history/add', methods=['POST'])
def add_favorite():
    """
    將特定路線紀錄標記為「常用/最愛」。
    POST:
        - 接收要加入最愛的起點、終點與詳細路線資料。
        - 調用 RouteHistoryModel 將其寫入或更新為 is_favorite = 1。
        - 使用 flash 提示新增成功。
        - 302 重導向回首頁 '/'。
    """
    pass

@transit_bp.route('/history/delete/<int:history_id>', methods=['POST'])
def delete_history(history_id):
    """
    刪除特定的歷史紀錄或常用最愛路線。
    POST:
        - 調用 RouteHistoryModel.delete(history_id)。
        - 302 重導向回首頁 '/'。
    """
    pass

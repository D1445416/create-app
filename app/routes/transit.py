from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from app.models.route_history import RouteHistoryModel
import json

# 建立交通與歷史紀錄 Blueprint
transit_bp = Blueprint('transit', __name__, url_prefix='/transit')

@transit_bp.route('/search', methods=['POST'])
def search_route():
    """
    執行路線規劃搜尋。
    POST:
        - 接收表單起點與終點 (start_point, end_point)。
        - 呼叫/模擬外部 TDX 交通 API 計算轉乘規劃、車資、替代路線。
        - 若使用者已登入，將搜尋紀錄寫入 DB (route_history 表)。
        - 將計算結果存入 session['search_result']。
        - 302 重導向至 '/transit/result'。
    """
    start_point = request.form.get('start_point', '').strip()
    end_point = request.form.get('end_point', '').strip()

    if not start_point or not end_point:
        flash('起點與終點為必填欄位！', 'danger')
        return redirect(url_for('main.index'))

    # 模擬外部交通規劃 API 的回傳資料
    mock_details = [
        {
            "option_name": "路線方案 A：捷運主導",
            "total_time": 25,
            "cost": 35,
            "segments": [
                {"type": "walking", "text": "步行 3 分鐘前往捷運市政府站"},
                {"type": "mrt", "text": "搭乘捷運綠線至文心森林公園站 (3站)"},
                {"type": "walking", "text": "步行 4 分鐘抵達終點"}
            ]
        },
        {
            "option_name": "路線方案 B：快捷公車",
            "total_time": 32,
            "cost": 20,
            "segments": [
                {"type": "walking", "text": "步行 2 分鐘前往市政府專用道公車站"},
                {"type": "bus", "text": "搭乘 300 號快捷公車至台中車站 (5站)"},
                {"type": "walking", "text": "步行 3 分鐘抵達終點"}
            ]
        }
    ]

    # 將搜尋結果寫入 session
    search_data = {
        'start_point': start_point,
        'end_point': end_point,
        'details': mock_details
    }
    session['search_result'] = search_data

    # 若使用者已登入，記錄此次搜尋歷史
    user_id = session.get('user_id')
    if user_id:
        try:
            # 建立一筆搜尋紀錄 (is_favorite = 0)
            RouteHistoryModel.create(
                user_id=user_id,
                start_point=start_point,
                end_point=end_point,
                details=mock_details,
                is_favorite=0
            )
        except Exception as e:
            # 記錄錯誤但不阻礙使用者搜尋體驗
            print(f"Error saving search history to database: {str(e)}")

    return redirect(url_for('transit.show_result'))

@transit_bp.route('/result')
def show_result():
    """
    顯示路線規劃結果頁面。
    GET:
        - 自 session 中讀取 'search_result'。
        - 渲染並返回 'result.html'。
    """
    search_result = session.get('search_result')
    if not search_result:
        flash('請先輸入起訖點以進行路線搜尋規劃。', 'warning')
        return redirect(url_for('main.index'))
        
    return render_template('result.html', search_result=search_result)

@transit_bp.route('/arrival')
def show_arrival():
    """
    即時到站預估查詢路由。
    GET:
        - 接收查詢參數 (route_name)。
        - 呼叫外部 TDX API 查詢該路線或該站牌即時到站預估時間。
        - 渲染並返回 'arrival.html'。
    """
    route_name = request.args.get('route_name', '').strip()
    return render_template('arrival.html', route_name=route_name)

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
    user_id = session.get('user_id')
    if not user_id:
        flash('請先登入帳號以使用收藏路線功能。', 'warning')
        return redirect(url_for('auth.login'))

    start_point = request.form.get('start_point', '').strip()
    end_point = request.form.get('end_point', '').strip()
    details_str = request.form.get('details', 'None')

    if not start_point or not end_point:
        flash('無法加入收藏：起點與終點不可為空！', 'danger')
        return redirect(url_for('main.index'))

    # 解析 details
    details = None
    if details_str and details_str != 'None':
        try:
            # 替換單引號為雙引號以便符合 JSON 標準
            valid_json_str = details_str.replace("'", '"')
            details = json.loads(valid_json_str)
        except Exception:
            details = None

    try:
        # 新增常用最愛 (is_favorite = 1)
        RouteHistoryModel.create(
            user_id=user_id,
            start_point=start_point,
            end_point=end_point,
            details=details,
            is_favorite=1
        )
        flash('已成功將此路線加入您的常用路線！', 'success')
    except Exception as e:
        flash(f'加入常用路線失敗：{str(e)}', 'danger')

    return redirect(url_for('main.index'))

@transit_bp.route('/history/delete/<int:history_id>', methods=['POST'])
def delete_history(history_id):
    """
    刪除特定的歷史紀錄或常用最愛路線。
    POST:
        - 調用 RouteHistoryModel.delete(history_id)。
        - 302 重導向回首頁 '/'。
    """
    user_id = session.get('user_id')
    if not user_id:
        flash('請先登入帳號。', 'warning')
        return redirect(url_for('auth.login'))

    try:
        # 獲取紀錄以進行安全檢查
        history = RouteHistoryModel.get_by_id(history_id)
        if history and history['user_id'] == user_id:
            RouteHistoryModel.delete(history_id)
            flash('紀錄已成功刪除。', 'success')
        else:
            flash('無此權限或紀錄不存在。', 'danger')
    except Exception as e:
        flash(f'刪除歷史紀錄時發生錯誤：{str(e)}', 'danger')

    return redirect(url_for('main.index'))

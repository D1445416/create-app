from flask import Blueprint, render_template, request
from app.services.route_calculator import calculate_best_route, LANDMARKS

f03_bp = Blueprint('f03', __name__)

@f03_bp.route('/planner', methods=['GET', 'POST'])
def route_planner():
    route_result = None
    error = None
    
    # 將地標清單依筆劃/英文字母排序
    landmark_list = sorted(list(LANDMARKS.keys()))

    if request.method == 'POST':
        start_point = request.form.get('start_point')
        end_point = request.form.get('end_point')
        preferences = request.form.getlist('preferences') # e.g. ['mrt', 'bus', 'youbike', 'train']

        if not start_point or not end_point:
            error = '請選擇起點與終點'
        elif start_point == end_point:
            error = '起點與終點不能相同'
        else:
            # 進行最佳路徑規劃
            route_result = calculate_best_route(start_point, end_point, preferences)
            if not route_result:
                error = '無法在目前偏好下找到合適路線，請嘗試勾選更多交通工具或步行。'

    return render_template(
        'f03/route_planner.html', 
        route_result=route_result, 
        error=error, 
        landmarks=landmark_list
    )

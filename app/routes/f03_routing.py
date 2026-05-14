from flask import Blueprint, render_template, request
from app.services.route_calculator import calculate_best_route

f03_bp = Blueprint('f03', __name__)

@f03_bp.route('/planner', methods=['GET', 'POST'])
def route_planner():
    route_result = None
    error = None

    if request.method == 'POST':
        start_point = request.form.get('start_point')
        end_point = request.form.get('end_point')
        preferences = request.form.getlist('preferences') # e.g. ['mrt', 'bus', 'youbike', 'train']

        if not start_point or not end_point:
            error = '請輸入起點與終點'
        else:
            # 呼叫路徑計算服務 (Mock)
            route_result = calculate_best_route(start_point, end_point, preferences)

    return render_template('f03/route_planner.html', route_result=route_result, error=error)

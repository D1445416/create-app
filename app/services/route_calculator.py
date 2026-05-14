import random

def calculate_best_route(start_point, end_point, preferences):
    """
    Mock 的路徑規劃演算法。
    根據起訖點與偏好的交通工具，回傳模擬的路徑規劃結果與 ETA。
    """
    
    # 簡單模擬不同運具的組合
    available_modes = preferences if preferences else ['mrt', 'bus', 'youbike', 'train']
    
    mode_names = {
        'mrt': '捷運',
        'bus': '公車',
        'youbike': 'YouBike',
        'train': '火車'
    }
    
    # 隨機產生 1 到 3 個轉乘步驟
    num_steps = random.randint(1, 3)
    steps = []
    total_time = 0
    total_cost = 0
    
    current_location = start_point
    
    for i in range(num_steps):
        mode = random.choice(available_modes)
        mode_str = mode_names.get(mode, '步行')
        
        step_time = random.randint(5, 25) # 分鐘
        step_cost = random.randint(0, 30) if mode != 'youbike' else random.randint(0, 10)
        
        next_location = end_point if i == num_steps - 1 else f"轉乘站 {chr(65 + random.randint(0, 5))}"
        
        steps.append({
            'mode': mode_str,
            'from': current_location,
            'to': next_location,
            'duration': step_time,
            'cost': step_cost,
            'instruction': f"搭乘 {mode_str} 從 {current_location} 到 {next_location}"
        })
        
        total_time += step_time
        total_cost += step_cost
        current_location = next_location

    return {
        'start': start_point,
        'end': end_point,
        'total_time': total_time,
        'total_cost': total_cost,
        'steps': steps,
        'eta': f"約 {total_time} 分鐘後抵達"
    }

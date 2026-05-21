import heapq

# 台中地標與座標資訊
LANDMARKS = {
    '台中車站': {'name': '台中車站', 'lat': 24.1373, 'lng': 120.6868},
    '市政府捷運站': {'name': '市政府捷運站', 'lat': 24.1629, 'lng': 120.6438},
    '逢甲大學': {'name': '逢甲大學', 'lat': 24.1798, 'lng': 120.6450},
    '一中商圈': {'name': '一中商圈', 'lat': 24.1487, 'lng': 120.6853},
    '東海大學': {'name': '東海大學', 'lat': 24.1802, 'lng': 120.6013},
    '高鐵台中站': {'name': '高鐵台中站', 'lat': 24.1121, 'lng': 120.6162},
    '國家歌劇院': {'name': '國家歌劇院', 'lat': 24.1627, 'lng': 120.6404},
    '勤美誠品綠園道': {'name': '勤美誠品綠園道', 'lat': 24.1513, 'lng': 120.6638},
    '秋紅谷': {'name': '秋紅谷', 'lat': 24.1674, 'lng': 120.6397},
}

# 交通路線邊（包含運具、時間（分鐘）、費用（元）、導引描述）
EDGES = [
    # 台中車站 <-> 一中商圈
    ('台中車站', '一中商圈', 'bus', 10, 15, '搭乘公車 300 路'),
    ('台中車站', '一中商圈', 'youbike', 15, 5, '騎乘 YouBike 沿雙十路'),
    ('台中車站', '一中商圈', 'walk', 25, 0, '沿雙十路步行'),

    # 台中車站 <-> 勤美誠品綠園道
    ('台中車站', '勤美誠品綠園道', 'bus', 12, 15, '搭乘公車 304 路'),
    ('台中車站', '勤美誠品綠園道', 'youbike', 18, 5, '騎乘 YouBike 經民權路'),
    
    # 一中商圈 <-> 勤美誠品綠園道
    ('一中商圈', '勤美誠品綠園道', 'bus', 10, 15, '搭乘公車 81 路'),
    ('一中商圈', '勤美誠品綠園道', 'youbike', 12, 5, '騎乘 YouBike 經英才路'),
    ('一中商圈', '勤美誠品綠園道', 'walk', 22, 0, '步行經健行路'),

    # 勤美誠品綠園道 <-> 市政府捷運站
    ('勤美誠品綠園道', '市政府捷運站', 'bus', 8, 15, '搭乘公車 300 路'),
    ('勤美誠品綠園道', '市政府捷運站', 'youbike', 10, 5, '騎乘 YouBike'),
    ('勤美誠品綠園道', '市政府捷運站', 'walk', 20, 0, '沿台灣大道步行'),

    # 台中車站 <-> 市政府捷運站
    ('台中車站', '市政府捷運站', 'train', 12, 15, '搭乘台鐵區間車至大慶車站並轉乘捷運'),
    ('台中車站', '市政府捷運站', 'bus', 20, 20, '搭乘台灣大道幹線公車 300 路'),

    # 市政府捷運站 <-> 國家歌劇院
    ('市政府捷運站', '國家歌劇院', 'walk', 8, 0, '沿市政北七路步行'),
    ('市政府捷運站', '國家歌劇院', 'youbike', 4, 5, '騎乘 YouBike'),

    # 國家歌劇院 <-> 秋紅谷
    ('國家歌劇院', '秋紅谷', 'walk', 6, 0, '沿惠來路步行'),
    ('國家歌劇院', '秋紅谷', 'youbike', 3, 5, '騎乘 YouBike'),

    # 國家歌劇院 <-> 逢甲大學
    ('國家歌劇院', '逢甲大學', 'bus', 10, 15, '搭乘公車 5 路'),
    ('國家歌劇院', '逢甲大學', 'youbike', 12, 5, '騎乘 YouBike 沿河南路'),

    # 秋紅谷 <-> 逢甲大學
    ('秋紅谷', '逢甲大學', 'bus', 8, 15, '搭乘公車 63 路'),
    ('秋紅谷', '逢甲大學', 'youbike', 10, 5, '騎乘 YouBike'),
    ('秋紅谷', '逢甲大學', 'walk', 20, 0, '步行經河南路'),

    # 市政府捷運站 <-> 高鐵台中站
    ('市政府捷運站', '高鐵台中站', 'mrt', 12, 30, '搭乘捷運綠線'),
    ('市政府捷運站', '高鐵台中站', 'bus', 25, 20, '搭乘公車 151 路'),

    # 台中車站 <-> 高鐵台中站
    ('台中車站', '高鐵台中站', 'train', 10, 15, '搭乘台鐵區間車至新烏日車站'),
    ('台中車站', '高鐵台中站', 'bus', 30, 20, '搭乘公車 82 路'),

    # 東海大學 <-> 秋紅谷
    ('東海大學', '秋紅谷', 'bus', 10, 15, '搭乘公車 300 路'),
    ('東海大學', '秋紅谷', 'youbike', 20, 10, '騎乘 YouBike 經台灣大道'),

    # 東海大學 <-> 逢甲大學
    ('東海大學', '逢甲大學', 'bus', 15, 15, '搭乘公車 354 路'),
    ('東海大學', '逢甲大學', 'youbike', 25, 10, '騎乘 YouBike 經福科路')
]

def calculate_best_route(start_point, end_point, preferences):
    """
    使用 Dijkstra 演算法計算最短時間路徑，只使用 preferences 勾選的交通工具（步行 walk 預設恆准許）。
    """
    if start_point not in LANDMARKS or end_point not in LANDMARKS:
        return None

    # walk 預設永遠允許
    allowed_modes = set(preferences) if preferences else {'mrt', 'bus', 'youbike', 'train'}
    allowed_modes.add('walk')

    # 建立鄰接清單
    graph = {node: [] for node in LANDMARKS}
    for u, v, mode, duration, cost, label in EDGES:
        if mode in allowed_modes:
            graph[u].append((v, mode, duration, cost, label))
            graph[v].append((u, mode, duration, cost, label))

    # Dijkstra 搜尋：優先佇列儲存 (累計時間, 當前站點, 路徑步驟, 累計花費)
    # heap 項目格式: (total_time, current_node, path, total_cost)
    # path 為 step 列表，每個 step 格式: (next_node, mode, duration, cost, label)
    pq = [(0, start_point, [], 0)]
    visited = {}

    while pq:
        time, curr, path, total_c = heapq.heappop(pq)

        if curr == end_point:
            # 找到最佳路徑，格式化輸出
            formatted_steps = []
            current_loc = start_point
            
            mode_names = {
                'mrt': '捷運',
                'bus': '公車',
                'youbike': 'YouBike',
                'train': '火車',
                'walk': '步行'
            }

            for next_loc, mode, duration, cost, label in path:
                formatted_steps.append({
                    'mode': mode,
                    'mode_name': mode_names.get(mode, '步行'),
                    'from': current_loc,
                    'to': next_loc,
                    'duration': duration,
                    'cost': cost,
                    'instruction': f"{label}，從 {current_loc} 到 {next_loc}"
                })
                current_loc = next_loc

            # 產生路線經緯度坐標
            route_coords = [
                {'name': start_point, 'lat': LANDMARKS[start_point]['lat'], 'lng': LANDMARKS[start_point]['lng']}
            ]
            for s in formatted_steps:
                to_node = s['to']
                route_coords.append({
                    'name': to_node,
                    'lat': LANDMARKS[to_node]['lat'],
                    'lng': LANDMARKS[to_node]['lng']
                })

            return {
                'start': start_point,
                'end': end_point,
                'total_time': time,
                'total_cost': total_c,
                'steps': formatted_steps,
                'route_coords': route_coords,
                'eta': f"約 {time} 分鐘後抵達"
            }

        if curr in visited and visited[curr] <= time:
            continue
        visited[curr] = time

        for neighbor, mode, duration, cost, label in graph.get(curr, []):
            if neighbor not in visited or visited[neighbor] > time + duration:
                new_path = list(path)
                new_path.append((neighbor, mode, duration, cost, label))
                heapq.heappush(pq, (time + duration, neighbor, new_path, total_c + cost))

    return None

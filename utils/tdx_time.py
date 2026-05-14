import random

def get_estimated_time(segments: list) -> dict:
    """
    獲取各交通路段的預估時間 (整合 TDX API)。
    
    由於 F-02 模組尚未完全整合，這裡暫時提供 Mock 實作。
    未來應改寫為向 TDX API 或是 F-02 模組請求即時動態資料。
    
    segments 格式範例：
    [
        {"type": "bus", "route_id": "300", "start_stop": "A", "end_stop": "B"},
        {"type": "mrt", "start_station": "103", "end_station": "110"},
        {"type": "youbike", "distance_km": 2.5}
    ]
    """
    total_minutes = 0
    details = []

    for seg in segments:
        est_time = 0
        seg_type = seg.get("type")
        
        if seg_type == "bus":
            # Mock: 公車搭乘時間隨機估算 10~30 分鐘，或依據實際 API
            est_time = random.randint(10, 30)
        elif seg_type == "mrt":
            # Mock: 捷運搭乘時間，每站約 2.5 分鐘
            try:
                start_idx = int(''.join(filter(str.isdigit, seg.get("start_station", "0"))))
                end_idx = int(''.join(filter(str.isdigit, seg.get("end_station", "0"))))
                diff = abs(start_idx - end_idx)
                est_time = diff * 2.5 + 2 # +2 分鐘等車
            except Exception:
                est_time = 15
        elif seg_type == "youbike":
            # Mock: Youbike 騎乘時間，假設時速 10 公里 (每公里 6 分鐘)
            distance = seg.get("distance_km", 0)
            est_time = distance * 6
        elif seg_type == "walking":
            # Mock: 走路時間，假設時速 4 公里 (每公里 15 分鐘)
            distance = seg.get("distance_km", 0)
            est_time = distance * 15
            
        est_time = int(est_time)
        total_minutes += est_time
        
        details.append({
            "type": seg_type,
            "estimated_minutes": est_time
        })
        
    return {
        "total_minutes": total_minutes,
        "details": details
    }

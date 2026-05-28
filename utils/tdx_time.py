import random

# 常數設定
WALKING_BUFFER_MINS = 3
WAITING_BUFFER_MINS = 5
DEFAULT_MINUTES_PER_KM = 3

def get_estimated_time(segments: list) -> dict:
    """
    獲取各交通路段的預估時間，並加入轉乘步行與等車的緩衝時間。
    """
    total_ride_time = 0
    total_walk_time = 0
    total_wait_time = 0
    details = []
    
    prev_type = None

    for i, seg in enumerate(segments):
        est_ride_time = 0
        seg_type = seg.get("type", "unknown")
        
        # 1. 計算該路段搭乘時間
        try:
            if seg_type == "bus":
                # Mock: 公車搭乘時間隨機估算 10~30 分鐘，或依據距離估算
                distance = seg.get("distance_km", 5)
                est_ride_time = max(5, int(distance * 4))
            elif seg_type == "mrt":
                # Mock: 捷運每站約 2.5 分鐘
                start_idx = int(''.join(filter(str.isdigit, seg.get("start_station", "0"))))
                end_idx = int(''.join(filter(str.isdigit, seg.get("end_station", "0"))))
                diff = abs(start_idx - end_idx)
                est_ride_time = max(2, diff * 3)
            elif seg_type == "youbike":
                distance = seg.get("distance_km", 2)
                est_ride_time = int(distance * 6) # 時速 10 公里
            elif seg_type == "walking":
                distance = seg.get("distance_km", 1)
                est_ride_time = int(distance * 15) # 時速 4 公里
            else:
                est_ride_time = 10
        except Exception:
            # 防呆機制：若計算失敗，套用預設時間
            distance = seg.get("distance_km", 5)
            est_ride_time = int(distance * DEFAULT_MINUTES_PER_KM)

        # 2. 計算轉乘緩衝時間
        walk_buffer = 0
        wait_buffer = 0
        
        # 只要不是第一段，且不是連續步行的情況下，加入轉乘時間
        if i > 0 and seg_type != "walking":
            walk_buffer = WALKING_BUFFER_MINS
            # 如果是需要等車的運具 (公車、捷運)，加入等車時間
            if seg_type in ["bus", "mrt"]:
                wait_buffer = WAITING_BUFFER_MINS
                
        # 3. 累加時間
        total_ride_time += est_ride_time
        total_walk_time += walk_buffer
        if seg_type == "walking":
            # 如果這一段本身就是步行，計入步行時間總和
            total_walk_time += est_ride_time
            total_ride_time -= est_ride_time
            
        total_wait_time += wait_buffer
        
        details.append({
            "type": seg_type,
            "ride_time": est_ride_time,
            "transfer_walk_buffer": walk_buffer,
            "transfer_wait_buffer": wait_buffer,
            "segment_total_time": est_ride_time + walk_buffer + wait_buffer
        })
        
        prev_type = seg_type
        
    return {
        "total_ride_time": total_ride_time,
        "total_walk_time": total_walk_time,
        "total_wait_time": total_wait_time,
        "total_minutes": total_ride_time + total_walk_time + total_wait_time,
        "details": details
    }

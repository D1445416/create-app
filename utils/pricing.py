import math

def calculate_bus_fare(distance_km: float) -> int:
    """
    計算台中公車費率（雙十優惠）
    規則：前 10 公里免費，超過 10 公里部分依里程計費，但最高只收 10 元。
    """
    if distance_km <= 10:
        return 0
    
    # 假設超過 10 公里後，每公里費率約 2.5 元 (僅為示例計算)
    # 實際可能需依據站牌區間計算，這裡簡化為里程計費
    over_distance = distance_km - 10
    fare = math.ceil(over_distance * 2.5)
    
    # 最高收費 10 元
    return min(10, fare)

def calculate_mrt_fare(start_station_id: str, end_station_id: str) -> int:
    """
    計算台中捷運費率
    規則：基本票價 20 元，依據距離增加。
    TODO: 未來應改為從 SQLite 資料庫中讀取站間票價表。
    這裡暫時使用 mock 的假票價邏輯 (依據站號差異估算)。
    """
    if start_station_id == end_station_id:
        return 0
    
    # Mock 計算邏輯：假設站號包含數字，取差值 * 5 + 20
    # 實際應用中請連接 SQLite 查詢
    try:
        start_idx = int(''.join(filter(str.isdigit, start_station_id)))
        end_idx = int(''.join(filter(str.isdigit, end_station_id)))
        diff = abs(start_idx - end_idx)
        fare = 20 + (diff * 5)
        # 捷運票價上限通常為 50 元
        return min(50, fare)
    except Exception:
        # 如果無法解析，回傳預設最低票價
        return 20

def calculate_youbike_fare(minutes: int) -> int:
    """
    計算 YouBike 費率 (以 2.0 為例)
    規則：前 30 分鐘 10 元 (部分卡片或優惠為 0 元)，4 小時內每 30 分鐘 10 元。
    這裡以標準無優惠費率計算。
    """
    if minutes <= 0:
        return 0
    
    # 每 30 分鐘為一個區間
    intervals = math.ceil(minutes / 30.0)
    
    if minutes <= 240: # 4 小時內
        return intervals * 10
    elif minutes <= 480: # 4~8 小時
        return (8 * 10) + ((intervals - 8) * 20)
    else: # 超過 8 小時
        return (8 * 10) + (8 * 20) + ((intervals - 16) * 40)

def calculate_total_fare(segments: list) -> dict:
    """
    計算整趟旅程的總費用與細項。
    segments 格式範例：
    [
        {"type": "bus", "distance_km": 12.5},
        {"type": "mrt", "start_station": "103", "end_station": "110"},
        {"type": "youbike", "minutes": 15}
    ]
    """
    total = 0
    details = []

    for seg in segments:
        fare = 0
        seg_type = seg.get("type")
        
        if seg_type == "bus":
            fare = calculate_bus_fare(seg.get("distance_km", 0))
        elif seg_type == "mrt":
            fare = calculate_mrt_fare(seg.get("start_station", ""), seg.get("end_station", ""))
        elif seg_type == "youbike":
            fare = calculate_youbike_fare(seg.get("minutes", 0))
            
        total += fare
        details.append({
            "type": seg_type,
            "fare": fare
        })
        
    return {
        "total_fare": total,
        "details": details
    }

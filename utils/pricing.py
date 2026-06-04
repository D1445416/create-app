import math

def calculate_bus_fare(distance_km: float) -> int:
    """
    計算台中公車費率（雙十優惠）
    規則：前 10 公里免費，超過 10 公里部分依里程計費 (假設每公里 2.5 元)，但最高只收 10 元。
    """
    try:
        if distance_km <= 10:
            return 0
        
        over_distance = distance_km - 10
        fare = math.ceil(over_distance * 2.5)
        
        # 雙十優惠：最高收費 10 元
        return min(10, fare)
    except Exception:
        # 防呆機制：若資料異常，給予預設基本車資
        return 10

def calculate_mrt_fare(start_station_id: str, end_station_id: str) -> int:
    """
    計算台中捷運費率
    規則：基本票價 20 元，依據距離增加。
    防呆：若站點無法解析，回傳預設票價。
    """
    if start_station_id == end_station_id:
        return 0
    
    try:
        # Mock 計算邏輯：假設站號包含數字，取差值 * 5 + 20
        start_idx = int(''.join(filter(str.isdigit, start_station_id)))
        end_idx = int(''.join(filter(str.isdigit, end_station_id)))
        diff = abs(start_idx - end_idx)
        fare = 20 + (diff * 5)
        # 捷運票價上限通常為 50 元
        return min(50, fare)
    except Exception:
        # 防呆機制：若無法解析，回傳預設最低票價
        return 20

def calculate_youbike_fare(minutes: int) -> int:
    """
    計算 YouBike 費率 (以 2.0 為例)
    規則：前 30 分鐘 10 元，4 小時內每 30 分鐘 10 元。
    """
    try:
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
    except Exception:
        return 10

def get_transfer_discount(prev_type: str, curr_type: str) -> int:
    """
    判斷轉乘優惠金額 (1 小時內)
    規則範例：
    - 捷運轉乘公車或公車轉捷運：折抵 20 元 (依實際規定可能是部分金額)
    - 捷運/公車轉乘 YouBike：前 30 分鐘免費 (折抵 10 元)
    """
    discount = 0
    transfer_pair = {prev_type, curr_type}
    
    if "mrt" in transfer_pair and "bus" in transfer_pair:
        discount = 20
    elif ("mrt" in transfer_pair or "bus" in transfer_pair) and curr_type == "youbike":
        discount = 10
        
    return discount

def calculate_total_fare(segments: list) -> dict:
    """
    計算整趟旅程的詳細費用與轉乘優惠。
    """
    breakdown = {
        "bus": 0,
        "mrt": 0,
        "youbike": 0
    }
    total_discount = 0
    details = []
    
    prev_type = None

    for seg in segments:
        fare = 0
        seg_type = seg.get("type", "unknown")
        
        # 1. 計算基本費率
        if seg_type == "bus":
            fare = calculate_bus_fare(seg.get("distance_km", 0))
        elif seg_type == "mrt":
            fare = calculate_mrt_fare(seg.get("start_station", ""), seg.get("end_station", ""))
        elif seg_type == "youbike":
            fare = calculate_youbike_fare(seg.get("minutes", 0))
            
        # 2. 判斷轉乘優惠
        discount = 0
        if prev_type and prev_type != seg_type:
            discount = get_transfer_discount(prev_type, seg_type)
            # 優惠不能超過當次車資
            discount = min(discount, fare)
            
        # 3. 累計花費與優惠
        if seg_type in breakdown:
            breakdown[seg_type] += fare
            
        total_discount += discount
        
        details.append({
            "type": seg_type,
            "original_fare": fare,
            "discount_applied": discount,
            "actual_fare": fare - discount
        })
        
        prev_type = seg_type
        
    total_fare = sum(breakdown.values()) - total_discount
        
    return {
        "bus_fare": breakdown["bus"],
        "mrt_fare": breakdown["mrt"],
        "youbike_fare": breakdown["youbike"],
        "total_discount": total_discount,
        "total_fare": max(0, total_fare),
        "details": details
    }

from flask import Blueprint, render_template, request, jsonify, abort
# 匯入 Model 類別以供說明（骨架僅定義結構，不包含具體查詢實作）
from app.models import Station, CrowdednessCache

# 建立 Blueprint，以便在主程式 app.py 中註冊
views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """
    【首頁路由 - 站點與擁擠度列表】
    
    HTTP 方法: GET
    
    輸入參數 (Query Parameters):
    - `search` (string, 選填): 關鍵字過濾站點名稱 (如 "市政府")。
    - `type` (string, 選填): 篩選站點類型，可選值為 `'metro'` (捷運) 或 `'bus'` (公車)。
    - `level` (string, 選填): 篩選擁擠度等級，可選值為 `'green'`, `'orange'`, `'red'`。
    
    處理邏輯:
    1. 呼叫 `Station.get_all_with_crowdedness()` 取得所有站點與其快取。
    2. 根據傳入的 `search`、`type`、`level` 參數，在列表中篩選符合條件的站點。
    3. 渲染首頁模板。
    
    錯誤處理:
    - 若資料庫讀取異常，捕獲錯誤並渲染首頁，同時在前端提示系統忙碌中。
    
    對應 Jinja2 模板: `templates/index.html` (繼承 `base.html`)
    """
    pass

@views_bp.route('/station/<string:station_id>')
def station_detail(station_id):
    """
    【站點詳情頁路由】
    
    HTTP 方法: GET
    
    輸入參數 (Path Parameters):
    - `station_id` (string, 必填): 站點唯一 ID (例如: 'BL01')。
    
    處理邏輯:
    1. 呼叫 `Station.get_by_id(station_id)` 獲取站點基本資料。
    2. 若站點不存在，立即拋出 404 錯誤。
    3. 呼叫 `CrowdednessCache.is_cache_valid(station_id)` 驗證該站擁擠度快取是否在 60 秒時效內。
    4. 若快取過期，呼叫外部 TDX API 重新請求即時資訊並更新資料庫快取。
    5. 取得該站點的最新快取記錄 `CrowdednessCache.get_by_station_id(station_id)`。
    6. 將站點與擁擠度快取資料傳遞至模板進行渲染。
    
    錯誤處理:
    - 若 `station_id` 不存在，呼叫 `abort(404)` 渲染 404 錯誤頁面。
    - 若 TDX API 連線超時，使用資料庫舊有的快取資料，並在頁面上標註 "快取更新失敗，此為歷史資料"。
    
    對應 Jinja2 模板: `templates/detail.html` (繼承 `base.html`)
    """
    pass

@views_bp.route('/api/stations/nearby', methods=['GET'])
def api_nearby_stations():
    """
    【API 路由 - GPS 定位周邊推薦站點】
    
    HTTP 方法: GET
    
    輸入參數 (Query Parameters):
    - `lat` (float, 必填): 使用者的 GPS 緯度。
    - `lng` (float, 必填): 使用者的 GPS 經度。
    - `limit` (int, 選填): 限制回傳的站點數量，預設為 5。
    
    處理邏輯:
    1. 從 request 中取得 `lat`、`lng` 與 `limit`。
    2. 驗證 `lat` 與 `lng` 是否為合格的浮點數，若格式不符回傳 400 Bad Request。
    3. 呼叫 `Station.get_nearby(lat, lng, limit)` 計算與使用者位置之距離，依距離由近到遠排序。
    4. 將包含距離、擁擠度、名稱等資訊的站點列表以 JSON 格式回傳。
    
    輸出 (Response):
    - 成功: JSON 陣列 (HTTP 200)
    - 錯誤: JSON 錯誤訊息 `{"error": "錯誤描述"}` (HTTP 400 / 500)
    """
    pass

@views_bp.route('/api/stations/refresh', methods=['POST'])
def api_refresh_cache():
    """
    【API 路由 - 強制更新擁擠度快取】
    
    HTTP 方法: POST
    
    輸入參數 (JSON Body, 選填):
    - `station_id` (string, 選填): 若指定，僅更新該站點；若省略，則更新所有站點快取。
    
    處理邏輯:
    1. 接收 POST JSON 請求。
    2. 呼叫 `tdx_api` 服務模組以取得外部即時載客/擁擠度資料。
    3. 呼叫 `CrowdednessCache.create_or_update()` 更新對應的快取與 `last_updated` 時間戳。
    4. 回傳更新成功狀態與受影響的站點數量。
    
    輸出 (Response):
    - 成功: `{"success": true, "updated_count": count}` (HTTP 200)
    - 錯誤: `{"error": "錯誤描述"}` (HTTP 400 / 502 / 500)
    """
    pass

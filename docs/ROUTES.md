# Flask 路由與頁面設計說明文件 (ROUTES.md)

本文件根據 [PRD.md](file:///c:/Users/User/create-app/docs/PRD.md)、[ARCHITECTURE.md](file:///c:/Users/User/create-app/docs/ARCHITECTURE.md) 與 [DB_DESIGN.md](file:///c:/Users/User/create-app/docs/DB_DESIGN.md)，規劃**台中大眾運輸站點狀態與擁擠度顯示系統**的網頁路由設計與 API 端點規範。

所有路由皆符合 RESTful 架構慣例，並以 Flask Blueprint 架構進行封裝，實現模組化管理。

---

## 1. 路由總覽表格

| 功能 | HTTP 方法 | URL 路徑 | 對應 Jinja2 模板 / 回傳格式 | 說明 |
| :--- | :---: | :--- | :--- | :--- |
| **首頁（站點與擁擠度列表）** | `GET` | `/` | `templates/index.html` | 顯示所有站點清單，依擁擠度以紅、橘、綠三色指標呈現。支援關鍵字搜尋及路線/擁擠度篩選。 |
| **站點詳細頁面** | `GET` | `/station/<station_id>` | `templates/detail.html` | 顯示單一捷運或公車站點的詳細即時擁擠人潮、座標及大眾運輸資訊。 |
| **GPS 定位周邊站點推薦 API**| `GET` | `/api/stations/nearby` | `JSON 陣列` | 前端以 AJAX 調用，傳入經緯度，由後端運算並回傳距離最近的 5 個站點及其擁擠度。 |
| **強制更新快取 API** | `POST` | `/api/stations/refresh`| `JSON 物件` | 後端系統排程或前端點擊重整時，強制調用 TDX API 更新資料庫內的快取資料。 |

---

## 2. 每個路由的詳細說明

### A. 首頁 (站點與擁擠度列表)
*   **網址路徑**：`/`
*   **HTTP 方法**：`GET`
*   **輸入參數** (Query Parameters)：
    *   `search` (string, 選填)：關鍵字搜尋站點名稱。例如 `?search=市政府`
    *   `type` (string, 選填)：篩選站點類型。可選為 `'metro'` (捷運) 或 `'bus'` (公車)。
    *   `level` (string, 選填)：篩選擁擠度顏色。可選為 `'green'`, `'orange'`, `'red'`。
*   **處理邏輯**：
    1.  呼叫 `Station.get_all_with_crowdedness()` 獲取所有站點基本資料與其擁擠度快取。
    2.  根據前端傳入的 `search`、`type`、`level` 參數，對結果清單進行篩選過濾。
    3.  將最終過濾後的站點清單傳入首頁模板進行渲染。
*   **輸出**：
    *   `templates/index.html` (渲染 HTML)
*   **錯誤處理**：
    *   若資料庫連線失敗，則渲染首頁並於前端彈出 Bootstrap Toast 警告訊息 "系統資料讀取失敗，請稍後再試。"。

---

### B. 站點詳細頁面
*   **網址路徑**：`/station/<station_id>`
*   **HTTP 方法**：`GET`
*   **輸入參數** (Path Parameters)：
    *   `station_id` (string, 必填)：站點唯一 ID，如 `BL01` (捷運市政府站)。
*   **處理邏輯**：
    1.  呼叫 `Station.get_by_id(station_id)` 取得站點基本資料。若無此站點，拋出 `404 Not Found`。
    2.  呼叫 `CrowdednessCache.is_cache_valid(station_id, cache_duration_seconds=60)` 檢查快取是否仍在時效（60 秒）內。
    3.  若**快取過期**，呼叫 `tdx_api` 服務，向交通部 TDX API 請求最新數據，並呼叫 `CrowdednessCache.create_or_update()` 寫入 SQLite 快取。
    4.  若**快取有效**，則直接獲取 `CrowdednessCache.get_by_station_id(station_id)`。
    5.  將資料傳入 `detail.html` 渲染頁面。
*   **輸出**：
    *   `templates/detail.html` (渲染 HTML)
*   **錯誤處理**：
    *   若 `station_id` 不存在，呼叫 `abort(404)`，渲染 `templates/404.html`。
    *   若 TDX API 連線失效或回傳異常，在頁面顯示資料庫最後快取成功的數據，並顯示警告標註："目前無法連接 API 獲取最新狀態，以下為 {last_updated} 的歷史快取資料"。

---

### C. GPS 定位周邊推薦站點 API
*   **網址路徑**：`/api/stations/nearby`
*   **HTTP 方法**：`GET`
*   **輸入參數** (Query Parameters)：
    *   `lat` (float, 必填)：使用者目前的經度（緯度座標）。
    *   `lng` (float, 必填)：使用者目前的緯度（經度座標）。
    *   `limit` (int, 選填)：回傳數量上限，預設為 5。
*   **處理邏輯**：
    1.  從網址參數取得並校驗 `lat`、`lng`、`limit` 的型別，防止 SQL 注入與型別錯誤。
    2.  呼叫 `Station.get_nearby(lat, lng, limit)` 計算空間距離排序，並帶出對應的 `level` 擁擠度。
    3.  轉化成 JSON 陣列格式輸出。
*   **輸出** (Response Body)：
    *   `HTTP 200` 成功：
        ```json
        [
          {
            "station_id": "BL01",
            "name": "市政府站",
            "type": "metro",
            "route_name": "捷運綠線",
            "lat": 24.162,
            "lng": 120.647,
            "level": "red",
            "passenger_count": 350,
            "last_updated": "2026-05-21T08:30:00"
          }
        ]
        ```
*   **錯誤處理**：
    *   經緯度漏傳或型別非數字時：回傳 `HTTP 400 Bad Request`，JSON：`{"error": "Missing or invalid latitude/longitude coordinates"}`。
    *   伺服器內部錯誤：回傳 `HTTP 500 Internal Server Error`，JSON：`{"error": "Internal server error"}`。

---

### D. 強制更新快取 API
*   **網址路徑**：`/api/stations/refresh`
*   **HTTP 方法**：`POST`
*   **輸入參數** (JSON Body, 選填)：
    *   `station_id` (string, 選填)：可指定僅更新單一站點；若省略則更新全站。
*   **處理邏輯**：
    1.  解析 JSON 請求。
    2.  調用 `tdx_api.py` 去外部 TDX API 取得最新的即時資料。
    3.  利用 SQLite 的 `UPSERT` 寫入 `crowdedness_cache` 並標記 `last_updated` 時間。
*   **輸出** (Response Body)：
    *   `HTTP 200` 成功：`{"success": true, "updated_count": 1}`
*   **錯誤處理**：
    *   若 TDX API 連線失效或認證 Token 錯誤：回傳 `HTTP 502 Bad Gateway`，JSON：`{"error": "TDX API remote connection failure"}`。
    *   若指定的 `station_id` 在 `stations` 表中不存在：回傳 `HTTP 404 Not Found`，JSON：`{"error": "Station ID not found"}`。

---

## 3. Jinja2 模板清單

系統採用 Jinja2 模板引擎進行伺服器端渲染 (SSR)，規劃建立的 HTML 模板如下：

1.  **[templates/base.html](file:///c:/Users/User/create-app/app/templates/base.html)**
    *   **類型**：基礎佈局共用模板 (Base Layout)
    *   **職責**：包含網頁的全域 `<head>`、全域 CSS 樣式表 ( style.css )、網站的通用導覽列 (Header)、導覽頁尾 (Footer)、全域 Javascript ( main.js ) 以及 Bootstrap 框架。
    *   **區塊 (Blocks)**：定義 `{% block title %}{% endblock %}` 與 `{% block content %}{% endblock %}` 供子模板繼承填入。

2.  **[templates/index.html](file:///c:/Users/User/create-app/app/templates/index.html)**
    *   **繼承**：`base.html`
    *   **職責**：**系統首頁**。
    *   **元件**：
        *   搜尋輸入框與篩選按鈕（過濾捷運/公車/擁擠顏色）。
        *   「GPS 周邊推薦站點」專屬面板（點擊後以 Vanilla JS 調用瀏覽器 API 並渲染結果）。
        *   站點與擁擠度卡片列表（以紅、橘、綠三種顏色邊框或標籤顯示）。

3.  **[templates/detail.html](file:///c:/Users/User/create-app/app/templates/detail.html)**
    *   **繼承**：`base.html`
    *   **職責**：**站點詳情頁**。
    *   **元件**：
        *   站點基本資訊展示（包含大眾運輸類型徽章、所屬路線）。
        *   詳細人潮擁擠狀況、載客人數、資料最後更新時間戳記。
        *   手動重新整理按鈕（發送 AJAX POST 觸發強製重新整理並動態更新資訊）。
        *   「回首頁」連結。

4.  **[templates/404.html](file:///c:/Users/User/create-app/app/templates/404.html)**
    *   **繼承**：`base.html`
    *   **職責**：**404 錯誤頁面**。當使用者輸入不存在的站點 ID 或存取不當網址時，顯示具設計感的人性化錯誤提示與導回首頁按鈕。

---

## 4. 路由骨架程式碼結構

已經在 [app/routes/](file:///c:/Users/User/create-app/app/routes/) 資料夾中建立了控制器 (Controller) 的路由骨架檔案：

*   **套件匯出**：[app/routes/\_\_init\_\_.py](file:///c:/Users/User/create-app/app/routes/__init__.py)
*   **路由定義**：[app/routes/views.py](file:///c:/Users/User/create-app/app/routes/views.py)
    *   已完整規劃 `@views_bp.route` 裝飾器、RESTful 方法與詳細的 Traditional Chinese Docstrings。函式主體先以 `pass` 預留，將於後續開發階段進行具體實作。

> [!TIP]
> **RESTful 的 URL 設計優點**：
> 1. 首頁 `/` 使用 `GET` 並搭配 Query 參數處理篩選，對 SEO 與網址書籤功能極為友善。
> 2. API 端點 `/api/stations/nearby` 使用 `GET` 並附帶參數，符合取得資料的冪等性 (Idempotency)。
> 3. 強制刷新快取 API `/api/stations/refresh` 涉及寫入與快取狀態變更，故使用 `POST` 方法。

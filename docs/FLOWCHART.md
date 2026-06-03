# 系統流程圖與使用者流程圖文件 (FLOWCHART.md)

本文件根據 [PRD.md](file:///c:/Users/User/create-app/docs/PRD.md) 與 [ARCHITECTURE.md](file:///c:/Users/User/create-app/docs/ARCHITECTURE.md) 設計，詳細規劃了**台中大眾運輸站點狀態與擁擠度顯示系統**的「使用者操作流程」、「系統資料流序列圖」以及「後端 API/路由功能對照表」。

透過這些圖表，可以清晰地視覺化使用者與系統各個元件（包括 Flask Route、SQLite 資料庫與外部 TDX API）的互動模式。

---

## 1. 使用者流程圖 (User Flow)

此流程圖描述使用者從進入系統首頁開始，如何透過搜尋、篩選或定位功能來查詢台中大眾運輸站點的擁擠度，並查看站點的詳細資訊。

```mermaid
flowchart LR
    Start([使用者開啟網頁]) --> Home[首頁 - 站點與擁擠度列表]
    
    Home --> Action{要執行什麼操作？}
    
    Action -->|搜尋站點| Search[輸入關鍵字搜尋]
    Search --> SearchResult[顯示符合關鍵字的站點列表]
    SearchResult --> DetailCheck{點擊特定站點？}
    
    Action -->|篩選路線或擁擠度| Filter[選擇捷運/公車路線或擁擠度顏色]
    Filter --> FilterResult[顯示篩選後的站點列表]
    FilterResult --> DetailCheck
    
    Action -->|定位周邊推薦| GPS[點擊 GPS 定位推薦]
    GPS --> GPSCheck{瀏覽器定位授權？}
    GPSCheck -->|允許| NearbyList[計算距離，顯示最近的週邊站點]
    GPSCheck -->|拒絕| DefaultList[提示定位失敗，顯示預設站點列表]
    NearbyList --> DetailCheck
    DefaultList --> DetailCheck
    
    Action -->|直接瀏覽| DetailCheck
    
    DetailCheck -->|是| DetailPage[進入站點詳細資訊頁面]
    DetailPage --> DetailAction{執行其他操作？}
    DetailAction -->|查看擁擠度明細與圖表| DetailPage
    DetailAction -->|返回列表| Home
    
    DetailCheck -->|否| Home
```

> [!NOTE]
> 首頁的核心設計為「直觀的紅橘綠三色擁擠度指標」，讓使用者在進入首頁或進行篩選時，能在 1 秒內透過視覺顏色判斷各站點的人潮擁擠程度，有效提升通勤決策效率。

---

## 2. 系統序列圖 (Sequence Diagram)

為了解決外部 **TDX API** 呼叫限制並提升前端響應速度，系統實作了 SQLite 資料庫快取機制。以下分別說明「快取失效 (Cache Miss)」與「快取命中 (Cache Hit)」兩種情境，以及「前端 GPS 定位推薦」的系統資料流。

### 情境一：載入首頁且快取失效時 (Cache Miss)
當使用者載入頁面，且資料庫中的快取資料已過期（例如超過 1 分鐘），系統將主動呼叫 TDX API 並更新快取。

```mermaid
sequenceDiagram
    actor User as 使用者
    participant Browser as 瀏覽器 (Client)
    participant Flask as Flask Route (Controller)
    participant Model as Station Model (Model)
    participant DB as SQLite 資料庫
    participant TDX as TDX API 服務模組
    participant TDX_API as 交通部 TDX API

    User->>Browser: 開啟網頁或重新整理
    Browser->>Flask: GET /
    Flask->>Model: get_all_stations_with_crowdedness()
    Model->>DB: 查詢站點基本資料與擁擠度快取
    DB-->>Model: 回傳快取資料 (最後更新時間 > 1分鐘前，已過期)
    
    rect rgb(240, 248, 255)
        note right of Model: 【快取失效】啟動 TDX API 即時介接流程
        Model->>TDX: get_realtime_crowdedness_from_tdx()
        TDX->>TDX_API: 發送 API 請求 (帶有 OAuth2 認證 Token)
        TDX_API-->>TDX: 回傳 JSON 格式之即時擁擠度資料
        TDX-->>Model: 解析並整理後的擁擠度資料
        Model->>DB: 更新 SQLite 中的擁擠度快取與更新時間 (UPDATE/INSERT)
        DB-->>Model: 確認儲存成功
    end
    
    Model-->>Flask: 回傳最新站點與擁擠度列表
    Flask->>Flask: 使用 Jinja2 渲染 index.html (帶入紅橘綠顏色指標)
    Flask-->>Browser: 回傳渲染後的 HTML 頁面
    Browser-->>User: 呈現視覺化站點擁擠度列表
```

---

### 情境二：載入首頁且快取命中時 (Cache Hit)
當使用者在快取有效期內（例如 1 分鐘內）重複瀏覽，系統直接從 SQLite 讀取快取資料，不呼叫外部 API。

```mermaid
sequenceDiagram
    actor User as 使用者
    participant Browser as 瀏覽器 (Client)
    participant Flask as Flask Route (Controller)
    participant Model as Station Model (Model)
    participant DB as SQLite 資料庫

    User->>Browser: 再次瀏覽或重整頁面
    Browser->>Flask: GET /
    Flask->>Model: get_all_stations_with_crowdedness()
    Model->>DB: 查詢站點基本資料與擁擠度快取
    DB-->>Model: 回傳快取資料 (最後更新時間在 1分鐘內，有效)
    
    note right of Model: 【快取命中】直接讀取本地 SQLite 資料，不呼叫外部 API
    Model-->>Flask: 直接回傳快取的站點與擁擠度列表
    Flask->>Flask: 使用 Jinja2 渲染 index.html
    Flask-->>Browser: 回傳渲染後的 HTML 頁面
    Browser-->>User: 快速呈現站點擁擠度列表
```

---

### 情境三：使用者啟用 GPS 定位推薦周邊站點
當使用者點擊「定位推薦」，前端透過 Geolocation API 獲取座標，並以 AJAX 方式請求後端 API，計算距離後即時更新頁面。

```mermaid
sequenceDiagram
    actor User as 使用者
    participant Browser as 瀏覽器 (JS AJAX)
    participant Flask as Flask Route (Controller)
    participant Model as Station Model (Model)
    participant DB as SQLite 資料庫

    User->>Browser: 點擊「定位推薦最近站點」
    Browser->>Browser: 調用 Geolocation API 取得 GPS 座標 (Lat, Lng)
    Browser->>Flask: GET /api/stations/nearby?lat={Lat}&lng={Lng}
    Flask->>Model: get_nearby_stations(lat, lng)
    Model->>DB: 查詢所有站點座標與擁擠度快取
    DB-->>Model: 回傳站點資料
    Model->>Model: 計算各站點與使用者座標的距離，並排序篩選最近 5 站
    Model-->>Flask: 回傳最近站點列表 (含擁擠度與距離)
    Flask-->>Browser: 回傳 JSON 格式的站點與距離資料
    Browser->>Browser: 動態更新網頁 DOM，將推薦站點以紅橘綠視覺指標呈現
    Browser-->>User: 顯示距離最近的周邊站點與擁擠狀況
```

---

## 3. 功能清單對照表

本系統規定的功能、URL 路由、HTTP 方法及對應的架構元件對照如下：

| 功能名稱 | URL 路徑 | HTTP 方法 | 負責的模組 / 邏輯元件 | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| **首頁（站點與擁擠度列表）** | `/` | `GET` | `app/routes/views.py` (Controller)<br>`app/models/station.py` (Model)<br>`app/templates/index.html` (View) | 顯示台中捷運/公車的站點列表，依照即時擁擠度渲染紅、橘、綠三色指標。支援搜尋及路線篩選。 |
| **站點詳細資訊頁面** | `/station/<station_id>` | `GET` | `app/routes/views.py` (Controller)<br>`app/models/station.py` (Model)<br>`app/templates/detail.html` (View) | 顯示特定站點的詳細資訊、即時人潮細節、車廂載客分配或下一班車擁擠狀況。 |
| **取得定位周邊站點 (API)** | `/api/stations/nearby` | `GET` | `app/routes/views.py` (Controller)<br>`app/models/station.py` (Model) | 接收前端經緯度參數 (`lat`, `lng`)，計算距離並以 JSON 回傳距離最近的數個站點及擁擠度資料。 |
| **手動/系統更新快取 (API)** | `/api/stations/refresh` | `POST` | `app/routes/views.py` (Controller)<br>`app/services/tdx_api.py` (Service) | 提供前端手動重新整理或系統排程觸發，強制向 TDX API 重新請求最新擁擠度並寫入資料庫快取。 |

> [!TIP]
> **API 金鑰與防護考量**：
> 所有的外部 API 呼叫（如 `/api/stations/refresh`）後端程式碼均透過 `app/services/tdx_api.py` 來安全管理 `Client ID` 和 `Client Secret`（讀取自 `.env`），避免將敏感金鑰暴露在前端 JS 程式碼中。

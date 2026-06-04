# 流程圖設計 (Flowchart) - 台中大眾運輸交通整合APP系統

本文件根據 [PRD.md](file:///c:/Users/User/Desktop/create-app/docs/PRD.md) 的功能需求與 [ARCHITECTURE.md](file:///c:/Users/User/Desktop/create-app/docs/ARCHITECTURE.md) 的系統架構設計，繪製本系統的**使用者流程圖（User Flow）**與**系統序列圖（Sequence Diagram）**，並提供**功能清單對照表**。

---

## 1. 使用者流程圖 (User Flow)

此流程圖描述使用者從開啟網頁開始，操作各項主要功能（包括定位、路線規劃、地圖檢視、即時到站查詢、新增與刪除收藏）的操作路徑。

```mermaid
flowchart LR
    %% 定義節點樣式
    classDef startEnd fill:#f9f,stroke:#333,stroke-width:2px;
    classDef process fill:#bbf,stroke:#333,stroke-width:1px;
    classDef decision fill:#ffb,stroke:#333,stroke-width:1px;

    Start([使用者開啟網頁]) --> Home[首頁 /]
    Home --> ChooseAction{選擇操作}
    
    %% 操作 A: 路線規劃
    ChooseAction -->|規劃路線| RouteSearch[輸入/自動定位起訖點]
    RouteSearch --> SubmitSearch[送出路線規劃]
    SubmitSearch --> ResultPage[顯示結果頁 /transit/result]
    ResultPage --> ViewResult[查看總時間、車資與替代方案]
    ResultPage --> ActionOnResult{後續操作？}
    ActionOnResult -->|收藏路線| SaveRoute[點擊收藏 /transit/history/add]
    ActionOnResult -->|返回首頁| Home
    SaveRoute --> Home

    %% 操作 B: 地圖檢視
    ChooseAction -->|檢視附近站點| MapPage[地圖頁 /map]
    MapPage --> AutoLocate[瀏覽器自動定位]
    AutoLocate --> ShowStops[顯示附近大眾運輸站點]
    ShowStops --> ClickStop[點選站點查看即時資訊]

    %% 操作 C: 即時到站查詢
    ChooseAction -->|即時到站查詢| RealtimeSearch[即時到站查詢 /transit/arrival]
    RealtimeSearch --> InputRoute[輸入公車/捷運路線]
    InputRoute --> ShowArrival[顯示即時預估到站時間]

    %% 操作 D: 歷史紀錄與收藏
    ChooseAction -->|使用歷史/收藏| ViewHistory[查看歷史紀錄與常用路線]
    ViewHistory --> HistoryAction{操作紀錄？}
    HistoryAction -->|點擊紀錄| QuickSearch[一鍵填入起訖點並搜尋]
    HistoryAction -->|刪除紀錄| DeleteHistory[點擊刪除 /transit/history/delete]
    QuickSearch --> SubmitSearch
    DeleteHistory --> Home
```

---

## 2. 系統序列圖 (Sequence Diagram)

此圖描述「使用者點擊收藏路線（新增功能）」到「資料存入 SQLite 資料庫」的完整交互流程，涵蓋瀏覽器、Flask Route、Model 與資料庫。

```mermaid
sequenceDiagram
    actor User as 使用者
    participant Browser as 瀏覽器 (Browser)
    participant Flask as Flask Controller (routes/transit.py)
    participant Model as Model (models/route_history.py)
    participant DB as SQLite 資料庫 (database.db)
    
    User->>Browser: 在結果頁點擊「收藏路線」按鈕
    Browser->>Flask: POST /transit/history/add (起點、終點、路線詳情)
    activate Flask
    
    Note over Flask: 處理請求參數，確認使用者身分
    Flask->>Model: RouteHistory.add_to_favorite(user_id, start, end, details)
    activate Model
    
    Model->>DB: INSERT INTO route_history (user_id, start_point, end_point, is_favorite, ...)
    activate DB
    DB-->>Model: 回傳插入成功與資料列 ID
    deactivate DB
    
    Model-->>Flask: 回傳已建立之 RouteHistory 實體物件
    deactivate Model
    
    Flask-->>Browser: 302 Redirect to / (重新導向至首頁)
    deactivate Flask
    
    Browser->>Flask: GET / (請求首頁)
    activate Flask
    Flask-->>Browser: 回傳 HTML (包含更新後的常用路線列表)
    deactivate Flask
    
    Browser-->>User: 畫面重新載入，顯示新收藏的常用路線
```

---

## 3. 功能清單對照表

| 功能模組 | 功能描述 | URL 路徑 | HTTP 方法 | 對應後端檔案與 View |
| :--- | :--- | :--- | :--- | :--- |
| **首頁模組 (Main)** | 顯示搜尋表單與歷史/收藏列表 | `/` | `GET` | [main.py](file:///c:/Users/User/Desktop/create-app/app/routes/main.py) <br>渲染 `index.html` |
| **地圖模組 (Main)** | 大眾運輸檢視圖 (地圖頁面) | `/map` | `GET` | [main.py](file:///c:/Users/User/Desktop/create-app/app/routes/main.py) <br>渲染 `map.html` |
| **交通核心 (Transit)** | 執行起訖點路線規劃搜尋 | `/transit/search` | `POST` | [transit.py](file:///c:/Users/User/Desktop/create-app/app/routes/transit.py) <br>呼叫外部 API 並處理邏輯 |
| **交通核心 (Transit)** | 顯示路線規劃與時間預估結果 | `/transit/result` | `GET` | [transit.py](file:///c:/Users/User/Desktop/create-app/app/routes/transit.py) <br>渲染 `result.html` |
| **交通核心 (Transit)** | 即時到站時間查詢 | `/transit/arrival` | `GET` | [transit.py](file:///c:/Users/User/Desktop/create-app/app/routes/transit.py) <br>取得特定公車/捷運即時到站資訊 |
| **歷史與收藏 (History)** | 新增常用路線/收藏 | `/transit/history/add` | `POST` | [transit.py](file:///c:/Users/User/Desktop/create-app/app/routes/transit.py) <br>呼叫 [route_history.py](file:///c:/Users/User/Desktop/create-app/app/models/route_history.py) 寫入 |
| **歷史與收藏 (History)** | 刪除歷史紀錄或常用路線 | `/transit/history/delete/<int:id>` | `POST` | [transit.py](file:///c:/Users/User/Desktop/create-app/app/routes/transit.py) <br>呼叫 [route_history.py](file:///c:/Users/User/Desktop/create-app/app/models/route_history.py) 移除 |

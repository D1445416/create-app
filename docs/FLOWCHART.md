# 流程圖設計文件 (Flowcharts & Sequence Diagrams)

本文件使用 Mermaid 語法來繪製「台中大眾運輸交通整合APP」F-03 轉乘規劃模組的操作流程與資料流。

## 一、使用者流程圖 (User Flow)

這個流程圖描述使用者在網頁上的操作路徑：

```mermaid
flowchart TD
    Start([使用者訪問 /f03/planner]) --> InitView[地圖載入：預設顯示台中所有地標標記]
    InitView --> Selection[使用者在下拉選單選擇起點站與終點站]
    Selection --> Prefs[勾選偏好的交通工具: 捷運/公車/YouBike/火車]
    Prefs --> Submit[點擊「開始規劃路徑」按鈕]
    
    Submit --> Val{輸入驗證}
    Val -->|起訖點相同| ErrSame[頁面顯示警告: 起點與終點不能相同] --> Selection
    Val -->|通過| Calc[後端 Dijkstra 演算法計算最佳路線]
    
    Calc --> ResultCheck{是否有可行路線?}
    ResultCheck -->|否| ErrNoPath[頁面顯示提示: 無法在目前偏好下找到合適路線] --> Prefs
    ResultCheck -->|是| Render[前端渲染結果]
    
    Render --> Sidebar[左側顯示預估時間、費用、轉乘次數與詳細時間軸]
    Render --> MapDraw[右側 Leaflet 地圖標註起訖點並繪製分色運具折線]
    
    Sidebar --> Interaction[使用者點擊地圖標記或路線線段查看氣泡提示]
    MapDraw --> Interaction
    Interaction --> End([完成查詢 / 重新查詢])
```

---

## 二、系統序列圖 (Sequence Diagram)

這張序列圖描述當使用者提交查詢時，資料如何在瀏覽器、Flask 路由控制、Dijkstra 演算法服務與地圖渲染庫之間傳遞：

```mermaid
sequenceDiagram
    actor User as 使用者
    participant Browser as 瀏覽器 (HTML/JS)
    participant Flask as Flask 路由控制器 (f03_routing)
    participant Service as 轉乘演算服務 (route_calculator)
    participant Leaflet as Leaflet.js 地圖庫

    User->>Browser: 選擇起訖站、勾選交通偏好並點擊規劃
    Browser->>Flask: HTTP POST /f03/planner (傳送 start_point, end_point, preferences)
    Note over Flask: 執行防呆驗證<br/>(檢查起訖是否相同)
    
    alt 驗證通過
        Flask->>Service: calculate_best_route(start, end, preferences)
        Note over Service: 1. 根據 preferences 過濾圖資邊<br/>2. Dijkstra 演算法搜尋最短時間路徑
        Service-->>Flask: 回傳最優路線字典 (含 total_time, total_cost, steps, route_coords)
        Flask->>Browser: 載入模板渲染 HTML，並將 route_result 轉成 JSON 嵌入 JS 區塊
        Browser->>Leaflet: 初始化地圖，載入 CartoDB 圖磚
        Browser->>Leaflet: 標註起訖點 Marker 並為 steps 繪製對應色彩的 Polyline
        Leaflet-->>User: 呈現視覺化地圖與路線詳細時間軸
    else 驗證失敗 (起訖相同)
        Flask-->>Browser: 傳回錯誤訊息 error
        Browser-->>User: 顯示警告警告框
    end
```

---

## 三、功能清單與對照表

以下為 F-03 模組規劃之 URL 路由與 HTTP 動作對照：

| 功能編號 | 功能名稱 | URL 路徑 | HTTP 方法 | 後端處理函式 | 前端對應視圖 / 模板 |
| --- | --- | --- | --- | --- | --- |
| **F-03** | 跨運具轉乘首頁與地標檢視 | `/f03/planner` | **GET** | `route_planner()` | `f03/route_planner.html` (地圖初始呈現) |
| **F-03** | 執行轉乘路徑演算與繪圖 | `/f03/planner` | **POST** | `route_planner()` | `f03/route_planner.html` (地圖繪製折線與時間軸) |

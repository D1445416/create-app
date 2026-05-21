# 路由與頁面設計文件 (Routes & Page Design)

本文件描述「台中大眾運輸交通整合APP」F-03 轉乘規劃模組的 URL 路由規劃與前端 Jinja2 模板對照。

## 一、路由總覽表格

| 功能 | HTTP 方法 | URL 路徑 | 對應模板 | 說明 |
| --- | --- | --- | --- | --- |
| 轉乘規劃首頁 | GET | `/f03/planner` | `app/templates/f03/route_planner.html` | 進入頁面，顯示預設地標地圖與路線查詢表單。 |
| 轉乘路徑演算與繪圖 | POST | `/f03/planner` | `app/templates/f03/route_planner.html` | 接收起迄點與運具偏好表單，執行 Dijkstra 演算法，將路線渲染至地圖與左側時間軸。 |

---

## 二、路由詳細說明

### 2.1 轉乘規劃首頁 (`GET /f03/planner`)

- **輸入**：無。
- **處理邏輯**：
  1. 後端載入 `app/services/route_calculator.py` 中的靜態地標清單 `LANDMARKS`。
  2. 將地標名稱排序後，打包為 `landmarks` 清單變數。
- **輸出**：渲染並回傳 `f03/route_planner.html`，前端 JS 會接收地標清單並在地圖上繪製預設大眾運輸站點的標記點。

### 2.2 轉乘路徑演算 (`POST /f03/planner`)

- **輸入**：
  - `start_point` (form-data: select, 必填) - 起點站名稱。
  - `end_point` (form-data: select, 必填) - 終點站名稱。
  - `preferences` (form-data: array of checkboxes) - 偏好交通工具 (可包含 `mrt`, `bus`, `youbike`, `train`)。
- **處理邏輯**：
  1. **防呆驗證 1**：若 `start_point` 或 `end_point` 未傳入，設定 `error = '請選擇起點與終點'`。
  2. **防呆驗證 2**：若 `start_point == end_point`，設定 `error = '起點與終點不能相同'`。
  3. **演算法搜尋**：若驗證通過，呼叫核心服務層 `calculate_best_route(start_point, end_point, preferences)` 計算最快轉乘路徑。
  4. **路徑存在性驗證**：若演算法回傳 `None` (無可行路徑)，設定 `error = '無法在目前偏好下找到合適路線，請嘗試勾選更多交通工具或步行。'`。
- **輸出**：
  - 成功：渲染 `f03/route_planner.html`，帶入 `route_result` 字典資料，前端 JS 將座標數組繪製為色彩折線。
  - 失敗：渲染 `f03/route_planner.html`，帶入 `error` 字串，於頁面頂部彈出紅色警示框。

---

## 三、Jinja2 模板清單

### 3.1 基礎父模板：`app/templates/base.html`
- **結構**：
  - `<head>`：宣告 viewport、全站 UTF-8 編碼、引入 Bootstrap 5 CSS 與 Bootstrap Icons 樣式庫。
  - `<body>`：全站共用頂部導覽列，包含「交通資訊整合平台」品牌標題與選單連結。
  - 區塊 `{ % block content % }`：供子模板置入主頁面內容。
  - 腳本：引入 Bootstrap 5 JS Bundle。

### 3.2 轉乘規劃模板：`app/templates/f03/route_planner.html`
- **繼承關係**：繼承自 `base.html`。
- **外部資源**：於 `{ % block styles % }` 與 `{ % block scripts % }` 中引入 Leaflet.js 的樣式表與 JavaScript 腳本庫。
- **版面配置**：
  - 左側欄 (col-md-4 / col-lg-4)：包含路線搜尋卡片與最佳路線細節時間軸。
  - 右側欄 (col-md-8 / col-lg-8)：全高 Leaflet.js 地圖容器與大眾運輸顏色徽章圖例。

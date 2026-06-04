# 路由與頁面設計文件 (Routes & Page Design) - 台中大眾運輸交通整合APP系統

本文件詳細規劃本系統的 Flask 路由設計（Routes/Controllers）與前端頁面結構，並建立與資料庫 Model 及前端 UI 模板的對照關係。

---

## 1. 路由總覽表

我們將路由劃分為三個主要模組：**主頁面與地圖 (Main)**、**交通核心業務 (Transit)** 以及 **身分驗證 (Auth)**。

| 功能模組 | HTTP 方法 | URL 路徑 | 對應 Jinja2 模板 | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| **首頁 (Main)** | GET | `/` | [index.html](file:///c:/Users/User/Desktop/create-app/app/templates/index.html) | 顯示首頁搜尋表單、歷史搜尋紀錄與常用最愛路線 |
| **地圖 (Main)** | GET | `/map` | [map.html](file:///c:/Users/User/Desktop/create-app/app/templates/map.html) | 顯示大眾運輸地圖檢視圖（捷運、公車、YouBike站點） |
| **交通 (Transit)** | POST | `/transit/search` | — (重導向至結果頁) | 接收起訖點搜尋條件，呼叫 TDX API 並將紀錄寫入 DB |
| **交通 (Transit)** | GET | `/transit/result` | [result.html](file:///c:/Users/User/Desktop/create-app/app/templates/result.html) | 顯示路線規劃結果（車程時間、車資、替代方案） |
| **交通 (Transit)** | GET | `/transit/arrival` | [arrival.html](file:///c:/Users/User/Desktop/create-app/app/templates/arrival.html) | 即時公車/捷運到站時間查詢頁面 |
| **歷史 (Transit)** | POST | `/transit/history/add` | — (重導向至首頁) | 將指定搜尋紀錄標記為「常用最愛」或新增最愛 |
| **歷史 (Transit)** | POST | `/transit/history/delete/<id>` | — (重導向至首頁) | 刪除指定的搜尋歷史紀錄或最愛收藏 |
| **驗證 (Auth)** | GET | `/register` | [register.html](file:///c:/Users/User/Desktop/create-app/app/templates/register.html) | 顯示使用者註冊頁面 |
| **驗證 (Auth)** | POST | `/register` | — (重導向至登入/首頁) | 接收註冊表單，寫入 `user` 表 |
| **驗證 (Auth)** | GET | `/login` | [login.html](file:///c:/Users/User/Desktop/create-app/app/templates/login.html) | 顯示使用者登入頁面 |
| **驗證 (Auth)** | POST | `/login` | — (重導向至首頁) | 驗證使用者帳密，寫入 session |
| **驗證 (Auth)** | POST | `/logout` | — (重導向至首頁) | 清除 session 登出使用者 |

---

## 2. 路由詳細說明

### 2.1 主頁面模組 (`main_bp`)

#### GET `/`
*   **輸入參數**：無（從 `session['user_id']` 判斷當前登入狀態）
*   **處理邏輯**：
    *   若使用者已登入，呼叫 `RouteHistoryModel.get_by_user_id(user_id)` 撈取該使用者的歷史紀錄與收藏路線。
*   **輸出**：渲染 `index.html`（傳入 `history_list` 與 `favorite_list`）
*   **錯誤處理**：若資料庫連線失敗，回傳 500。

#### GET `/map`
*   **輸入參數**：`lat`、`lng`（選填，前端 Geolocation 取得的座標）
*   **處理邏輯**：若有座標傳入，計算周邊站點；若無，預設顯示台中市中心。
*   **輸出**：渲染 `map.html`。

---

### 2.2 交通業務模組 (`transit_bp`)

#### POST `/transit/search`
*   **輸入參數**：表單欄位 `start_point`、`end_point`（必填）
*   **處理邏輯**：
    1.  檢查欄位是否為空。
    2.  呼叫外部 TDX API 計算最佳大眾運輸規劃與替代方案。
    3.  若使用者已登入，呼叫 `RouteHistoryModel.create()` 儲存搜尋歷史至 DB。
    4.  將路線規劃結果暫存至 `session['search_result']`。
*   **輸出**：重導向 (302) 至 `/transit/result`。
*   **錯誤處理**：
    *   起訖點為空 ➡️ 導回首頁並拋出 Flash 錯誤訊息。
    *   TDX API 逾時/失敗 ➡️ 導回首頁提示「無法取得路線資料」。

#### GET `/transit/result`
*   **輸入參數**：無（從 `session['search_result']` 讀取）
*   **處理邏輯**：讀取暫存的搜尋規劃，提供票價、路程時間與各段交通工具明細。
*   **輸出**：渲染 `result.html`。

#### GET `/transit/arrival`
*   **輸入參數**：`route_name`（選填，如 `"300"`）
*   **處理邏輯**：向 TDX API 查詢該公車路線或捷運站的即時預估到站時間。
*   **輸出**：渲染 `arrival.html`。

#### POST `/transit/history/add`
*   **輸入參數**：表單欄位 `start_point`、`end_point`、`details`
*   **處理邏輯**：
    *   若未登入，提示需登入。
    *   已登入則呼叫 `RouteHistoryModel.create(..., is_favorite=1)` 或 `RouteHistoryModel.update_favorite()`。
*   **輸出**：重導向至 `/`，並顯示 Flash「已成功加入常用路線」。

#### POST `/transit/history/delete/<int:history_id>`
*   **輸入參數**：URL 參數 `history_id`
*   **處理邏輯**：呼叫 `RouteHistoryModel.delete(history_id)`。
*   **輸出**：重導向至 `/`。

---

### 2.3 身分驗證模組 (`auth_bp`)

#### GET & POST `/register`
*   **輸入參數**：表單欄位 `username`、`password`、`email`
*   **處理邏輯**：
    *   GET：直接渲染註冊表單。
    *   POST：使用 `generate_password_hash` 加密密碼，呼叫 `UserModel.create()` 寫入。
*   **輸出**：註冊成功重導向至 `/login`；失敗則帶回註冊頁面並顯示錯誤。

#### GET & POST `/login`
*   **輸入參數**：表單欄位 `username`、`password`
*   **處理邏輯**：
    *   GET：直接渲染登入表單。
    *   POST：呼叫 `UserModel.get_by_username()`，利用 `check_password_hash` 比對密碼。驗證通過後，將 `id` 與 `username` 寫入 `session`。
*   **輸出**：成功導向至 `/`；失敗顯示「帳號或密碼錯誤」。

#### POST `/logout`
*   **處理邏輯**：清空 `session` 中使用者的登入資訊。
*   **輸出**：重導向至 `/`。

---

## 3. Jinja2 模板清單

所有模板皆存放在 `app/templates/` 目錄。我們規劃了共同的基礎母版以維護版面一致性。

1.  **[base.html](file:///c:/Users/User/Desktop/create-app/app/templates/base.html)**
    *   **角色**：基礎母版 (Base Template)
    *   **內容**：HTML 標頭、CSS/JS 靜態資源引入、導覽列（包含首頁、地圖、即時到站連結與使用者登入/登出狀態按鈕）、以及頁尾。
2.  **[index.html](file:///c:/Users/User/Desktop/create-app/app/templates/index.html)**
    *   **角色**：首頁 (首頁搜尋表單與歷史/最愛) — 繼承 `base.html`
3.  **[map.html](file:///c:/Users/User/Desktop/create-app/app/templates/map.html)**
    *   **角色**：地圖檢視頁面 — 繼承 `base.html`
4.  **[result.html](file:///c:/Users/User/Desktop/create-app/app/templates/result.html)**
    *   **角色**：路線規劃結果顯示頁面 — 繼承 `base.html`
5.  **[arrival.html](file:///c:/Users/User/Desktop/create-app/app/templates/arrival.html)**
    *   **角色**：即時到站查詢頁面 — 繼承 `base.html`
6.  **[login.html](file:///c:/Users/User/Desktop/create-app/app/templates/login.html)**
    *   **角色**：登入頁面 — 繼承 `base.html`
7.  **[register.html](file:///c:/Users/User/Desktop/create-app/app/templates/register.html)**
    *   **角色**：註冊頁面 — 繼承 `base.html`

# 系統架構文件：台中大眾運輸站點狀態與擁擠度顯示系統

## 1. 技術架構說明

本專案採用輕量級的 Python Flask 框架，搭配 Jinja2 模板引擎進行伺服器端渲染 (SSR, Server-Side Rendering)。這種架構適合規模適中、不需複雜前端狀態管理的應用，能快速建立起系統的原型並上線。

- **後端 (Backend)**：Python 3 + Flask
  - 負責接收使用者請求、介接外部 TDX API、處理資料快取與核心業務邏輯。
- **模板引擎 (Template Engine)**：Jinja2
  - 負責將後端處理好的資料（如站點列表、擁擠度顏色）動態填入 HTML 中，並回傳給使用者的瀏覽器。
- **前端 (Frontend)**：HTML / CSS / JavaScript (Vanilla JS)
  - 處理基本的使用者互動（如地理定位 API）、版面配置與響應式設計 (RWD)。
- **資料庫 (Database)**：SQLite 
  - 用於儲存站點基本靜態資料（如站點名稱、座標），以及快取從 TDX API 取得的即時擁擠度資料。

### Flask MVC 模式說明
本專案採用類似 MVC (Model-View-Controller) 的架構來分離關注點：
- **Model (模型)**：對應資料庫結構與 TDX API 的資料處理，負責資料的存取與快取邏輯。
- **View (視圖)**：對應 Jinja2 HTML 模板，負責介面的呈現。
- **Controller (控制器)**：對應 Flask 路由 (Routes)，負責接收使用者請求、呼叫 Model 取得資料，再將資料傳遞給 View 進行渲染。

---

## 2. 專案資料夾結構

本專案建議採用模組化的結構，便於未來的維護與擴充：

```text
create-app/
├── app/                      # 應用程式主目錄
│   ├── models/               # 資料庫模型與資料存取邏輯
│   │   ├── __init__.py
│   │   └── station.py        # 站點資料與快取模型
│   ├── routes/               # Flask 路由 (Controller)
│   │   ├── __init__.py
│   │   └── views.py          # 頁面路由與 API 端點
│   ├── services/             # 外部服務介接模組
│   │   ├── __init__.py
│   │   └── tdx_api.py        # TDX API 介接與認證邏輯
│   ├── templates/            # Jinja2 HTML 模板 (View)
│   │   ├── base.html         # 基礎共用模板 (包含 Header, Footer)
│   │   ├── index.html        # 首頁 (站點列表與擁擠度顯示)
│   │   └── detail.html       # 站點詳細資訊頁面
│   └── static/               # 靜態資源檔案
│       ├── css/
│       │   └── style.css     # 全域樣式表 (包含紅、橘、綠顏色指標定義)
│       └── js/
│           └── main.js       # 前端互動邏輯 (如 GPS 定位取得)
├── instance/                 # 放置不需加入版控的應用程式執行個體檔案
│   └── database.db           # SQLite 資料庫檔案
├── docs/                     # 專案文件目錄
│   ├── PRD.md                # 產品需求文件
│   └── ARCHITECTURE.md       # 系統架構文件 (本文)
├── app.py                    # Flask 應用程式入口檔案
├── requirements.txt          # Python 依賴套件清單
└── .env                      # 環境變數設定檔 (如 TDX API 金鑰，不進版控)
```

---

## 3. 元件關係圖

以下圖表說明了系統中各元件如何協同工作：

```mermaid
flowchart TD
    Browser[瀏覽器 / 使用者]

    subgraph Flask 應用程式
        Router[Flask Route (Controller)]
        Template[Jinja2 Template (View)]
        TDXService[TDX API 服務模組]
        Model[資料庫 Model]
    end

    DB[(SQLite 資料庫\n站點資料 & 快取)]
    TDX_API((交通部 TDX API))

    %% Request flow
    Browser -- "1. 發送 HTTP 請求\n(如瀏覽首頁)" --> Router
    Router -- "2. 檢查快取 / 取得資料" --> Model
    Model -- "3. 讀寫資料" --> DB
    
    %% Cache Miss Flow
    Model -. "4. 若快取過期，呼叫 API 服務" .-> TDXService
    TDXService -. "5. 抓取即時擁擠度資料" .-> TDX_API
    TDXService -. "6. 回傳資料並更新至" .-> Model

    %% Response flow
    Router -- "7. 將資料傳遞給模板" --> Template
    Template -- "8. 渲染完整的 HTML" --> Router
    Router -- "9. 回傳 HTTP 回應" --> Browser
```

---

## 4. 關鍵設計決策

1. **伺服器端渲染 (Flask + Jinja2)**
   - **原因**：考量到專案需求著重於資訊展示與簡單的篩選/搜尋操作，不需要複雜的前端狀態管理工具（如 React/Vue）。使用 Flask + Jinja2 可以大幅降低開發門檻，加快原型開發速度。

2. **使用 SQLite 作為快取與靜態資料庫**
   - **原因**：SQLite 屬於輕量級檔案型資料庫，不需額外架設資料庫伺服器，非常適合小型專案與 MVP 階段。我們將靜態的站點資訊（如站名、代碼、經緯度）預先存入 SQLite，並將 TDX API 取得的即時擁擠度資料加上「最後更新時間」存入資料庫作為快取。

3. **實作 TDX API 資料快取機制**
   - **原因**：TDX API 有嚴格的呼叫次數限制 (Rate Limit)。為避免頻繁重新整理頁面導致 API 請求過量被封鎖，系統會在呼叫 API 後將結果存放在資料庫中，並設定過期時間（例如 1 分鐘）。當有新請求進入時，若快取未過期則直接讀取資料庫，過期才重新向 TDX 發出請求，以此同時兼顧效能與即時性。

4. **分離外部服務介接邏輯 (`services/tdx_api.py`)**
   - **原因**：TDX API 需要處理 Oauth2 Token 認證與不同端點的呼叫。將這些邏輯獨立於路由與 Model 之外，能保持 Controller 的簡潔，未來若 TDX API 規格變更，也只需修改單一模組，提升程式碼的內聚性與可維護性。

5. **環境變數管理 (.env)**
   - **原因**：基於資安考量，TDX API 的 `Client ID` 和 `Client Secret` 絕對不能寫死在程式碼中。系統將採用 `python-dotenv` 套件讀取 `.env` 檔案，確保開發者的敏感資訊得到妥善保護，且不會不小心推送到 Git 上。

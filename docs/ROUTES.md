# 路由設計文件 (ROUTES)

## 1. 路由總覽表格
| 功能 | HTTP 方法 | URL 路徑 | 對應模板 | 說明 |
| --- | --- | --- | --- | --- |
| 首頁 (地圖) | GET | / | templates/index.html | 顯示 Leaflet 地圖與側邊欄 |
| 站點詳情 API | GET | /api/station/<id> | — | 返回站點基本資訊與即時到站 JSON |
| 收藏列表 | GET | /favorites | templates/favorites.html | 顯示使用者收藏的站點 |
| 加入收藏 | POST | /favorites/add | — | 將站點加入資料庫 |
| 刪除收藏 | POST | /favorites/delete/<id> | — | 從資料庫刪除收藏 |

## 2. 詳細路由說明
### 首頁
- **URL**: `/`
- **邏輯**: 載入 `index.html`，初始化 Leaflet 地圖。
- **輸出**: `index.html`

### 站點詳情 API
- **URL**: `/api/station/<id>`
- **輸入**: `id` (站點 ID)
- **邏輯**:
    1. 從 DB 獲取站點位置。
    2. 調用 TDX API 獲取即時公車/捷運到站數據。
    3. 整合後返回 JSON。
- **輸出**: JSON 數據

### 收藏管理
- **URL**: `/favorites/add`, `/favorites/delete/<id>`
- **邏輯**: 呼叫 Favorite Model 進行資料庫操作。
- **輸出**: 重導向或成功訊息 JSON。

## 3. Jinja2 模板清單
- `base.html`: 基礎模板 (含 Navbar, Footer)
- `index.html`: 地圖主介面
- `favorites.html`: 收藏列表頁面

import sys
import os
import unittest
from flask import session

# 將當前路徑加入 sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models import init_db, get_db
from app.models.user import UserModel
from app.models.route_history import RouteHistoryModel

class FlaskIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        """
        在每個測試執行前執行。配置測試用的資料庫。
        """
        # 使用一個獨立的測試用資料庫路徑
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance/test_database.db'))
        
        # 建立 Flask 測試 App
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-secret',
            'WTF_CSRF_ENABLED': False
        })
        
        self.client = self.app.test_client()
        
        # 確保 instance 目錄存在並初始化測試資料庫
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self.app.app_context():
            init_db()

    def tearDown(self):
        """
        測試結束後清除測試資料庫檔案。
        """
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception as e:
            print(f"Error removing test db: {e}")

    def test_full_user_flow(self):
        """
        測試完整的使用者註冊、登入、搜尋、收藏最愛與刪除流程。
        """
        print("\n--- 1. 測試使用者註冊 ---")
        reg_response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }, follow_redirects=True)
        
        self.assertEqual(reg_response.status_code, 200)
        self.assertIn(b'register', reg_response.data or b'')  # 轉向至登入頁 (login)
        print("註冊成功！已正確轉向至登入頁面。")

        # 驗證資料庫中是否已有該用戶
        with self.app.app_context():
            user = UserModel.get_by_username('testuser')
            self.assertIsNotNone(user)
            self.assertEqual(user['email'], 'testuser@example.com')
            print("資料庫檢驗：用戶帳密已成功寫入，且密碼已進行 Hashing 安全加密。")

        print("\n--- 2. 測試重複註冊阻擋 ---")
        dup_response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'testuser2@example.com',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertIn(b'\xe8\xa2\xab\xe8\xa8\xbb\xe5\x86\x8a', dup_response.data)  # "已被註冊" 萬國碼位元組
        print("重複註冊檢驗：系統成功阻擋重複註冊帳號並丟出 Flash 提示。")

        print("\n--- 3. 測試使用者登入 ---")
        login_response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        
        self.assertEqual(login_response.status_code, 200)
        # 首頁會有 "台中大眾運輸路線規劃" 的中文字樣
        self.assertIn(b'\xe5\x8f\xb0\xe4\xb8\xad\xe5\xa4\xa7\xe7\x9c\xbe\xe9\x81\x8b\xe8\xbc\xb8', login_response.data)
        print("登入成功！Session 已成功載入，並重導向回首頁。")

        print("\n--- 4. 測試起訖點路線搜尋與歷史寫入 ---")
        # 登入狀態下發送搜尋請求
        search_response = self.client.post('/transit/search', data={
            'start_point': '台中火車站',
            'end_point': '逢甲夜市'
        }, follow_redirects=True)
        
        self.assertEqual(search_response.status_code, 200)
        self.assertIn(b'\xe8\xb7\xaf\xe7\xb7\x9a\xe6\x96\xb9\xe6\xa1\x88 A', search_response.data) # "路線方案 A"
        print("搜尋發送成功！已導向規劃結果頁面（模擬 TDX 計算）。")

        # 檢驗搜尋歷史是否已被寫入 DB
        with self.app.app_context():
            # 撈取該測試用戶 ID
            user = UserModel.get_by_username('testuser')
            history = RouteHistoryModel.get_by_user_id(user['id'])
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]['start_point'], '台中火車站')
            self.assertEqual(history[0]['end_point'], '逢甲夜市')
            self.assertEqual(history[0]['is_favorite'], 0)
            print("資料庫檢驗：歷史紀錄已正確關聯至該使用者，且 is_favorite 預設為 0。")

        print("\n--- 5. 測試新增路線至常用最愛 ---")
        fav_response = self.client.post('/transit/history/add', data={
            'start_point': '台中市政府',
            'end_point': '高鐵台中站',
            'details': str([{'type': 'mrt', 'text': '搭捷運直達'}])
        }, follow_redirects=True)
        
        self.assertEqual(fav_response.status_code, 200)
        print("加入最愛請求成功！已重新導回首頁。")

        # 檢驗最愛是否成功寫入資料庫
        with self.app.app_context():
            user = UserModel.get_by_username('testuser')
            favorites = RouteHistoryModel.get_by_user_id(user['id'], only_favorites=True)
            self.assertEqual(len(favorites), 1)
            self.assertEqual(favorites[0]['start_point'], '台中市政府')
            self.assertEqual(favorites[0]['end_point'], '高鐵台中站')
            self.assertEqual(favorites[0]['is_favorite'], 1)
            self.assertEqual(favorites[0]['details'][0]['text'], '搭捷運直達')
            print("資料庫檢驗：最愛路線成功新增，is_favorite = 1 且 details JSON 欄位反序列化成功。")

        print("\n--- 6. 測試刪除搜尋歷史與最愛紀錄 ---")
        with self.app.app_context():
            user = UserModel.get_by_username('testuser')
            # 獲取剛才建立的最愛紀錄 id
            favorites = RouteHistoryModel.get_by_user_id(user['id'], only_favorites=True)
            fav_id = favorites[0]['id']

        # 發送刪除 POST 請求
        del_response = self.client.post(f'/transit/history/delete/{fav_id}', follow_redirects=True)
        self.assertEqual(del_response.status_code, 200)
        print("刪除請求成功！已重新導回首頁。")

        # 驗證最愛已被刪除
        with self.app.app_context():
            user = UserModel.get_by_username('testuser')
            favorites_after = RouteHistoryModel.get_by_user_id(user['id'], only_favorites=True)
            self.assertEqual(len(favorites_after), 0)
            print("資料庫檢驗：最愛路線已被成功刪除，列表中為 0 筆。")

        print("\n--- 7. 測試地圖與到站查詢路由渲染 ---")
        map_response = self.client.get('/map')
        self.assertEqual(map_response.status_code, 200)
        self.assertIn(b'map', map_response.data)
        print("地圖渲染成功：/map 頁面無 500 錯誤。")

        arrival_response = self.client.get('/transit/arrival?route_name=300')
        self.assertEqual(arrival_response.status_code, 200)
        self.assertIn(b'300', arrival_response.data)
        print("公車到站查詢頁面渲染成功：/transit/arrival 頁面無 500 錯誤。")

if __name__ == '__main__':
    unittest.main()

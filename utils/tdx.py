import requests
import json

class TDXClient:
    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    def get_token(self):
        # 實際實作時需向 TDX 請求 Token
        # 這裡先回傳模擬 Token
        return "mock_token"

    def get_bus_arrival(self, station_id):
        # 模擬公車到站數據
        return [
            {"RouteName": "300", "EstimateTime": 0},
            {"RouteName": "301", "EstimateTime": 300},
            {"RouteName": "305", "EstimateTime": 720}
        ]

    def get_mrt_arrival(self, station_id):
        # 模擬捷運到站數據
        return [
            {"Destination": "北屯總站", "EstimateTime": 180},
            {"Destination": "高鐵台中站", "EstimateTime": 480}
        ]

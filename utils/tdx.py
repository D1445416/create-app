import requests
import json
import time
import datetime
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

class TDXClient:
    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id or os.getenv("TDX_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("TDX_CLIENT_SECRET")
        self.access_token = None
        self.token_expiry = 0
        self.bus_cache = {}  # Format: {query_name: {"timestamp": float, "data": list}}

        # Define TMRT station order and travel times in minutes from Beitun Main
        self.TMRT_STATIONS = [
            "北屯總站", "舊社", "松竹", "四維國小", "文心崇德", "文心中清", 
            "文華高中", "文心櫻花", "市政府", "水安宮", "文心森林公園", 
            "南屯", "豐樂公園", "大慶", "九張犁", "九德", "烏日", "高鐵台中站"
        ]
        self.TMRT_TRAVEL_TIMES = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34]

    def get_token(self):
        # Check if cached token is still valid
        now_ts = time.time()
        if self.access_token and now_ts < self.token_expiry - 300:
            return self.access_token

        url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            print("[TDX Client] Requesting new Access Token...")
            response = requests.post(url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                res_json = response.json()
                self.access_token = res_json.get("access_token")
                expires_in = res_json.get("expires_in", 86400)
                self.token_expiry = now_ts + expires_in
                print(f"[TDX Client] Token successfully updated. Expires in {expires_in} seconds.")
                return self.access_token
            else:
                print(f"[TDX Client] Auth error {response.status_code}: {response.text}")
        except Exception as e:
            print("[TDX Client] Failed to authenticate:", e)
        
        # In case of auth failure, return cached token if available, else None
        return self.access_token

    def get_bus_arrival(self, station_id, station_name):
        # 1. Clean stop name for OData filter
        query_name = station_name.replace("轉乘樞紐", "").replace("捷運", "").replace("公車", "").replace("站", "")
        if not query_name.strip():
            query_name = station_name
            
        # 2. Check 30-second memoization cache
        now_ts = time.time()
        if query_name in self.bus_cache:
            cache_entry = self.bus_cache[query_name]
            if now_ts - cache_entry["timestamp"] < 30:
                print(f"[TDX Cache] Hit cache for bus stop: {query_name}")
                return cache_entry["data"]

        # 3. Call TDX API
        bus_list = []
        token = self.get_token()
        success = False
        
        if token:
            url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Taichung?$filter=contains(StopName/Zh_tw, '{query_name}')&$format=JSON"
            headers = {"Authorization": f"Bearer {token}"}
            try:
                print(f"[TDX API] Fetching bus ETA for: {query_name}")
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Deduplicate and format routes
                    temp_routes = {}
                    for item in data:
                        route_name = item.get("RouteName", {}).get("Zh_tw")
                        est_time = item.get("EstimateTime")
                        
                        if route_name and est_time is not None and est_time >= 0:
                            # Keep the smallest estimate time for each route name
                            if route_name not in temp_routes or est_time < temp_routes[route_name]:
                                temp_routes[route_name] = est_time
                                
                    for route_name, est_time in temp_routes.items():
                        bus_list.append({
                            "RouteName": route_name,
                            "EstimateTime": est_time
                        })
                        
                    # Sort routes by arrival time
                    bus_list.sort(key=lambda x: x["EstimateTime"])
                    success = True
                    print(f"[TDX API] Successfully loaded {len(bus_list)} real routes for {query_name}.")
                elif response.status_code == 429:
                    print(f"[TDX API] Rate limited (429) for stop {query_name}. Transitioning to fallback.")
                else:
                    print(f"[TDX API] Error {response.status_code} for stop {query_name}: {response.text}")
            except Exception as e:
                print(f"[TDX API] Request exception for stop {query_name}:", e)

        # 4. Graceful Fallback / Simulation (if TDX failed or was rate limited)
        if not success:
            print(f"[TDX Fallback] Generating smooth simulated departures for {query_name}.")
            # Using current timestamp to make count-down deterministic and smooth
            now = int(time.time())
            
            # Select simulated routes based on station name hash to make them stable per station
            name_hash = sum(ord(c) for c in query_name)
            sim_routes = []
            if name_hash % 3 == 0:
                sim_routes = [("300", 300), ("301", 480), ("305", 720)]
            elif name_hash % 3 == 1:
                sim_routes = [("151", 360), ("152", 540), ("153", 900)]
            else:
                sim_routes = [("73", 400), ("83", 600), ("324", 800)]
                
            for route_name, interval in sim_routes:
                t_remaining = interval - (now % interval)
                bus_list.append({
                    "RouteName": route_name,
                    "EstimateTime": t_remaining
                })
            bus_list.sort(key=lambda x: x["EstimateTime"])

        # 5. Cache result and return
        self.bus_cache[query_name] = {
            "timestamp": now_ts,
            "data": bus_list
        }
        return bus_list

    def get_mrt_arrival(self, station_id, station_name):
        # 1. Clean station name
        clean_name = station_name.replace("捷運", "").replace("轉乘樞紐", "").replace("站", "")
        
        # 2. Find station index in TMRT list
        idx = -1
        for i, s in enumerate(self.TMRT_STATIONS):
            if clean_name in s or s in clean_name:
                idx = i
                break
        if idx == -1:
            idx = 8  # Default to 市政府
            
        now = datetime.datetime.now()
        current_minute_of_day = now.hour * 60 + now.minute + now.second / 60.0
        
        # 3. Handle non-operating hours (24:00 - 06:00)
        # TMRT last trains depart terminals at 24:00, arriving at center around 00:17, HSR at 00:34
        if now.hour < 6 or (now.hour == 0 and now.minute > 35):
            return [
                {"Destination": "北屯總站", "EstimateTime": 99999},
                {"Destination": "高鐵台中站", "EstimateTime": 99999}
            ]
            
        # 4. Dispatch interval policy
        # Peak/Off-peak (6:00 - 23:00) -> 6 mins frequency
        # Night (23:00 - 24:00) -> 15 mins frequency
        def get_dispatch_times(hour):
            if hour >= 23:
                return [0, 15, 30, 45, 60]
            else:
                return [i * 6 for i in range(11)]
                
        # 5. Calculate Southbound trains (towards HSR, index 17)
        sb_estimates = []
        if idx < 17:
            for h_offset in [-1, 0, 1]:
                target_hour = (now.hour + h_offset) % 24
                if target_hour < 6:
                    continue
                dispatches = get_dispatch_times(target_hour)
                for disp in dispatches:
                    arrival_min = target_hour * 60 + disp + self.TMRT_TRAVEL_TIMES[idx]
                    diff_sec = int((arrival_min - current_minute_of_day) * 60)
                    if diff_sec >= 0:
                        sb_estimates.append(diff_sec)
                        
        # 6. Calculate Northbound trains (towards Beitun, index 0)
        nb_estimates = []
        if idx > 0:
            for h_offset in [-1, 0, 1]:
                target_hour = (now.hour + h_offset) % 24
                if target_hour < 6:
                    continue
                dispatches = get_dispatch_times(target_hour)
                for disp in dispatches:
                    arrival_min = target_hour * 60 + disp + (34 - self.TMRT_TRAVEL_TIMES[idx])
                    diff_sec = int((arrival_min - current_minute_of_day) * 60)
                    if diff_sec >= 0:
                        nb_estimates.append(diff_sec)
                        
        sb_estimates.sort()
        nb_estimates.sort()
        
        # 7. Package results
        res = []
        if nb_estimates and idx > 0:
            res.append({"Destination": "北屯總站", "EstimateTime": nb_estimates[0]})
        if sb_estimates and idx < 17:
            res.append({"Destination": "高鐵台中站", "EstimateTime": sb_estimates[0]})
            
        return res

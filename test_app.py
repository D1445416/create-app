import sys
import os
import json
import importlib.util

# Resolve collision between app/ folder and app.py in root
spec = importlib.util.spec_from_file_location("app_root", "app.py")
app_root = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_root)
app = app_root.app

def run_test():
    with app.test_client() as client:
        payload = {
            "segments": [
                {
                    "type": "bus",
                    "route_id": "300",
                    "distance_km": 12.5,
                    "start_stop": "A",
                    "end_stop": "B"
                },
                {
                    "type": "bus",
                    "route_id": "301",
                    "distance_km": 8.0,
                    "start_stop": "B",
                    "end_stop": "C"
                },
                {
                    "type": "mrt",
                    "start_station": "103",
                    "end_station": "110"
                },
                {
                    "type": "youbike",
                    "minutes": 15,
                    "distance_km": 2.5
                }
            ]
        }
        
        response = client.post('/api/v1/calculate_trip', json=payload)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.get_json(), indent=2, ensure_ascii=False))

        print("\n--- Testing Web Page Rendering ---")
        # Test index page
        res_idx = client.get('/')
        print(f"Index Page Status: {res_idx.status_code}")
        if res_idx.status_code != 200:
            print("Index Page Error Output:")
            print(res_idx.data.decode('utf-8')[:1000])

        # Test favorites page
        res_fav = client.get('/favorites')
        print(f"Favorites Page Status: {res_fav.status_code}")
        if res_fav.status_code != 200:
            print("Favorites Page Error Output:")
            print(res_fav.data.decode('utf-8')[:1000])

if __name__ == '__main__':
    run_test()

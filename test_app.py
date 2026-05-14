import sys
import json
from app import app

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

if __name__ == '__main__':
    run_test()

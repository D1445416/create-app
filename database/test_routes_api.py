import requests
import json

def test_routes():
    base_url = "http://127.0.0.1:5000"
    
    print("Testing GET /api/v1/route_plans...")
    # 市政府站轉乘樞紐 (HUB_01) to 台中車站轉乘樞紐 (HUB_02)
    url = f"{base_url}/api/v1/route_plans?start=HUB_01&end=HUB_02"
    try:
        res = requests.get(url)
        print("Status:", res.status_code)
        if res.status_code == 200:
            data = res.json()
            print("Successfully retrieved route plans!")
            print("Plans generated:")
            for p in data["plans"]:
                print(f"- {p['name']}: {p['total_minutes']} mins, NT$ {p['total_fare']}")
                print(f"  Path coordinates count: {len(p['path'])}")
        else:
            print("Error:", res.text)
    except Exception as e:
        print("Failed to request route_plans:", e)

if __name__ == "__main__":
    test_routes()

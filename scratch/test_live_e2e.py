import urllib.request
import json

def test():
    # 1. Frontend check
    res = urllib.request.urlopen("http://localhost:3000")
    print("Frontend status:", res.status)

    # 2. Backend health check
    res2 = urllib.request.urlopen("http://127.0.0.1:8001/health")
    print("Backend Health status:", res2.status, res2.read().decode())

    # 3. Batch image search check
    req = urllib.request.Request(
        "http://127.0.0.1:8001/api/v1/images/batch-search",
        data=json.dumps({
            "dishes": [
                {"dish_id": "d1", "dish_name": "Tonkotsu Ramen", "original_script": "豚骨ラーメン", "cuisine": "Japanese"},
                {"dish_id": "d2", "dish_name": "Mango Smoothie", "original_script": "망고 스무디", "cuisine": "Korean"},
                {"dish_id": "d3", "dish_name": "Butter Chicken", "original_script": "बटर चिकन", "cuisine": "Indian"},
                {"dish_id": "d4", "dish_name": "Margherita Pizza", "original_script": "Pizza Margherita", "cuisine": "Italian"},
                {"dish_id": "d5", "dish_name": "Unknown Mystery Dish", "original_script": "謎の料理", "cuisine": "Unknown"}
            ]
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res3 = urllib.request.urlopen(req)
    print("Batch Image Search HTTP status:", res3.status)
    data = json.loads(res3.read().decode())
    for dish_id, info in data["results"].items():
        print(f"Dish {dish_id}: alt='{info['alt_text']}' status={info['status']} fallback={info['is_fallback']} src={info['source']}")

if __name__ == "__main__":
    test()

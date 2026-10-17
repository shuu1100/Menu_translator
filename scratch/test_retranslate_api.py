import json
import httpx
import time
import sys

sys.stdout.reconfigure(encoding="utf-8")

dish_test = {
    "dish_id": "test_1",
    "reading_order": 1,
    "bounding_box": {"ymin": 0.0, "xmin": 0.0, "ymax": 1.0, "xmax": 1.0},
    "original_text": "Grilled Chicken Platter",
    "original_name": "Grilled Chicken Platter",
    "original_description": "The grilled chicken is served with rice and fresh vegetables.",
    "translated_title": "Grilled Chicken Platter",
    "translated_name": "Grilled Chicken Platter",
    "culinary_description": "The grilled chicken is served with rice and fresh vegetables.",
    "translated_description": "The grilled chicken is served with rice and fresh vegetables.",
    "price": "$14.50",
}

target_languages = [
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("hi", "Hindi"),
    ("ja", "Japanese"),
    ("it", "Italian"),
    ("ar", "Arabic"),
    ("ru", "Russian"),
]

print("=== TESTING REAL MULTILINGUAL TRANSLATION VIA FASTAPI RETRANSLATE ENDPOINT ===")

with httpx.Client(timeout=45.0) as client:
    for code, name in target_languages:
        t0 = time.time()
        payload = {
            "dishes": [dish_test],
            "target_language": code,
        }
        res = client.post("http://127.0.0.1:8001/api/v1/menus/retranslate", json=payload)
        elapsed = time.time() - t0
        if res.status_code == 200:
            data = res.json()
            d = data["dishes"][0]
            print(f"[{code}] {name} ({elapsed:.2f}s):")
            print(f"  Title: {d.get('translated_title')} | Name: {d.get('translated_name')}")
            print(f"  Desc:  {d.get('translated_description')}")
        else:
            print(f"[{code}] {name} FAILED HTTP {res.status_code}: {res.text}")

print("=== END TEST ===")

import json
import httpx
import sys

sys.stdout.reconfigure(encoding="utf-8")

dish_no_desc = {
    "dish_id": "test_nodesc",
    "reading_order": 2,
    "bounding_box": {"ymin": 0.0, "xmin": 0.0, "ymax": 1.0, "xmax": 1.0},
    "original_text": "Espresso Solo",
    "original_name": "Espresso Solo",
    "original_description": None,
    "translated_title": "Espresso Solo",
    "translated_name": "Espresso Solo",
    "culinary_description": None,
    "translated_description": None,
    "price": "$3.00",
}

with httpx.Client(timeout=45.0) as client:
    res = client.post(
        "http://127.0.0.1:8001/api/v1/menus/retranslate",
        json={"dishes": [dish_no_desc], "target_language": "es"},
    )
    data = res.json()
    d = data["dishes"][0]
    print("ESPRESSO SOLO in Spanish:")
    print("  Title:", d.get("translated_title"))
    print("  Name:", d.get("translated_name"))
    print("  Desc:", d.get("translated_description"))
    assert d.get("translated_description") is None, "Description should remain None when no printed description existed!"
    print("PASS: Missing description honestly reported as None!")

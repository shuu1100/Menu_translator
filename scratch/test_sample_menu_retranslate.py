import json
import httpx
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Sample dishes from Korean BBQ
korean_dishes = [
    {
        "dish_id": "kbbq-1",
        "reading_order": 1,
        "bounding_box": {"ymin": 0.22, "xmin": 0.08, "ymax": 0.35, "xmax": 0.92},
        "original_text": "통삼겹살",
        "original_name": "통삼겹살",
        "original_description": "두툼하게 썰어 숯불에 구워낸 국내산 프리미엄 암퇘지 삼겹살",
        "translated_title": "Thick-Cut Pork Belly",
        "translated_name": "Thick-Cut Pork Belly",
        "culinary_description": "Thick-cut premium pork belly grilled over natural charcoal embers",
        "translated_description": "Thick-cut premium pork belly grilled over natural charcoal embers",
        "price": "₩18,000",
        "representative_image": {
            "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947",
            "source": "unsplash",
            "alt_text": "Thick-cut pork belly",
            "photographer": "K BBQ Chef",
        }
    },
    {
        "dish_id": "kbbq-2",
        "reading_order": 2,
        "bounding_box": {"ymin": 0.37, "xmin": 0.08, "ymax": 0.50, "xmax": 0.92},
        "original_text": "한우 차돌박이",
        "original_name": "한우 차돌박이",
        "original_description": "고소하고 부드러운 최상급 한우 1++ 차돌박이 얇게 저민 구이",
        "translated_title": "Hanwoo Beef Brisket",
        "translated_name": "Hanwoo Beef Brisket",
        "culinary_description": "Thinly shaved prime Korean native beef brisket with rich marbling",
        "translated_description": "Thinly shaved prime Korean native beef brisket with rich marbling",
        "price": "₩26,000",
        "representative_image": {
            "image_url": "https://images.unsplash.com/photo-1558030006-450675393462",
            "source": "unsplash",
            "alt_text": "Hanwoo beef brisket",
            "photographer": "Beef Master",
        }
    }
]

with httpx.Client(timeout=45.0) as client:
    # 1. Retranslate Korean BBQ dishes to Spanish
    res_es = client.post(
        "http://127.0.0.1:8001/api/v1/menus/retranslate",
        json={"dishes": korean_dishes, "target_language": "es"},
    )
    assert res_es.status_code == 200, f"Error: {res_es.text}"
    dishes_es = res_es.json()["dishes"]
    print("=== SPANISH RETRANSLATION ===")
    for d in dishes_es:
        print(f"Dish: {d['original_name']} -> {d['translated_name']}")
        print(f"Desc: {d['translated_description']}")
        print(f"Image: {d['representative_image']['image_url']}\n")

    # 2. Retranslate to Japanese
    res_ja = client.post(
        "http://127.0.0.1:8001/api/v1/menus/retranslate",
        json={"dishes": korean_dishes, "target_language": "ja"},
    )
    assert res_ja.status_code == 200, f"Error: {res_ja.text}"
    dishes_ja = res_ja.json()["dishes"]
    print("=== JAPANESE RETRANSLATION ===")
    for d in dishes_ja:
        print(f"Dish: {d['original_name']} -> {d['translated_name']}")
        print(f"Desc: {d['translated_description']}")
        print(f"Image: {d['representative_image']['image_url']}\n")

print("SUCCESS: Demo menu retranslation works flawlessly in both Spanish and Japanese!")

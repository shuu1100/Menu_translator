import json
import httpx
import sys

sys.stdout.reconfigure(encoding="utf-8")

dish_with_img = {
    "dish_id": "dish_101",
    "reading_order": 1,
    "bounding_box": {"ymin": 0.1, "xmin": 0.1, "ymax": 0.5, "xmax": 0.9},
    "original_text": "닭갈비",
    "original_name": "닭갈비",
    "original_description": "매콤한 양념에 볶은 닭고기와 신선한 야채",
    "translated_title": "Spicy Stir-fried Chicken",
    "translated_name": "Spicy Stir-fried Chicken",
    "culinary_description": "Chicken stir-fried with spicy sauce and fresh vegetables",
    "translated_description": "Chicken stir-fried with spicy sauce and fresh vegetables",
    "price": "₩14,000",
    "representative_image": {
        "image_url": "https://images.unsplash.com/photo-dakgalbi-test",
        "thumbnail_url": "https://images.unsplash.com/photo-dakgalbi-thumb",
        "alt_text": "Delicious spicy stir-fried chicken",
        "photographer": "Chef Kim",
        "photographer_url": "https://unsplash.com/@chefkim",
        "source_url": "https://unsplash.com/photos/123",
        "source": "unsplash",
        "relevance_score": 0.92,
    },
}

with httpx.Client(timeout=45.0) as client:
    # 1. Retranslate to Spanish
    res_es = client.post(
        "http://127.0.0.1:8001/api/v1/menus/retranslate",
        json={"dishes": [dish_with_img], "target_language": "es"},
    )
    assert res_es.status_code == 200, f"Spanish failed: {res_es.text}"
    dish_es = res_es.json()["dishes"][0]
    
    print("--- Retranslation to Spanish ---")
    print("Original text:", dish_es["original_text"])
    print("Spanish name:", dish_es["translated_name"])
    print("Spanish desc:", dish_es["translated_description"])
    print("Image preserved:", dish_es["representative_image"]["image_url"] == "https://images.unsplash.com/photo-dakgalbi-test")
    assert dish_es["original_text"] == "닭갈비", "Original OCR text was mutated!"
    assert dish_es["representative_image"] is not None, "Image was lost!"
    assert dish_es["representative_image"]["photographer"] == "Chef Kim"
    assert "pollo" in dish_es["translated_description"].lower()

    # 2. Retranslate to Japanese
    res_ja = client.post(
        "http://127.0.0.1:8001/api/v1/menus/retranslate",
        json={"dishes": [dish_es], "target_language": "ja"},
    )
    assert res_ja.status_code == 200, f"Japanese failed: {res_ja.text}"
    dish_ja = res_ja.json()["dishes"][0]

    print("--- Retranslation to Japanese ---")
    print("Original text:", dish_ja["original_text"])
    print("Japanese name:", dish_ja["translated_name"])
    print("Japanese desc:", dish_ja["translated_description"])
    print("Image preserved:", dish_ja["representative_image"]["image_url"] == "https://images.unsplash.com/photo-dakgalbi-test")
    assert dish_ja["original_text"] == "닭갈비", "Original OCR text was mutated!"
    assert dish_ja["representative_image"] is not None, "Image was lost!"

print("ALL TESTS PASSED: True multilingual translation with image & source preservation verified!")

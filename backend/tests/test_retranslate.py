import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_retranslate_endpoint():
    payload = {
        "dishes": [
            {
                "dish_id": "test_01",
                "reading_order": 1,
                "section": "BEVERAGES",
                "bounding_box": {"xmin": 0.1, "ymin": 0.1, "xmax": 0.5, "ymax": 0.2},
                "original_text": "블랙 밀크티",
                "translated_title": "Black Milk Tea",
                "price": "4,500",
                "currency": "₩",
                "evidence_status": "unverified",
                "key_ingredients": [],
                "allergen_warnings": [],
                "dietary_compatibility": {"user_conflicts": []}
            },
            {
                "dish_id": "test_02",
                "reading_order": 2,
                "section": "BEVERAGES",
                "bounding_box": {"xmin": 0.1, "ymin": 0.25, "xmax": 0.5, "ymax": 0.35},
                "original_text": "아이스 블랙 스무디",
                "translated_title": "Iced Black Smoothie",
                "price": "5,300",
                "currency": "₩",
                "evidence_status": "unverified",
                "key_ingredients": [],
                "allergen_warnings": [],
                "dietary_compatibility": {"user_conflicts": []}
            }
        ],
        "target_language": "en"
    }

    response = client.post("/api/v1/menus/retranslate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["target_language"] == "en"
    assert len(data["dishes"]) == 2
    assert "Black Milk Tea" in data["dishes"][0]["translated_title"]
    assert "Smoothie" in data["dishes"][1]["translated_title"]
    assert data["dishes"][0]["phonetic_transcription"] is not None

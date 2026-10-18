import io
import time
import httpx
from PIL import Image

IMAGE_PATH = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

print("1. Opening image and testing /api/v1/menus/analyze with rotation=90...")
with open(IMAGE_PATH, "rb") as f:
    files = {"file": ("menu.jpg", f.read(), "image/jpeg")}

data = {
    "target_language": "en",
    "rotation": 90,
}

t0 = time.time()
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://127.0.0.1:8001/api/v1/menus/analyze", files=files, data=data)
    elapsed = time.time() - t0
    print(f"Status: {res.status_code} in {elapsed:.1f}s")
    if res.status_code == 200:
        result = res.json()
        menu = result.get("menu", {})
        items = menu.get("items", [])
        print(f"Detected language: {menu.get('source_language')}")
        print(f"Total dishes extracted: {len(items)}")
        for idx, item in enumerate(items[:10]):
            sec = item.get("section") or "General"
            orig = item.get("original_name")
            trans = item.get("translated_name")
            price = item.get("price_display")
            roman = item.get("phonetic_transcription")
            print(f"  [{sec}] {orig} ({roman}) -> {trans} | {price}")
    else:
        print("Error body:", res.text[:500])

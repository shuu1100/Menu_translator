import sys
sys.path.insert(0, ".")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
import time
import base64
import json
from PIL import Image

image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(image_path, "rb") as f:
    img = Image.open(f)
    rotated = img.transpose(Image.Transpose.ROTATE_270)

from backend.app.services.image_processor import ImageProcessor
preprocessed = ImageProcessor.preprocess_for_vlm(rotated, max_dimension=1024)
b64_image = base64.b64encode(preprocessed.image_bytes).decode("utf-8")

prompt = """You are a precise multilingual restaurant menu reader.
Read all unique drinks and dishes from this Korean menu. Extract each distinct item into JSON:
{
  "source_language": "ko",
  "items": [
    {"original_name": "Korean dish/drink name as printed", "section": "Category name (e.g. ORIGINAL TEA, MILK TEA, SMOOTHIE, FRUIT TEA, COFFEE)", "price_display": "Price string (e.g. L 4.5 / J 5.6, 4,500)"}
  ]
}
RULES:
1. Scan columns left to right. Extract each unique drink and price.
2. Do not repeat items.
3. Output valid JSON only."""

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": prompt, "images": [b64_image]},
        {"role": "assistant", "content": "{\n  \"source_language\": \"ko\",\n  \"items\": [\n"}
    ],
    "keep_alive": "30m",
    "options": {
        "temperature": 0.1,
        "top_p": 0.9,
        "repeat_penalty": 1.18,
        "num_ctx": 3072,
        "num_predict": 1500,
    },
    "stream": False,
}

print("Running test for distinct items...")
t0 = time.perf_counter()
with httpx.Client(timeout=120.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.perf_counter() - t0
    data = res.json()
    raw = data.get("message", {}).get("content", "")
    print(f"Elapsed: {elapsed:.2f}s | Eval count: {data.get('eval_count')} | Done: {data.get('done_reason')}")
    
    full_text = "{\n  \"source_language\": \"ko\",\n  \"items\": [\n" + raw
    from backend.app.services.vision.json_parser import ModelJsonParser
    lang, items, warnings = ModelJsonParser.parse_and_validate(full_text, rotated.width, rotated.height)
    print(f"\nExtracted: {len(items)} items from '{lang}' in {elapsed:.2f}s!")
    for idx, itm in enumerate(items[:20]):
        print(f"  #{idx+1}: [{itm.section}] '{itm.original_name}' - {itm.price_display}")

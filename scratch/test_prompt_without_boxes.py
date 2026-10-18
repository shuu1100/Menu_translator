import sys
sys.path.insert(0, ".")
import httpx
import time
import base64
from PIL import Image

image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(image_path, "rb") as f:
    img = Image.open(f)
    rotated = img.transpose(Image.Transpose.ROTATE_270)

from backend.app.services.image_processor import ImageProcessor
preprocessed = ImageProcessor.preprocess_for_vlm(rotated, max_dimension=1024)
b64_image = base64.b64encode(preprocessed.image_bytes).decode("utf-8")

prompt = """You are a fast, factual menu OCR engine.
Read the Korean restaurant menu image and extract all dishes, beverages, sections, and prices into valid JSON:
{
  "source_language": "ko",
  "items": [
    {
      "reading_order": 1,
      "section": "Section/Category title (e.g. 'ORIGINAL TEA', 'MILK TEA', 'SMOOTHIE')",
      "original_name": "Dish or drink name in Korean",
      "subtitle_or_description": null,
      "price_display": "Price string (e.g. '4.5 / 5.6', '4,500', 'L 4.5 J 5.6')",
      "currency": "₩"
    }
  ]
}
RULES:
1. Output valid JSON only. Do not output conversational commentary.
2. If an item has no description, set "subtitle_or_description": null.
3. Clean section titles: do not extract blog watermarks, stamps, or URLs.
"""

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": prompt, "images": [b64_image]}
    ],
    "format": "json",
    "keep_alive": "30m",
    "options": {
        "temperature": 0.1,
        "top_p": 0.9,
        "num_ctx": 4096,
        "num_predict": 2048,
    },
    "stream": False,
}

print("Running test without box_2d on rotated Gong Cha menu...")
t0 = time.perf_counter()
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.perf_counter() - t0
    print(f"Status: {res.status_code}, Elapsed: {elapsed:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print(f"Done reason: {data.get('done_reason')}")
    print(f"Eval count: {data.get('eval_count')}")
    print(f"Content len: {len(content)}, Thinking len: {len(thinking)}")
    
    from backend.app.services.vision.json_parser import ModelJsonParser
    raw_to_parse = content if (content and "{" in content) else thinking
    try:
        lang, items, warnings = ModelJsonParser.parse_and_validate(raw_to_parse, rotated.width, rotated.height)
        print(f"SUCCESS: Extracted {len(items)} items from '{lang}' menu!")
        for idx, itm in enumerate(items[:10]):
            print(f"  #{idx+1}: [{itm.section}] {itm.original_name} - {itm.price_display}")
    except Exception as e:
        print(f"Failed to parse: {e}")
        if content:
            print("Content sample:", content[:300])
        if thinking:
            print("Thinking sample:", thinking[:300])

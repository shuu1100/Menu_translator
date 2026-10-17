import sys
sys.path.insert(0, ".")
import httpx
import time
import base64
from PIL import Image

image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(image_path, "rb") as f:
    img = Image.open(f)
    # Correct orientation: rotate 90 deg clockwise (ROTATE_270)
    rotated = img.transpose(Image.Transpose.ROTATE_270)
    
from backend.app.services.image_processor import ImageProcessor
preprocessed = ImageProcessor.preprocess_for_vlm(rotated, max_dimension=1024)
b64_image = base64.b64encode(preprocessed.image_bytes).decode("utf-8")

prompt = """You are a fast, factual restaurant menu extraction engine.
Extract all menu categories, drinks, and prices from this Korean Gong cha menu into valid JSON:
{
  "source_language": "ko",
  "items": [
    {
      "reading_order": 1,
      "section": "Category name as printed (e.g. 'ORIGINAL TEA', 'MILK TEA')",
      "original_name": "Korean drink name (e.g. '블랙 밀크티')",
      "price_display": "Price as printed (e.g. '4.5 / 5.6' or '4,500')",
      "subtitle_or_description": null
    }
  ]
}
Output valid JSON only. Do not output conversational commentary.
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
        "num_ctx": 3584,
        "num_predict": 1200,
    },
    "stream": False,
}

print("Running test on rotated Gong Cha menu with format=json, num_predict=1200, num_ctx=3584...")
t0 = time.perf_counter()
with httpx.Client(timeout=150.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.perf_counter() - t0
    print(f"Status: {res.status_code}, Elapsed: {elapsed:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print(f"Content len: {len(content)}, Thinking len: {len(thinking)}")
    print(f"Done reason: {data.get('done_reason')}")
    print(f"Eval count: {data.get('eval_count')}")
    
    from backend.app.services.vision.json_parser import ModelJsonParser
    raw_to_parse = content if content.strip() else thinking
    try:
        lang, items, warnings = ModelJsonParser.parse_and_validate(raw_to_parse, rotated.width, rotated.height)
        print(f"SUCCESS! Extracted {len(items)} items from '{lang}' menu!")
        for idx, itm in enumerate(items[:8]):
            print(f" #{idx+1} [{itm.section}] {itm.original_name} - {itm.price_display}")
    except Exception as e:
        print(f"Parsing failed: {e}")
        print("Raw head (first 500 chars):", repr(raw_to_parse[:500]))
        print("Raw tail (last 500 chars):", repr(raw_to_parse[-500:]))

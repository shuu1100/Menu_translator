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

prompt = """Read this restaurant menu image. Extract each dish/drink item into a JSON array:
{
  "source_language": "ko",
  "items": [
    {"original_name": "Korean item name", "section": "Category header", "price_display": "price"}
  ]
}
RULES:
1. Extract every item under each category.
2. Output JSON only. Do not output markdown codeblocks."""

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": prompt, "images": [b64_image]},
        {"role": "assistant", "content": "{\n  \"source_language\": \"ko\",\n  \"items\": [\n"}
    ],
    "keep_alive": "30m",
    "options": {
        "temperature": 0.1,
        "num_ctx": 3072,
        "num_predict": 2048,
    },
    "stream": False,
}

print("Running test with lean schema and assistant prefill...")
t0 = time.perf_counter()
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.perf_counter() - t0
    data = res.json()
    raw = data.get("message", {}).get("content", "")
    th = data.get("message", {}).get("thinking", "")
    print(f"Elapsed: {elapsed:.2f}s | Eval count: {data.get('eval_count')} | Done: {data.get('done_reason')}")
    print(f"Raw len: {len(raw)}, Th len: {len(th)}")
    
    full_text = "{\n  \"source_language\": \"ko\",\n  \"items\": [\n" + raw
    with open("scratch/lean_output.json", "w", encoding="utf-8") as f:
        f.write(full_text)
    
    from backend.app.services.vision.json_parser import ModelJsonParser
    lang, items, warnings = ModelJsonParser.parse_and_validate(full_text, rotated.width, rotated.height)
    print(f"Extracted: {len(items)} items from '{lang}' in {elapsed:.2f}s!")
    for idx, itm in enumerate(items[:10]):
        print(f"  #{idx+1}: [{itm.section}] '{itm.original_name}' - {itm.price_display}")

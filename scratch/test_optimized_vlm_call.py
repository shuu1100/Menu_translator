import sys
sys.path.insert(0, ".")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
import time
import base64
from PIL import Image

image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(image_path, "rb") as f:
    img = Image.open(f)
    rotated = img.transpose(Image.Transpose.ROTATE_270)

from backend.app.services.image_processor import ImageProcessor
preprocessed = ImageProcessor.preprocess_for_vlm(rotated, max_dimension=960)
b64_image = base64.b64encode(preprocessed.image_bytes).decode("utf-8")

# Highly structured, concise prompt that guides the model directly to JSON
user_prompt = """Extract all dishes, drinks, categories, and prices from this restaurant menu into JSON:
{
  "source_language": "ko",
  "items": [
    {
      "reading_order": 1,
      "section": "Category name (e.g. ORIGINAL TEA, MILK TEA, SMOOTHIE)",
      "original_name": "Dish/beverage name in Korean",
      "subtitle_or_description": null,
      "price_display": "Price as printed (e.g. 4.5 / 5.6)",
      "currency": "₩"
    }
  ]
}
RULES: Output valid JSON only. Do not output blog watermarks, stamps, or markdown commentary."""

# Use assistant turn prefill to force zero thinking
payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {
            "role": "user",
            "content": user_prompt,
            "images": [b64_image],
        },
        {
            "role": "assistant",
            "content": "{\n  \"source_language\": \"ko\",\n  \"items\": [",
        }
    ],
    "keep_alive": "30m",
    "options": {
        "temperature": 0.1,
        "top_p": 0.9,
        "num_ctx": 3072,     # 100% GPU resident on 8GB RTX 4060
        "num_predict": 1500, # Bounded output
    },
    "stream": False,
}

print("Running optimized VLM inference test...")
t0 = time.perf_counter()
with httpx.Client(timeout=120.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.perf_counter() - t0
    print(f"Status: {res.status_code}, Elapsed: {elapsed:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    raw_content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print(f"Done reason: {data.get('done_reason')}")
    print(f"Eval tokens: {data.get('eval_count')} in {data.get('eval_duration', 0)/1e9:.2f}s")
    print(f"Prompt tokens: {data.get('prompt_eval_count')} in {data.get('prompt_eval_duration', 0)/1e9:.2f}s")
    print(f"Speed: {data.get('eval_count', 0) / (data.get('eval_duration', 1)/1e9):.1f} tok/s")
    print(f"Thinking length: {len(thinking)}, Content length: {len(raw_content)}")

    # Combine prefill with generated content
    full_json = "{\n  \"source_language\": \"ko\",\n  \"items\": [" + raw_content
    from backend.app.services.vision.json_parser import ModelJsonParser
    lang, items, warnings = ModelJsonParser.parse_and_validate(full_json, rotated.width, rotated.height)
    print(f"\nSUCCESS! Extracted {len(items)} items from '{lang}' menu in {elapsed:.2f}s!")
    for idx, itm in enumerate(items[:15]):
        print(f"  #{idx+1}: [{itm.section}] '{itm.original_name}' | Price: {itm.price_display}")

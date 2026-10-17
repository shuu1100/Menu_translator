import sys
sys.path.insert(0, ".")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
import base64
from PIL import Image
from backend.app.services.image_processor import ImageProcessor
from backend.app.services.vision.prompts import MENU_EXTRACTION_SYSTEM_PROMPT, MENU_EXTRACTION_USER_PROMPT
from backend.app.services.vision.json_parser import ModelJsonParser
import httpx
import time

image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"
with open(image_path, "rb") as f:
    img = Image.open(f)
    rotated = img.transpose(Image.Transpose.ROTATE_270)

pre = ImageProcessor.preprocess_for_vlm(rotated, max_dimension=1024)
b64_image = base64.b64encode(pre.image_bytes).decode("utf-8")

user_prompt = """Extract all dish and beverage items from this menu image into valid JSON:
{
  "source_language": "ko",
  "items": [
    {"original_name": "Item name as printed", "section": "Category name", "price_display": "Price"}
  ]
}
RULES:
1. Extract verbatim original names and prices across all categories.
2. Do not invent items or repeat identical items.
3. Output JSON only without markdown or commentary."""
prefill = '{\n  "source_language": "ko",\n  "items": [\n'
payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": user_prompt, "images": [b64_image]},
        {"role": "assistant", "content": prefill}
    ],
    "keep_alive": "30m",
    "options": {
        "temperature": 0.1,
        "top_p": 0.9,
        "repeat_penalty": 1.15,
        "num_ctx": 3584,
        "num_predict": 750
    },
    "stream": False
}

print("Sending request with assistant prefill...")
t0 = time.perf_counter()
with httpx.Client(timeout=120.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    t1 = time.perf_counter()
    d = res.json()
    msg = d.get("message", {})
    c = msg.get("content", "")
    th = msg.get("thinking", "")
    print(f"Duration: {t1-t0:.2f}s | Eval count: {d.get('eval_count')} | Done: {d.get('done_reason')}")
    print(f"Content len: {len(c)} | Thinking len: {len(th)}")
    full_output = prefill + c
    lang, items, warnings = ModelJsonParser.parse_and_validate(full_output, pre.original_width, pre.original_height)
    print(f"PARSED SUCCESSFULLY: {len(items)} items, language: {lang}")
    for it in items[:10]:
        print(f"  - {it.original_name} [{it.section}] -> {it.price_display}")

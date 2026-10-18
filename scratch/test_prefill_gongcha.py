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
    # The menu photo is oriented 90 degrees clockwise (ROTATE_270 brings it upright)
    rotated = img.transpose(Image.Transpose.ROTATE_270)

from backend.app.services.image_processor import ImageProcessor
preprocessed = ImageProcessor.preprocess_for_vlm(rotated, max_dimension=1024)
b64_image = base64.b64encode(preprocessed.image_bytes).decode("utf-8")

from backend.app.services.vision.prompts import (
    MENU_EXTRACTION_SYSTEM_PROMPT,
    MENU_EXTRACTION_USER_PROMPT,
)

user_prompt = f"{MENU_EXTRACTION_SYSTEM_PROMPT}\n\n{MENU_EXTRACTION_USER_PROMPT}"

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
            "content": "</think>\n{\n  \"source_language\": \"ko\",\n  \"items\": [",
        }
    ],
    "keep_alive": "30m",
    "options": {
        "temperature": 0.1,
        "top_p": 0.9,
        "num_ctx": 4096,
        "num_predict": 1500,
    },
    "stream": False,
}

print("Testing Korean Gong cha extraction with assistant prefill (zero thinking delay)...")
t0 = time.perf_counter()
with httpx.Client(timeout=120.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.perf_counter() - t0
    print(f"Status: {res.status_code}, Elapsed: {elapsed:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    done_reason = data.get("done_reason")
    eval_count = data.get("eval_count")
    prompt_eval_count = data.get("prompt_eval_count")
    prompt_eval_duration = data.get("prompt_eval_duration", 0) / 1e9
    eval_duration = data.get("eval_duration", 0) / 1e9

    print(f"Done reason: {done_reason}")
    print(f"Prompt eval tokens: {prompt_eval_count} in {prompt_eval_duration:.2f}s")
    print(f"Eval tokens: {eval_count} in {eval_duration:.2f}s (Speed: {eval_count/eval_duration if eval_duration else 0:.1f} tok/s)")
    print(f"Thinking length: {len(thinking)}, Content length: {len(content)}")

    # Reconstruct prefilled prefix
    full_output = '{\n  "source_language": "ko",\n  "items": [' + content

    from backend.app.services.vision.json_parser import ModelJsonParser
    lang, items, warnings = ModelJsonParser.parse_and_validate(full_output, rotated.width, rotated.height)
    print(f"\n--- SUCCESS! Extracted {len(items)} items from '{lang}' menu! ---")
    for idx, itm in enumerate(items[:15]):
        print(f" #{idx+1} [{itm.section}] {itm.original_name} - {itm.price_display}")

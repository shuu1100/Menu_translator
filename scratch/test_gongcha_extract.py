import sys
sys.path.insert(0, ".")
import httpx
import base64
import json
import time

from backend.app.services.image_processor import ImageProcessor
from backend.app.services.vision.prompts import (
    MENU_EXTRACTION_SYSTEM_PROMPT,
    MENU_EXTRACTION_USER_PROMPT,
)
from backend.app.services.vision.json_parser import ModelJsonParser

image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"
with open(image_path, "rb") as f:
    raw_bytes = f.read()

t_start = time.perf_counter()
t0 = time.perf_counter()
pil_img = ImageProcessor.validate_and_decode(raw_bytes)
t_decode = time.perf_counter() - t0

t0 = time.perf_counter()
preprocessed = ImageProcessor.preprocess_for_vlm(pil_img, max_dimension=1024)
b64_image = base64.b64encode(preprocessed.image_bytes).decode("utf-8")
t_preprocess = time.perf_counter() - t0

user_prompt = f"{MENU_EXTRACTION_SYSTEM_PROMPT}\n\n{MENU_EXTRACTION_USER_PROMPT}"

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {
            "role": "user",
            "content": user_prompt,
            "images": [b64_image],
        }
    ],
    "keep_alive": "30m",
    "options": {
        "temperature": 0.1,
        "top_p": 0.9,
        "num_ctx": 4096,
        "num_predict": 2048,
    },
    "stream": False,
}

print(f"1. Decode: {t_decode*1000:.1f}ms")
print(f"2. Preprocess: {t_preprocess*1000:.1f}ms")
print("Calling Ollama with num_predict=2048, num_ctx=4096, keep_alive=30m...")
t0 = time.perf_counter()
with httpx.Client(timeout=300.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    t_inference = time.perf_counter() - t0
    print(f"3. Inference status: {res.status_code}, elapsed: {t_inference:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    done_reason = data.get("done_reason")
    eval_count = data.get("eval_count")
    prompt_eval_count = data.get("prompt_eval_count")
    print(f"Done reason: {done_reason}, Prompt eval tokens: {prompt_eval_count}, Eval tokens: {eval_count}")
    print(f"Content len: {len(content)}, Thinking len: {len(thinking)}")

    t0 = time.perf_counter()
    raw_to_parse = content
    if not raw_to_parse or not raw_to_parse.strip() or ("{" not in raw_to_parse and "[" not in raw_to_parse):
        if thinking and ("{" in thinking or "items" in thinking):
            raw_to_parse = ModelJsonParser.clean_raw_output(thinking)

    source_lang, items, warnings = ModelJsonParser.parse_and_validate(
        raw_output=raw_to_parse,
        orig_width=preprocessed.original_width,
        orig_height=preprocessed.original_height,
    )
    t_parse = time.perf_counter() - t0
    print(f"4. Parsing: {t_parse*1000:.1f}ms -> Extracted {len(items)} items from '{source_lang}' menu")
    print(f"Total time so far: {time.perf_counter() - t_start:.2f}s")
    for i in items[:5]:
        print(f"  Item: {i.original_name} | Price: {i.price_display} | Section: {i.section}")

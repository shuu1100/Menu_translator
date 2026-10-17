import sys
sys.path.insert(0, ".")
import httpx
import time
import base64

image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(image_path, "rb") as f:
    img_bytes = f.read()

from backend.app.services.image_processor import ImageProcessor
pil_img = ImageProcessor.validate_and_decode(img_bytes)
preprocessed = ImageProcessor.preprocess_for_vlm(pil_img, max_dimension=1024)
b64_image = base64.b64encode(preprocessed.image_bytes).decode("utf-8")

from backend.app.services.vision.prompts import (
    MENU_EXTRACTION_SYSTEM_PROMPT,
    MENU_EXTRACTION_USER_PROMPT,
)

# A clean, direct instruction prompt
prompt = f"{MENU_EXTRACTION_SYSTEM_PROMPT}\n\n{MENU_EXTRACTION_USER_PROMPT}"

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {
            "role": "user",
            "content": prompt,
            "images": [b64_image],
        }
    ],
    "format": "json",
    "keep_alive": "30m",
    "options": {
        "temperature": 0.1,
        "top_p": 0.9,
        "num_ctx": 3072,      # fits fully in GPU VRAM
        "num_predict": 1024,
    },
    "stream": False,
}

print("Testing visual extraction with num_ctx=3072...")
t0 = time.time()
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.time() - t0
    print(f"Status: {res.status_code}, Total Elapsed: {elapsed:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print(f"Content len: {len(content)}, Thinking len: {len(thinking)}")
    print(f"Done reason: {data.get('done_reason')}")
    print(f"Prompt eval tokens: {data.get('prompt_eval_count')}, eval duration: {data.get('prompt_eval_duration', 0)/1e9:.2f}s")
    print(f"Eval tokens: {data.get('eval_count')}, eval duration: {data.get('eval_duration', 0)/1e9:.2f}s")
    if data.get('eval_count') and data.get('eval_duration'):
        tok_s = data['eval_count'] / (data['eval_duration'] / 1e9)
        print(f"Tokens/sec: {tok_s:.2f}")

    # Check ollama ps
    ps_res = client.get("http://localhost:11434/api/ps").json()
    for m in ps_res.get("models", []):
        print(f"Model: {m.get('name')}, size: {m.get('size')}, size_vram: {m.get('size_vram')}")

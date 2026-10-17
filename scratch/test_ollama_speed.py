import sys
sys.path.insert(0, ".")
import httpx
import time
import base64
from PIL import Image

image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(image_path, "rb") as f:
    img_bytes = f.read()

b64_image = base64.b64encode(img_bytes).decode("utf-8")

from backend.app.services.vision.prompts import (
    MENU_EXTRACTION_SYSTEM_PROMPT,
    MENU_EXTRACTION_USER_PROMPT,
)

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
        "num_ctx": 4096,
        "num_predict": 1200,
    },
    "stream": False,
}

print("Sending extraction request with format=json, keep_alive=30m, num_predict=1200...")
t0 = time.time()
with httpx.Client(timeout=300.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.time() - t0
    print(f"Status: {res.status_code}, Elapsed: {elapsed:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print(f"Content length: {len(content)}")
    print(f"Thinking length: {len(thinking)}")
    print(f"Done reason: {data.get('done_reason')}")
    print(f"Prompt eval count: {data.get('prompt_eval_count')}")
    print(f"Prompt eval duration: {data.get('prompt_eval_duration', 0)/1e9:.2f}s")
    print(f"Eval count: {data.get('eval_count')}")
    print(f"Eval duration: {data.get('eval_duration', 0)/1e9:.2f}s")
    print("Content preview (first 500 chars):")
    print(content[:500])

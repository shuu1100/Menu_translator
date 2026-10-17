import httpx
import time
import base64
import json
from PIL import Image
import io

image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with Image.open(image_path) as img:
    # Rotate 90 deg clockwise to be right side up
    img = img.rotate(-90, expand=True)
    # Resize so max dimension is 960 (preserves text crispness while cutting vision tokens by 30%)
    img.thumbnail((960, 960), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    img_bytes = buf.getvalue()

b64_image = base64.b64encode(img_bytes).decode("utf-8")
print(f"Preprocessed image size: {img.size}, {len(img_bytes)} bytes")

# Test 1: Direct Ollama chat with concise JSON prompt and think disabled
prompt = """Read this restaurant menu image. Extract each dish into JSON:
{"items": [{"name": "original dish name", "price": "price", "section": "category"}]}
Output JSON only. Be concise."""

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": prompt, "images": [b64_image]}
    ],
    "options": {
        "temperature": 0.1,
        "num_ctx": 2560,
        "num_predict": 1200,
    },
    "stream": False,
    "keep_alive": "30m",
}

print("Invoking Ollama qwen3-vl:8b directly...")
t0 = time.time()
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.time() - t0
    print(f"Status: {res.status_code} in {elapsed:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print("eval_count (tokens):", data.get("eval_count"))
    print("eval_duration (s):", data.get("eval_duration", 0) / 1e9)
    print("prompt_eval_count:", data.get("prompt_eval_count"))
    tok_s = data.get("eval_count", 0) / (data.get("eval_duration", 1) / 1e9)
    print(f"Speed: {tok_s:.1f} tokens/s")
    print(f"Content length: {len(content)}, Thinking length: {len(thinking)}")
    print("Output sample (first 400 chars):")
    print(content[:400])

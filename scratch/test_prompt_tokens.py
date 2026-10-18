import base64
import io
import time
import httpx
from PIL import Image

IMAGE_PATH = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(IMAGE_PATH, "rb") as f:
    img = Image.open(f)
    rotated = img.transpose(Image.Transpose.ROTATE_270)
    # resize max dimension 1600 for fast inference
    rotated.thumbnail((1600, 1600))
    buf = io.BytesIO()
    rotated.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

prompt = """Visually extract all menu items, categories/sections, and prices from this menu.
Immediately output ONLY a single RFC 8259 JSON object starting with '{' and ending with '}'.
Do not output any thinking tags, reasoning, or markdown fences.

Required schema:
{
  "source_language": "ko",
  "items": [
    {
      "reading_order": 1,
      "section": "Section name or null",
      "original_name": "Exact dish or drink name as printed",
      "price_display": "Price as printed or null",
      "currency": "₩",
      "box_2d": null
    }
  ]
}
Output JSON:
{"""

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": prompt, "images": [b64]}
    ],
    "options": {
        "temperature": 0.0,
        "num_predict": 4096,
        "num_ctx": 6144
    },
    "stream": False
}

print("Sending request to Ollama with 1600 max dim and direct JSON prompt...")
t0 = time.time()
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    print(f"Status: {res.status_code} in {time.time()-t0:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print("Content len:", len(content))
    print("Thinking len:", len(thinking))
    print("Done reason:", data.get("done_reason"))
    print("Eval count:", data.get("eval_count"))
    if content:
        print("CONTENT SNIPPET:\n", content[:500])
    elif thinking:
        print("THINKING SNIPPET:\n", thinking[:500])

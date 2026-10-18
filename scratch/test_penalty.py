import io
import base64
import httpx
import json
import time
from PIL import Image

path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(path, "rb") as f:
    img = Image.open(f)
    rotated = img.transpose(Image.Transpose.ROTATE_270)
    buf = io.BytesIO()
    rotated.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

prompt = """Extract all dishes, beverages, sections and prices from this menu.
Return ONLY a valid JSON object adhering strictly to:
{
  "source_language": "ko",
  "items": [
    {
      "reading_order": 1,
      "section": "ORIGINAL TEA",
      "original_name": "블랙 밀크티",
      "price_display": "4.5 / 5.6",
      "box_2d": null
    }
  ]
}
Output raw JSON starting with '{' and ending with '}'. Do not use markdown fences. Do not output repetitive commentary.
"""

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": prompt, "images": [b64]}
    ],
    "options": {
        "temperature": 0.2,
        "repeat_penalty": 1.2,
        "num_predict": 2048,
        "num_ctx": 4096
    },
    "stream": False
}

print("Querying Ollama with repeat_penalty=1.2 and temperature=0.2...")
t0 = time.time()
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    print(f"Done in {time.time()-t0:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print(f"Content len: {len(content)}, Thinking len: {len(thinking)}, done_reason: {data.get('done_reason')}")
    if content:
        print("CONTENT:\n", content[:1500])
    else:
        print("THINKING:\n", thinking[:1500])

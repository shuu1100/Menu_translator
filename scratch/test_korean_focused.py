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
    rotated.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

system_msg = """You are a menu extraction AI. Extract the beverage and food items from the menu into JSON.
CRITICAL: Keep your thinking brief and concise. Do NOT analyze customization guides (ice/sugar/sweetness grades).
Output ONLY valid RFC 8259 JSON adhering to:
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
"""

user_msg = "Extract all drink items and prices under the main sections (ORIGINAL TEA, MILK TEA, SMOOTHIE, FRUIT TEA, SEASON MENU, BEST SELLER) into the required JSON."

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg, "images": [b64]}
    ],
    "options": {
        "temperature": 0.1,
        "num_predict": 4096,
        "num_ctx": 6144
    },
    "stream": False
}

print("Testing focused extraction with num_predict=4096...")
t0 = time.time()
with httpx.Client(timeout=240.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.time() - t0
    print(f"Status: {res.status_code} in {elapsed:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print("Content length:", len(content))
    print("Thinking length:", len(thinking))
    print("Done reason:", data.get("done_reason"))
    print("Eval count:", data.get("eval_count"))
    
    with open("scratch/korean_result.json", "w", encoding="utf-8") as f:
        f.write(content)
        
    print("\n--- CONTENT (first 1000 chars) ---")
    print(content[:1000])

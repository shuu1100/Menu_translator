import sys
import os
sys.path.insert(0, r"C:\local_disc_D\Hackathan\Hack_to_october")

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
Output raw JSON starting with '{' and ending with '}'. Do not use markdown fences. Do not output think tags or commentary.
"""

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": prompt, "images": [b64]}
    ],
    "options": {
        "temperature": 0.0,
        "num_predict": 2048,
        "num_ctx": 4096
    },
    "stream": False
}

print("Querying Ollama...")
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print("Content len:", len(content))
    print("Thinking len:", len(thinking))
    
    # Save thinking to a file to examine
    with open("scratch/last_thinking.txt", "w", encoding="utf-8") as out:
        out.write("CONTENT:\n" + content + "\n\nTHINKING:\n" + thinking)
    print("Saved to scratch/last_thinking.txt")
    
    from backend.app.services.vision.json_parser import ModelJsonParser
    raw_to_parse = content if content.strip() else thinking
    print("Raw to parse len:", len(raw_to_parse))
    try:
        lang, items, warnings = ModelJsonParser.parse_and_validate(raw_to_parse, rotated.width, rotated.height)
        print(f"SUCCESS: {len(items)} items extracted! Language: {lang}")
        for itm in items:
            print(f"- [{itm.section}] {itm.original_name} ({itm.price_display})")
    except Exception as e:
        print("PARSE ERROR:", e)

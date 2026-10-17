import io
import base64
import httpx
import json
import time
from PIL import Image

path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(path, "rb") as f:
    img = Image.open(f)
    # Rotate 90 degrees clockwise to make text horizontal
    rotated = img.transpose(Image.Transpose.ROTATE_270)
    buf = io.BytesIO()
    rotated.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

target_language = "English"

prompt = f"""You are a professional menu translation and visual extraction engine.
Visually read all dishes and beverages from this menu and translate them into {target_language}.
Ignore ice/sweetness customization tables. Focus on the drink/food items.

Return ONLY a valid JSON object adhering strictly to RFC 8259:
{{
  "source_language": "ko",
  "target_language": "en",
  "items": [
    {{
      "reading_order": 1,
      "section": "ORIGINAL TEA",
      "original_name": "블랙 밀크티",
      "translated_name": "Black Milk Tea",
      "phonetic_transcription": "Beullaek Milkeuti",
      "price_display": "4.5 / 5.6",
      "culinary_description": "Classic black tea brewed with creamy milk",
      "box_2d": null
    }}
  ]
}}
Output raw JSON only starting with '{{' and ending with '}}'. Do not use markdown code fences. Keep reasoning brief.
"""

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": prompt, "images": [b64]}
    ],
    "options": {
        "temperature": 0.1,
        "num_predict": 4096,
        "num_ctx": 8192
    },
    "stream": False
}

print("Testing direct Visual Extraction + Translation in one pass...")
t0 = time.time()
with httpx.Client(timeout=240.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.time() - t0
    print(f"Status: {res.status_code} in {elapsed:.2f}s")
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    done_reason = data.get("done_reason")
    eval_count = data.get("eval_count")
    print(f"Content length: {len(content)}, Thinking length: {len(thinking)}, Done: {done_reason}, Eval count: {eval_count}")
    
    with open("scratch/single_pass_output.txt", "w", encoding="utf-8") as f:
        f.write("CONTENT:\n" + content + "\n\nTHINKING:\n" + thinking)
        
    # Check if JSON can be parsed
    from backend.app.services.vision.json_parser import ModelJsonParser
    raw_to_parse = content if content.strip() else thinking
    clean = ModelJsonParser.clean_raw_output(raw_to_parse)
    parsed = json.loads(clean)
    items = parsed.get("items", [])
    print(f"\nSUCCESS! Extracted & Translated {len(items)} items:")
    for i, it in enumerate(items[:10]):
        print(f" #{i+1} [{it.get('section')}] {it.get('original_name')} -> {it.get('translated_name')} ({it.get('price_display')})")
        print(f"     Phonetic: {it.get('phonetic_transcription')} | Desc: {it.get('culinary_description')}")

import io
import base64
import httpx
from PIL import Image

path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(path, "rb") as f:
    img = Image.open(f)
    rotated = img.transpose(Image.Transpose.ROTATE_270)
    buf = io.BytesIO()
    rotated.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

# Let's test /api/generate with system prompt forbidding thinking or raw mode
prompt = """<|im_start|>system
You are a fast OCR extraction engine. Do not produce any thought process. Output pure JSON only.<|im_end|>
<|im_start|>user
Extract all dishes/drinks and prices from this Korean menu into a single JSON object:
{"source_language": "ko", "items": [{"section": "...", "original_name": "...", "price_display": "..."}]}<|im_end|>
<|im_start|>assistant
<think>
Done.
</think>
{"""

payload = {
    "model": "qwen3-vl:8b",
    "prompt": prompt,
    "images": [b64],
    "raw": True,
    "options": {
        "temperature": 0.2,
        "num_predict": 2048,
        "num_ctx": 4096
    },
    "stream": False
}

print("Testing /api/generate with prefilled </think>...")
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/generate", json=payload)
    print("Status:", res.status_code)
    data = res.json()
    response_text = data.get("response", "")
    print("Response len:", len(response_text))
    print("Done reason:", data.get("done"))
    print("\n--- RESPONSE TEXT (first 1000) ---")
    print("{" + response_text[:1000])
    with open("scratch/generate_result.txt", "w", encoding="utf-8") as f:
        f.write("{" + response_text)

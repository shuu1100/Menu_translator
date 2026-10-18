import io
import base64
import httpx
from PIL import Image

path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(path, "rb") as f:
    img = Image.open(f)
    rotated = img.transpose(Image.Transpose.ROTATE_270)
    # Let's test a crop of the TOP section: ORIGINAL TEA & MILK TEA
    # Rotated image size is 1024 x 768
    # ORIGINAL TEA is roughly in the top left quadrant
    crop = rotated.crop((0, 0, 500, 400))
    buf = io.BytesIO()
    crop.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

# Test 1: System prompt with direct instruction
system_prompt = "You are a concise OCR JSON extractor. NEVER produce <think> reasoning tags. Output pure RFC 8259 JSON immediately."
user_prompt = "List all drinks and prices in this menu section: {\"items\": [{\"name\": \"...\", \"price\": \"...\"}]}"

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt, "images": [b64]}
    ],
    "options": {
        "temperature": 0.0,
        "num_predict": 1024,
    },
    "stream": False
}

print("Testing cropped section with system prompt...")
with httpx.Client(timeout=60.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    data = res.json()
    msg = data.get("message", {})
    print("Content len:", len(msg.get("content", "")))
    print("Thinking len:", len(msg.get("thinking", "")))
    print("Done reason:", data.get("done_reason"))
    print("\n--- CONTENT ---")
    print(msg.get("content", ""))
    print("\n--- THINKING (first 300) ---")
    print(msg.get("thinking", "")[:300])

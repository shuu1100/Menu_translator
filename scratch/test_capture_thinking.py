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

prompt = "Extract all menu items from this Korean menu into JSON: {\"source_language\": \"ko\", \"items\": [{\"section\": \"...\", \"original_name\": \"...\", \"price_display\": \"...\"}]}"

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

with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    data = res.json()
    msg = data.get("message", {})
    thinking = msg.get("thinking", "")
    content = msg.get("content", "")
    with open("scratch/thinking_sample.txt", "w", encoding="utf-8") as out:
        out.write("THINKING:\n" + thinking + "\n\nCONTENT:\n" + content)
    print("Done! Thinking len:", len(thinking), "Content len:", len(content))

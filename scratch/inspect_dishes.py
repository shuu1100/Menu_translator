import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
import urllib.request
import uuid
import json

url = "http://127.0.0.1:8001/api/v1/menus/analyze"
boundary = uuid.uuid4().hex
image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(image_path, "rb") as f:
    img_bytes = f.read()

parts = [
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"menu.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode("utf-8") + img_bytes + b"\r\n",
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"target_language\"\r\n\r\nen\r\n".encode("utf-8"),
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"rotation\"\r\n\r\n90\r\n".encode("utf-8"),
    f"--{boundary}--\r\n".encode("utf-8")
]

req = urllib.request.Request(url, data=b"".join(parts), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

print(f"Total dishes: {len(data.get('dishes', []))}")
for d in data.get("dishes", []):
    print(f"  [{d.get('category')}] {d.get('original_name')} -> {d.get('translated_name')} | Price: {d.get('price')} {d.get('currency') or ''}")

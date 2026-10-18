import urllib.request
import urllib.error
import uuid
import json
import time

url = "http://127.0.0.1:8001/api/v1/menus/analyze"
boundary = uuid.uuid4().hex
image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

with open(image_path, "rb") as f:
    img_bytes = f.read()

print(f"Loaded test image: {len(img_bytes)} bytes")

parts = []
parts.append(
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="menu.jpg"\r\n'
    f"Content-Type: image/jpeg\r\n\r\n".encode("utf-8")
    + img_bytes
    + b"\r\n"
)
parts.append(
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="target_language"\r\n\r\n'
    f"en\r\n".encode("utf-8")
)
parts.append(
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="rotation"\r\n\r\n'
    f"90\r\n".encode("utf-8")
)
parts.append(f"--{boundary}--\r\n".encode("utf-8"))
body = b"".join(parts)

req = urllib.request.Request(
    url,
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)

print("Sending request to FastAPI /api/v1/menus/analyze...")
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        elapsed = time.time() - t0
        print(f"Success! Status: {resp.status} in {elapsed:.2f}s")
        data = json.loads(resp.read().decode("utf-8"))
        print("Dishes count:", len(data.get("dishes", [])))
        print("Processing metadata:", data.get("processing_metadata"))
except urllib.error.HTTPError as e:
    elapsed = time.time() - t0
    print(f"HTTP Error: {e.code} {e.reason} in {elapsed:.2f}s")
    err_body = e.read().decode("utf-8", errors="replace")
    print("Response body:\n", err_body)
except Exception as e:
    elapsed = time.time() - t0
    print(f"Exception after {elapsed:.2f}s: {type(e)} {e}")

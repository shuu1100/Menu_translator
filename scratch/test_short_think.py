import httpx
import json
import time

items = [
    {"id": "item_1", "name": "블랙 밀크티", "section": "ORIGINAL TEA"},
    {"id": "item_2", "name": "망고 스무디", "section": "SMOOTHIE"},
]

prompt = """You are a fast culinary translator.
CRITICAL: Keep your thinking to under 50 words. Then close </think> and immediately output the JSON list of objects:
[
  {
    "id": "item_1",
    "translated_title": "Black Milk Tea",
    "phonetic_transcription": "Beullaek Milkeuti",
    "culinary_description": "Rich black tea infused with creamy milk."
  }
]

Translate these items to English:
""" + json.dumps(items, ensure_ascii=False)

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "options": {
        "temperature": 0.1,
        "num_predict": 1024,
    },
    "stream": False
}

print("Testing prompt with short thinking constraint...")
t0 = time.time()
with httpx.Client(timeout=60.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.time() - t0
    data = res.json()
    msg = data.get("message", {})
    content = msg.get("content", "")
    thinking = msg.get("thinking", "")
    print(f"Elapsed: {elapsed:.2f}s, Content len: {len(content)}, Thinking len: {len(thinking)}, Done: {data.get('done_reason')}")
    print("\n--- CONTENT ---")
    print(content)

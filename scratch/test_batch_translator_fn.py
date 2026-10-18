import httpx
import json
import time

items = [
    {"id": "item_1", "name": "블랙 밀크티", "section": "ORIGINAL TEA"},
    {"id": "item_2", "name": "얼그레이 밀크티", "section": "ORIGINAL TEA"},
    {"id": "item_3", "name": "망고 스무디", "section": "SMOOTHIE"},
    {"id": "item_4", "name": "솔티드 카라멜 밀크티", "section": "SEASON MENU"},
]

system_prompt = "You are a professional culinary translator. Translate dish/drink names into English. Output ONLY a valid JSON array of objects with keys: id, translated_title, phonetic_transcription, culinary_description."
user_prompt = f"Translate these Korean menu items to English:\n{json.dumps(items, ensure_ascii=False)}\nOutput JSON array:"

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "options": {
        "temperature": 0.1,
        "num_predict": 1024,
        "num_ctx": 4096
    },
    "stream": False
}

print("Running test_batch_translator_fn...")
t0 = time.time()
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.time() - t0
    data = res.json()
    content = data.get("message", {}).get("content", "")
    thinking = data.get("message", {}).get("thinking", "")
    print(f"Elapsed: {elapsed:.2f}s, Content len: {len(content)}, Thinking len: {len(thinking)}")
    with open("scratch/batch_result.txt", "w", encoding="utf-8") as f:
        f.write("CONTENT:\n" + content + "\n\nTHINKING:\n" + thinking)
    print("Done! Content saved to scratch/batch_result.txt")

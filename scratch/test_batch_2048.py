import httpx
import json
import time

items = [
    {"id": "item_1", "name": "블랙 밀크티", "section": "ORIGINAL TEA"},
    {"id": "item_2", "name": "얼그레이 밀크티", "section": "ORIGINAL TEA"},
    {"id": "item_3", "name": "망고 스무디", "section": "SMOOTHIE"},
    {"id": "item_4", "name": "솔티드 카라멜 밀크티", "section": "SEASON MENU"},
]

system_prompt = "You are a professional culinary translator. Output ONLY a valid JSON list of translated items. Keep internal reasoning to a minimum."
user_prompt = f"Translate these Korean menu items to English:\n{json.dumps(items, ensure_ascii=False)}\nOutput JSON list with schema: [{{\"id\": \"item_id\", \"translated_title\": \"English title\", \"phonetic_transcription\": \"Romanization\", \"culinary_description\": \"Description\"}}]"

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "options": {
        "temperature": 0.1,
        "num_predict": 2048,
        "num_ctx": 4096
    },
    "stream": False
}

print("Running batch translation with num_predict=2048...")
t0 = time.time()
with httpx.Client(timeout=180.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    elapsed = time.time() - t0
    data = res.json()
    content = data.get("message", {}).get("content", "")
    thinking = data.get("message", {}).get("thinking", "")
    done_reason = data.get("done_reason")
    print(f"Elapsed: {elapsed:.2f}s, Content len: {len(content)}, Done reason: {done_reason}")
    print("Content preview:")
    with open("scratch/batch_2048_result.json", "w", encoding="utf-8") as f:
        f.write(content)
    try:
        parsed = json.loads(content)
        print(f"SUCCESSFULLY PARSED {len(parsed)} TRANSLATIONS:")
        for item in parsed:
            print(f" - {item.get('id')}: {item.get('translated_title')} ({item.get('phonetic_transcription')})")
    except Exception as e:
        print("Parse error on content:", e)
        print("Content was:", content[:400])

import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding="utf-8")

def test_batch():
    dishes = [
        {"id": 0, "original_name": "豚骨ラーメン", "description": "チャーシューとネギが入った濃厚な豚骨スープのラーメン", "price": "¥980"},
        {"id": 1, "original_name": "김치볶음밥", "description": "매콤한 김치와 밥을 볶아 계란후라이를 얹은 요리", "price": "₩8,000"},
        {"id": 2, "original_name": "망고 스무디", "description": "신선한 망고를 갈아 만든 시원한 음료", "price": "₩5,500"},
        {"id": 3, "original_name": "Pizza Margherita", "description": "Pomodoro, mozzarella fresca e basilico", "price": "€12.00"},
    ]

    target_lang = "es"
    lang_name = "Spanish"

    system_prompt = (
        f"You are a professional culinary translator. Translate all menu items into natural, idiomatic {lang_name} ({target_lang}).\n"
        f"RULES:\n"
        f"- Translate every dish name ('translated_title') and description ('culinary_description') into {lang_name}.\n"
        f"- Preserve established cultural terms where appropriate.\n"
        f"- Do not produce any <think> tags or reasoning.\n"
        f"- Output RFC 8259 JSON matching this exact schema:\n"
        f'{{"items": [{{"id": 0, "translated_title": "...", "phonetic_transcription": "...", "culinary_description": "..."}}]}}'
    )

    prefill = '{\n  "items": [\n    {\n      "id": 0,'

    payload = {
        "model": "qwen3-vl:8b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({"items": dishes}, ensure_ascii=False)},
            {"role": "assistant", "content": prefill},
        ],
        "options": {"num_predict": 1024, "num_ctx": 2048, "temperature": 0.1},
        "stream": False,
    }

    t0 = time.time()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        res = json.loads(resp.read().decode())
        content = prefill + res.get("message", {}).get("content", "")
        print(f"Batch translation to {lang_name} finished in {time.time()-t0:.2f}s")
        print("Raw response:\n", content)

if __name__ == "__main__":
    test_batch()

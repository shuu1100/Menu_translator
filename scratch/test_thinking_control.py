import httpx
import time

url = "http://localhost:11434/api/chat"

tests = [
    {
        "name": "standard user prompt",
        "payload": {
            "model": "qwen3-vl:8b",
            "messages": [{"role": "user", "content": "Extract menu item: Black Milk Tea 4500. Return JSON."}],
            "format": "json",
            "options": {"num_predict": 300, "temperature": 0.1},
            "stream": False,
        }
    },
    {
        "name": "system prompt: Do not think",
        "payload": {
            "model": "qwen3-vl:8b",
            "messages": [
                {"role": "system", "content": "You are a concise extraction engine. Do not think. Output raw JSON immediately."},
                {"role": "user", "content": "Extract menu item: Black Milk Tea 4500. Return JSON."}
            ],
            "format": "json",
            "options": {"num_predict": 300, "temperature": 0.1},
            "stream": False,
        }
    },
    {
        "name": "assistant prefill or /no_think",
        "payload": {
            "model": "qwen3-vl:8b",
            "messages": [
                {"role": "user", "content": "/no_think Extract menu item: Black Milk Tea 4500. Return JSON."}
            ],
            "format": "json",
            "options": {"num_predict": 300, "temperature": 0.1},
            "stream": False,
        }
    },
    {
        "name": "think: false in options",
        "payload": {
            "model": "qwen3-vl:8b",
            "messages": [{"role": "user", "content": "Extract menu item: Black Milk Tea 4500. Return JSON."}],
            "format": "json",
            "options": {"num_predict": 300, "temperature": 0.1, "think": False},
            "stream": False,
        }
    },
]

with httpx.Client(timeout=60.0) as client:
    for t in tests:
        t0 = time.time()
        res = client.post(url, json=t["payload"])
        elapsed = time.time() - t0
        data = res.json()
        msg = data.get("message", {})
        c = msg.get("content", "")
        th = msg.get("thinking", "")
        print(f"[{t['name']}] Elapsed: {elapsed:.2f}s | Content len: {len(c)} | Thinking len: {len(th)} | Tokens: {data.get('eval_count')}")
        if c:
            print(f"  Content: {c[:120]}")

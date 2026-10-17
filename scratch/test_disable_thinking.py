import httpx
import time

url = "http://localhost:11434/api/chat"

# Test different ways to control thinking in Qwen3-VL / Ollama
tests = [
    {
        "name": "think: false in options",
        "payload": {
            "model": "qwen3-vl:8b",
            "messages": [{"role": "user", "content": "Extract: Milk Tea 4500. Return JSON: {\"name\": \"...\", \"price\": \"...\"}"}],
            "options": {"num_predict": 200, "temperature": 0.0, "think": False},
            "stream": False,
        }
    },
    {
        "name": "no_think in message content",
        "payload": {
            "model": "qwen3-vl:8b",
            "messages": [{"role": "user", "content": "Return JSON directly without thinking. {\"name\": \"...\", \"price\": \"...\"}\nItem: Milk Tea 4500"}],
            "options": {"num_predict": 200, "temperature": 0.0},
            "stream": False,
        }
    },
    {
        "name": "system prompt: Output JSON directly with no reasoning",
        "payload": {
            "model": "qwen3-vl:8b",
            "messages": [
                {"role": "system", "content": "Output JSON directly. Do not reason. Do not think. No explanations."},
                {"role": "user", "content": "Item: Milk Tea 4500. JSON:"}
            ],
            "options": {"num_predict": 200, "temperature": 0.0},
            "stream": False,
        }
    },
    {
        "name": "assistant prefill: {",
        "payload": {
            "model": "qwen3-vl:8b",
            "messages": [
                {"role": "user", "content": "Extract: Milk Tea 4500. Output JSON."},
                {"role": "assistant", "content": "{"}
            ],
            "options": {"num_predict": 200, "temperature": 0.0},
            "stream": False,
        }
    },
    {
        "name": "format: json",
        "payload": {
            "model": "qwen3-vl:8b",
            "messages": [{"role": "user", "content": "Extract Milk Tea 4500. JSON only."}],
            "format": "json",
            "options": {"num_predict": 200, "temperature": 0.0},
            "stream": False,
        }
    }
]

with httpx.Client(timeout=30.0) as client:
    for t in tests:
        t0 = time.time()
        try:
            res = client.post(url, json=t["payload"])
            elapsed = time.time() - t0
            data = res.json()
            msg = data.get("message", {})
            c = msg.get("content", "")
            th = msg.get("thinking", "")
            print(f"[{t['name']}] Elapsed: {elapsed:.2f}s | Content ({len(c)}): {repr(c[:80])} | Thinking ({len(th)})")
        except Exception as e:
            print(f"[{t['name']}] Error: {e}")

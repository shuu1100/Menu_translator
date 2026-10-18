import httpx

res = httpx.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen3-vl:8b",
        "messages": [
            {"role": "user", "content": 'Output JSON: {"fruit": "apple"}'},
            {"role": "assistant", "content": "</think>\n{"},
        ],
        "options": {"num_predict": 50},
        "stream": False,
    },
    timeout=60.0,
)
print("Done:", res.json().get("done_reason"))
print("Message:", res.json().get("message"))

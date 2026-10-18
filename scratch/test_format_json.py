import httpx
import json

payload = {
    "model": "qwen3-vl:8b",
    "messages": [
        {
            "role": "user",
            "content": "List 2 Spanish dishes with price in JSON: {\"items\": [{\"name\": \"...\", \"price\": \"...\"}]}"
        }
    ],
    "format": "json",
    "options": {
        "temperature": 0.1,
        "num_predict": 512
    },
    "stream": False
}

with httpx.Client(timeout=60.0) as client:
    res = client.post("http://localhost:11434/api/chat", json=payload)
    print("Status:", res.status_code)
    data = res.json()
    msg = data.get("message", {})
    print("Thinking len:", len(msg.get("thinking", "")))
    print("Content:")
    print(msg.get("content"))

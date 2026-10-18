import asyncio
import json
import httpx

async def test_ollama():
    url = "http://localhost:11434/api/chat"
    test_sentence = "The grilled chicken is served with rice and fresh vegetables."
    languages = [
        ("es", "Spanish"),
        ("fr", "French"),
        ("de", "German"),
        ("hi", "Hindi"),
        ("ja", "Japanese"),
    ]

    for code, name in languages:
        system_prompt = (
            f"You are a professional multilingual translator. Translate the following text into natural, idiomatic {name} ({code}).\n"
            "Preserve culinary meaning accurately. Return ONLY a JSON object with this format:\n"
            '{"translation": "translated text here"}'
        )
        payload = {
            "model": "qwen3-vl:8b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": test_sentence},
            ],
            "options": {"temperature": 0.1, "num_predict": 256},
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            print(f"\n[{code} - {name}]:\nRaw content: {content.strip()}")

if __name__ == "__main__":
    asyncio.run(test_ollama())

import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding="utf-8")

def test():
    test_sentence = "The grilled chicken is served with rice and fresh vegetables."
    languages = [
        ("es", "Spanish"),
        ("fr", "French"),
        ("de", "German"),
        ("hi", "Hindi"),
        ("ja", "Japanese"),
        ("ko", "Korean"),
        ("zh", "Chinese"),
        ("it", "Italian"),
        ("ar", "Arabic"),
        ("ru", "Russian"),
        ("pt", "Portuguese"),
    ]

    for code, name in languages:
        t0 = time.time()
        user_prompt = (
            f"You are a professional multilingual culinary translator. "
            f"Translate the following text into natural, idiomatic {name} ({code}):\n"
            f"'{test_sentence}'\n"
            "Return an RFC 8259 JSON object with key 'translated_text'."
        )
        data = json.dumps({
            "model": "qwen3-vl:8b",
            "messages": [
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": '{\n  "translated_text": "'},
            ],
            "options": {"num_predict": 128, "num_ctx": 1024, "temperature": 0.1},
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request("http://localhost:11434/api/chat", data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read().decode())
            msg = res.get("message", {})
            full = '{\n  "translated_text": "' + msg.get("content", "")
            parsed = json.loads(full) if full.endswith("}") else full
            val = parsed.get("translated_text") if isinstance(parsed, dict) else parsed
            print(f"[{code.upper()} - {name}] in {time.time()-t0:.2f}s: {val}")

if __name__ == "__main__":
    test()

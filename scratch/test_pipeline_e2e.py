import httpx
import json
import time

IMAGE_PATH = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

print("Sending Korean Gong Cha menu with rotation=90 to /analyze...")
t0 = time.perf_counter()
with open(IMAGE_PATH, "rb") as f:
    files = {"file": ("gongcha.jpg", f, "image/jpeg")}
    data = {
        "target_language": "en",
        "rotation": 90
    }
    with httpx.Client(timeout=300.0) as client:
        r = client.post("http://127.0.0.1:8001/api/v1/menus/analyze", files=files, data=data)
        elapsed = round(time.perf_counter() - t0, 2)
        print(f"Status Code: {r.status_code} in {elapsed}s")
        if r.status_code == 200:
            res = r.json()
            dishes = res.get("dishes", [])
            print(f"Dishes extracted: {len(dishes)}")
            for idx, d in enumerate(dishes[:16]):
                nat = (d.get('original_text') or '').encode('ascii', 'backslashreplace').decode('ascii')
                tra = (d.get('translated_title') or '').encode('ascii', 'backslashreplace').decode('ascii')
                desc = (d.get('culinary_description') or '').encode('ascii', 'backslashreplace').decode('ascii')
                print(f"[{idx+1}] Native: {nat} | Translated: {tra} | Price: {d.get('price')}")
                if desc:
                    print(f"     Desc: {desc}")
            
            proc = res.get("processing_metadata", {})
            print(f"\nTotal Reported Latency: {proc.get('total_latency_ms')}ms")
            print("Diagnostics:", json.dumps(proc.get("diagnostics", {}), indent=2))
            print("\nStage Latencies:")
            for s in proc.get("stages", []):
                print(f"  - {s.get('stage')}: {s.get('duration_ms')}ms (req_id: {s.get('request_id')})")
            with open("scratch/bench_result.json", "w", encoding="utf-8") as out:
                json.dump(res, out, indent=2, ensure_ascii=False)
        else:
            print("Error:", r.text[:500])

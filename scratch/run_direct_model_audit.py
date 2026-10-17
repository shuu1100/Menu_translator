"""Direct Model & Multilingual Benchmark Audit for Ollama Qwen3-VL:8B."""

import asyncio
import base64
import json
import os
import sys
import time
import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "qwen3-vl:8b"
KOREAN_IMAGE_PATH = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"
REPORT_PATH = r"C:\local_disc_D\Hackathan\Hack_to_october\scratch\audit_report.json"

sys.stdout.reconfigure(line_buffering=True)


def log(msg: str):
    print(msg, flush=True)


async def main():
    log("=" * 70)
    log("PHASE 1: Ollama Service & Model Compatibility Verification")
    log("=" * 70)

    report: dict = {
        "phase_1": {},
        "phase_2": [],
        "phase_3": [],
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        # 1. Version
        v_res = await client.get(f"{OLLAMA_URL}/api/version")
        version_data = v_res.json()
        log(f"Ollama Version: {version_data.get('version')}")
        report["phase_1"]["ollama_version"] = version_data.get("version")

        # 2. Tags
        tags_res = await client.get(f"{OLLAMA_URL}/api/tags")
        models = [m["name"] for m in tags_res.json().get("models", [])]
        log(f"Models in Ollama: {models}")
        report["phase_1"]["installed_models"] = models

        # 3. Model Show
        show_res = await client.post(f"{OLLAMA_URL}/api/show", json={"name": MODEL_NAME})
        show_data = show_res.json() if show_res.status_code == 200 else {}
        details = show_data.get("details", {})
        log(f"Model Arch: {details.get('family')}, Params: {details.get('parameter_size')}, Quant: {details.get('quantization_level')}")
        report["phase_1"]["model_details"] = details

        # 4. Text Baseline
        log("\nTesting Text Generation Baseline (Translation query)...")
        t0 = time.perf_counter()
        tb_res = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": "Translate 'Iced Green Tea' into Korean, Japanese, and Spanish."}],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 100},
            },
            timeout=60.0,
        )
        tb_latency = (time.perf_counter() - t0) * 1000
        tb_data = tb_res.json()
        eval_count = tb_data.get("eval_count", 0)
        eval_dur_s = (tb_data.get("eval_duration", 1) or 1) / 1e9
        tps = eval_count / eval_dur_s if eval_dur_s > 0 else 0
        log(f"Text Baseline Latency: {tb_latency:.1f}ms, Speed: {tps:.1f} tokens/s, Tokens: {eval_count}")
        report["phase_1"]["text_baseline"] = {
            "latency_ms": tb_latency,
            "tokens": eval_count,
            "tokens_per_sec": tps,
            "sample_output": tb_data.get("message", {}).get("content", "").strip(),
        }

        log("\n" + "=" * 70)
        log("PHASE 2: Direct Model Testing (Bypassing Application Code)")
        log("=" * 70)

        with open(KOREAN_IMAGE_PATH, "rb") as f:
            korean_img_b64 = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "You are an accurate multilingual OCR engine. Inspect this menu image carefully.\n"
            "Extract structured data as raw RFC 8259 JSON with these exact fields:\n"
            "{\n"
            '  "detected_languages": ["ko"],\n'
            '  "sections": ["Category name 1", "Category name 2"],\n'
            '  "items": [\n'
            "    {\n"
            '      "name": "Original dish or drink name exactly as printed",\n'
            '      "printed_description": "Verbatim description printed next to dish, or null if none",\n'
            '      "price": "Price string as printed or null",\n'
            '      "promotional_labels": "e.g. Best Seller, New, or null"\n'
            "    }\n"
            "  ],\n"
            '  "uncertain_text": []\n'
            "}\n"
            "RULES:\n"
            "1. Extract ONLY authentic text printed on the menu image.\n"
            "2. If no description is printed, set printed_description to null.\n"
            "3. Do NOT invent descriptions, recipes, or flavor notes.\n"
            "4. Return ONLY valid JSON starting with '{' and ending with '}'."
        )

        leakage_phrases = [
            "Let's check the structure",
            "Need to extract each item",
            "The menu has columns",
            "Wait no",
            "looking at the image",
            "user provided text",
            "Artisan regional culinary",
            "Pizza Margherita",
        ]

        for run_idx in range(1, 4):
            log(f"\n--- Direct Model Trial #{run_idx} of 3 ---")
            t_start = time.perf_counter()
            r = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                            "images": [korean_img_b64],
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 2500,
                        "num_ctx": 4096,
                    },
                },
                timeout=300.0,
            )
            elapsed_ms = (time.perf_counter() - t_start) * 1000

            if r.status_code == 200:
                data = r.json()
                msg = data.get("message", {})
                content = msg.get("content", "")
                thinking = msg.get("thinking", "")
                eval_c = data.get("eval_count", 0)
                dur_s = (data.get("eval_duration", 1) or 1) / 1e9
                speed = eval_c / dur_s if dur_s > 0 else 0
                done_reason = data.get("done_reason")

                log(f"Trial #{run_idx} finished in {elapsed_ms/1000:.1f}s | Speed: {speed:.1f} t/s | Tokens: {eval_c} | Reason: {done_reason}")
                log(f"Content Length: {len(content)} chars | Thinking Length: {len(thinking)} chars")

                # Check leakage phrases in content vs thinking
                in_content = [p for p in leakage_phrases if p.lower() in content.lower()]
                in_thinking = [p for p in leakage_phrases if p.lower() in thinking.lower()]
                log(f"Leakage in raw content: {in_content}")
                log(f"Leakage in internal thinking: {in_thinking}")

                # JSON parse check
                parsed = None
                items_count = 0
                first_few = []
                try:
                    clean_c = content.strip()
                    if clean_c.startswith("```"):
                        clean_c = clean_c.split("```")[1]
                        if clean_c.startswith("json"):
                            clean_c = clean_c[4:]
                        clean_c = clean_c.strip()
                    parsed = json.loads(clean_c)
                    if isinstance(parsed, dict) and "items" in parsed:
                        items_count = len(parsed["items"])
                        first_few = [it.get("name") for it in parsed["items"][:5]]
                except Exception as je:
                    log(f"JSON Parse Note: {je}")

                log(f"Extracted Dishes: {items_count}")
                log(f"Sample Dishes: {first_few}")

                trial_info = {
                    "trial": run_idx,
                    "latency_ms": elapsed_ms,
                    "eval_count": eval_c,
                    "tokens_per_sec": speed,
                    "done_reason": done_reason,
                    "content_length": len(content),
                    "thinking_length": len(thinking),
                    "items_extracted": items_count,
                    "sample_dishes": first_few,
                    "leakage_in_content": in_content,
                    "leakage_in_thinking": in_thinking,
                    "raw_content_preview": content[:400],
                    "raw_thinking_preview": thinking[:400] if thinking else "",
                }
                report["phase_2"].append(trial_info)
            else:
                log(f"Trial #{run_idx} FAILED: HTTP {r.status_code}")

        # Save Phase 1 & 2 results immediately
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        log(f"\nSaved intermediate report to {REPORT_PATH}")

        log("\n" + "=" * 70)
        log("PHASE 3: Full Application Multilingual Pipeline Benchmark")
        log("=" * 70)

        training_dir = r"C:\local_disc_D\Hackathan\Hack_to_october\data\training\images"
        bench_cases = [
            {"id": "ko_tea", "name": "Korean Multi-Column Tea Menu (Real)", "path": KOREAN_IMAGE_PATH, "lang": "ko"},
            {"id": "ja_ramen", "name": "Japanese Ramen Menu", "path": os.path.join(training_dir, "menu_rest_fam_japanese_02_clear_00.png"), "lang": "ja"},
            {"id": "ar_levantine", "name": "Levantine Arabic RTL Menu", "path": os.path.join(training_dir, "menu_rest_fam_levantine_04_clear_00.png"), "lang": "ar"},
            {"id": "it_trattoria", "name": "Italian Trattoria Menu", "path": os.path.join(training_dir, "menu_rest_fam_italian_01_clear_00.png"), "lang": "it"},
        ]

        for bc in bench_cases:
            if not os.path.exists(bc["path"]):
                log(f"Image not found: {bc['path']}")
                continue

            with open(bc["path"], "rb") as f:
                img_data = f.read()

            log(f"\nBenchmarking {bc['name']} via FastAPI backend...")
            t0 = time.perf_counter()
            files = {"file": ("test_menu.png", img_data, "image/png")}
            data = {"target_language": "en"}
            try:
                res = await client.post("http://127.0.0.1:8001/api/v1/menus/analyze", files=files, data=data, timeout=300.0)
                dur_ms = (time.perf_counter() - t0) * 1000

                if res.status_code == 200:
                    rj = res.json()
                    dishes = rj.get("dishes", [])
                    dish_count = len(dishes)
                    with_price = sum(1 for d in dishes if d.get("price"))
                    with_desc = sum(1 for d in dishes if d.get("culinary_description"))
                    leakage_count = sum(1 for d in dishes if "let's" in (d.get("original_text") or "").lower())
                    tags_count = sum(len(d.get("tags") or []) for d in dishes)

                    names = [d.get("original_text", "").strip().lower() for d in dishes]
                    unique_names = set(names)
                    dup_rate = (len(names) - len(unique_names)) / len(names) if names else 0.0

                    log(f"  -> HTTP 200 in {dur_ms/1000:.1f}s | Dishes: {dish_count} | Prices: {with_price} | Descriptions: {with_desc} | Tags: {tags_count}")
                    log(f"  -> Commentary in dishes: {leakage_count} | Duplication rate: {dup_rate*100:.1f}%")
                    if dishes:
                        log(f"  -> Sample 1: Orig: '{dishes[0].get('original_text')}' -> Trans: '{dishes[0].get('translated_title')}' (Price: {dishes[0].get('price')})")

                    report["phase_3"].append(
                        {
                            "id": bc["id"],
                            "name": bc["name"],
                            "language": bc["lang"],
                            "status": "PASS",
                            "duration_s": round(dur_ms / 1000, 2),
                            "dish_count": dish_count,
                            "price_coverage_pct": round((with_price / dish_count * 100) if dish_count else 0, 1),
                            "desc_coverage_pct": round((with_desc / dish_count * 100) if dish_count else 0, 1),
                            "commentary_leakage_count": leakage_count,
                            "duplicate_rate_pct": round(dup_rate * 100, 1),
                        }
                    )
                else:
                    log(f"  -> FAILED: HTTP {res.status_code}")
                    report["phase_3"].append({"id": bc["id"], "name": bc["name"], "status": f"FAIL ({res.status_code})"})
            except Exception as e:
                log(f"  -> Exception: {e}")
                report["phase_3"].append({"id": bc["id"], "name": bc["name"], "status": f"ERROR ({e})"})

        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        log(f"\nFinal benchmark complete! Results saved to {REPORT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())

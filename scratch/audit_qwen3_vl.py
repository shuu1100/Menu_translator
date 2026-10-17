"""Audit and Benchmark Suite for Ollama Qwen3-VL 8B and Multilingual Menu Translator.

Executes:
Phase 1: Ollama service, model compatibility, text generation baseline, hardware latency.
Phase 2: Direct model testing with real Korean menu image (3 runs) bypassing application.
Phase 3: Multilingual benchmark across languages and scripts.
"""

import asyncio
import base64
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "qwen3-vl:8b"
KOREAN_IMAGE_PATH = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"

print("=" * 80)
print("AUDIT & BENCHMARK: OLLAMA QWEN3-VL:8B ON MULTILINGUAL MENU TRANSLATOR")
print("=" * 80)


async def phase_1_verify_ollama():
    print("\n--- PHASE 1: Verify Ollama Service & Model Compatibility ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Check version
        try:
            r = await client.get(f"{OLLAMA_URL}/api/version")
            print(f"Ollama Version API: {r.status_code} -> {r.json()}")
        except Exception as e:
            print(f"FAILED to reach Ollama version API: {e}")
            return False

        # 2. Check tags
        try:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            models = [m.get("name") for m in r.json().get("models", [])]
            print(f"Available Models in Ollama: {models}")
            if MODEL_NAME not in models and f"{MODEL_NAME}:latest" not in models:
                print(f"WARNING: '{MODEL_NAME}' not found in tags!")
            else:
                print(f"SUCCESS: '{MODEL_NAME}' is present in Ollama tag registry.")
        except Exception as e:
            print(f"FAILED to query tags: {e}")

        # 3. Query Model Details (/api/show)
        try:
            r = await client.post(f"{OLLAMA_URL}/api/show", json={"name": MODEL_NAME})
            if r.status_code == 200:
                info = r.json()
                details = info.get("details", {})
                model_info = info.get("model_info", {})
                arch = details.get("family") or model_info.get("general.architecture")
                param_size = details.get("parameter_size")
                quant = details.get("quantization_level")
                print(f"Model Architecture: {arch}, Params: {param_size}, Quant: {quant}")
                print(f"Context Length: {model_info.get('qwen2vl.context_length') or model_info.get('qwen2.context_length') or 'N/A'}")
            else:
                print(f"Ollama /api/show returned {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"Error querying model info: {e}")

        # 4. Text Generation Baseline
        print("\nRunning Text Generation Baseline...")
        t0 = time.perf_counter()
        try:
            payload = {
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": "Translate 'Milk Tea with Tapioca Pearls' into Korean, Japanese, and Spanish."}],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 150},
            }
            r = await client.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60.0)
            latency = (time.perf_counter() - t0) * 1000
            if r.status_code == 200:
                data = r.json()
                eval_count = data.get("eval_count", 0)
                eval_duration_s = (data.get("eval_duration", 1) or 1) / 1e9
                tps = eval_count / eval_duration_s if eval_duration_s > 0 else 0
                print(f"Text Generation Result: HTTP {r.status_code} in {latency:.2f}ms")
                print(f"Tokens Generated: {eval_count}, Speed: {tps:.2f} tokens/s")
                content = data.get("message", {}).get("content", "").strip()
                thinking = data.get("message", {}).get("thinking", "").strip()
                print(f"Sample Output: {content[:150]}...")
                if thinking:
                    print(f"Model Thinking Block Detected: length={len(thinking)} chars")
            else:
                print(f"Text Generation FAILED: HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"Text Generation Exception: {e}")

    return True


async def phase_2_direct_model_testing():
    print("\n--- PHASE 2: Direct Model Testing Bypassing Application Code ---")
    if not os.path.exists(KOREAN_IMAGE_PATH):
        print(f"ERROR: Image not found at {KOREAN_IMAGE_PATH}")
        return

    with open(KOREAN_IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    b64_img = base64.b64encode(img_bytes).decode("utf-8")
    img_size_kb = len(img_bytes) / 1024
    print(f"Loaded Korean Menu Image: {img_size_kb:.2f} KB")

    prompt = (
        "You are an expert menu extraction OCR engine. Visually read the uploaded restaurant menu.\n"
        "Extract structured menu data into an RFC 8259 JSON object with this exact structure:\n"
        "{\n"
        '  "detected_languages": ["ko"],\n'
        '  "sections": ["Category name 1", "Category name 2"],\n'
        '  "items": [\n'
        "    {\n"
        '      "name": "Exact dish or drink name as printed",\n'
        '      "printed_description": "Verbatim description printed next to dish, or null if none",\n'
        '      "price": "Price string or null",\n'
        '      "promotional_labels": "e.g. Best Seller, New, or null"\n'
        "    }\n"
        "  ],\n"
        '  "uncertain_text": []\n'
        "}\n"
        "CRITICAL RULES:\n"
        "- Do NOT invent descriptions, flavor notes, or recipes.\n"
        "- If no description is printed, set printed_description to null.\n"
        "- Do NOT output your internal thoughts or reasoning.\n"
        "- Return valid raw JSON starting with '{' and ending with '}'."
    )

    results = []

    async with httpx.AsyncClient(timeout=300.0) as client:
        for run_idx in range(1, 4):
            print(f"\n>> Execution Run #{run_idx} of 3 (Direct to Ollama)...")
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [b64_img],
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 4096,
                    "num_ctx": 5120,
                },
            }

            t0 = time.perf_counter()
            try:
                r = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
                duration_ms = (time.perf_counter() - t0) * 1000
                if r.status_code != 200:
                    print(f"Run #{run_idx} FAILED: HTTP {r.status_code}: {r.text[:200]}")
                    continue

                data = r.json()
                msg = data.get("message", {})
                content = msg.get("content", "")
                thinking = msg.get("thinking", "")
                eval_count = data.get("eval_count", 0)
                eval_duration_s = (data.get("eval_duration", 1) or 1) / 1e9
                tps = eval_count / eval_duration_s if eval_duration_s > 0 else 0
                done_reason = data.get("done_reason")

                print(f"Run #{run_idx} Status: HTTP 200 in {duration_ms:.2f}ms ({duration_ms/1000:.1f}s)")
                print(f"Tokens: {eval_count}, Speed: {tps:.2f} tokens/s, Done Reason: {done_reason}")
                print(f"Content Length: {len(content)} chars, Thinking Length: {len(thinking)} chars")

                # Check for prompt leakage phrases in content vs thinking
                target_phrases = [
                    "Let's check the structure",
                    "Need to extract each item",
                    "The menu has columns",
                    "Wait no",
                    "looking at the image",
                    "user provided text",
                    "Artisan regional culinary",
                    "Pizza Margherita",
                ]

                print("Phrase Analysis:")
                found_in_content = []
                found_in_thinking = []
                for p in target_phrases:
                    if p.lower() in content.lower():
                        found_in_content.append(p)
                    if p.lower() in thinking.lower():
                        found_in_thinking.append(p)

                print(f"  Found in raw 'content': {found_in_content}")
                print(f"  Found in model 'thinking': {found_in_thinking}")

                # Attempt JSON parsing
                parsed_json = None
                items_extracted = 0
                try:
                    # Clean markdown fence if present
                    clean_c = content.strip()
                    if clean_c.startswith("```"):
                        clean_c = clean_c.split("```")[1]
                        if clean_c.startswith("json"):
                            clean_c = clean_c[4:]
                        clean_c = clean_c.strip()
                    parsed_json = json.loads(clean_c)
                    if isinstance(parsed_json, dict) and "items" in parsed_json:
                        items_extracted = len(parsed_json["items"])
                except Exception as je:
                    print(f"  Raw Content JSON Parse Note: {je}")

                print(f"  Parsed Items Count: {items_extracted}")
                if parsed_json and "items" in parsed_json and len(parsed_json["items"]) > 0:
                    sample_dishes = [it.get("name") for it in parsed_json["items"][:5]]
                    print(f"  Sample Extracted Dish Names: {sample_dishes}")

                results.append(
                    {
                        "run": run_idx,
                        "duration_ms": duration_ms,
                        "eval_count": eval_count,
                        "tps": tps,
                        "done_reason": done_reason,
                        "items_count": items_extracted,
                        "found_in_content": found_in_content,
                        "found_in_thinking": found_in_thinking,
                        "thinking_len": len(thinking),
                    }
                )

            except Exception as e:
                print(f"Run #{run_idx} Exception: {e}")

    return results


async def phase_3_multilingual_benchmark():
    print("\n--- PHASE 3: Multilingual Pipeline Benchmark ---")
    training_img_dir = r"C:\local_disc_D\Hackathan\Hack_to_october\data\training\images"
    test_cases = [
        {"lang": "ko", "name": "Korean Multi-Column Tea Menu (Real)", "path": KOREAN_IMAGE_PATH, "script": "Hangul (Korean)"},
        {"lang": "ja", "name": "Japanese Ramen Menu", "path": os.path.join(training_img_dir, "menu_rest_fam_japanese_02_clear_00.png"), "script": "Japanese (Kanji/Kana)"},
        {"lang": "ar", "name": "Levantine Arabic RTL Menu", "path": os.path.join(training_img_dir, "menu_rest_fam_levantine_04_clear_00.png"), "script": "Arabic (RTL)"},
        {"lang": "it", "name": "Italian Trattoria Menu", "path": os.path.join(training_img_dir, "menu_rest_fam_italian_01_clear_00.png"), "script": "Latin (Italian)"},
        {"lang": "fr", "name": "French Bistro Menu", "path": os.path.join(training_img_dir, "menu_rest_fam_french_05_clear_00.png"), "script": "Latin (French)"},
        {"lang": "es", "name": "Mexican Taqueria Menu", "path": os.path.join(training_img_dir, "menu_rest_fam_mexican_03_clear_00.png"), "script": "Latin (Spanish)"},
    ]

    benchmark_report = []

    async with httpx.AsyncClient(timeout=300.0) as client:
        for tc in test_cases:
            p = tc["path"]
            if not os.path.exists(p):
                print(f"File not found: {p}")
                continue

            with open(p, "rb") as f:
                img_data = f.read()

            print(f"\nTesting {tc['name']} ({tc['script']})... Size: {len(img_data)/1024:.1f} KB")

            # Call FastAPI backend menu analysis endpoint
            t0 = time.perf_counter()
            try:
                files = {"file": ("menu_test.png", img_data, "image/png")}
                data = {"target_language": "en"}
                res = await client.post("http://127.0.0.1:8001/api/v1/menus/analyze", files=files, data=data, timeout=300.0)
                elapsed_ms = (time.perf_counter() - t0) * 1000

                if res.status_code == 200:
                    resp_json = res.json()
                    dishes = resp_json.get("dishes", [])
                    meta = resp_json.get("menu_metadata", {})
                    proc = resp_json.get("processing_metadata", {})

                    # Metrics computation
                    dish_count = len(dishes)
                    with_desc = sum(1 for d in dishes if d.get("culinary_description"))
                    with_price = sum(1 for d in dishes if d.get("price"))
                    has_commentary = sum(1 for d in dishes if "let's" in (d.get("original_text") or "").lower() or "columns" in (d.get("original_text") or "").lower())
                    
                    # Duplicate check
                    names = [d.get("original_text", "").strip().lower() for d in dishes]
                    unique_names = set(names)
                    dup_rate = (len(names) - len(unique_names)) / len(names) if names else 0.0

                    print(f"  HTTP {res.status_code} in {elapsed_ms:.1f}ms ({elapsed_ms/1000:.1f}s)")
                    print(f"  Dishes Extracted: {dish_count}, With Price: {with_price}, With Desc: {with_desc}")
                    print(f"  Prompt Commentary in Dish Names: {has_commentary}")
                    print(f"  Duplicate Item Rate: {dup_rate*100:.1f}%")
                    if dishes:
                        print(f"  First 2 Dishes:")
                        for d in dishes[:2]:
                            print(f"    - Orig: '{d.get('original_text')}', Trans: '{d.get('translated_title')}', Price: '{d.get('price')}', Desc: '{d.get('culinary_description')}'")

                    benchmark_report.append(
                        {
                            "language": tc["lang"],
                            "name": tc["name"],
                            "script": tc["script"],
                            "status": "PASS",
                            "latency_s": round(elapsed_ms / 1000, 2),
                            "dish_count": dish_count,
                            "price_coverage": round((with_price / dish_count * 100) if dish_count else 0, 1),
                            "desc_coverage": round((with_desc / dish_count * 100) if dish_count else 0, 1),
                            "commentary_leakage_count": has_commentary,
                            "duplicate_rate": round(dup_rate * 100, 1),
                        }
                    )
                else:
                    print(f"  FAILED: HTTP {res.status_code}: {res.text[:200]}")
                    benchmark_report.append(
                        {
                            "language": tc["lang"],
                            "name": tc["name"],
                            "script": tc["script"],
                            "status": f"FAIL ({res.status_code})",
                            "latency_s": round(elapsed_ms / 1000, 2),
                            "dish_count": 0,
                        }
                    )
            except Exception as e:
                print(f"  Exception testing {tc['name']}: {e}")
                benchmark_report.append(
                    {
                        "language": tc["lang"],
                        "name": tc["name"],
                        "script": tc["script"],
                        "status": f"ERROR ({e})",
                        "latency_s": 0,
                        "dish_count": 0,
                    }
                )

    return benchmark_report


async def main():
    ok = await phase_1_verify_ollama()
    if not ok:
        print("Aborting: Ollama verification failed.")
        return

    p2_res = await phase_2_direct_model_testing()
    p3_res = await phase_3_multilingual_benchmark()

    print("\n" + "=" * 80)
    print("FINAL SUMMARY OF AUDIT FINDINGS")
    print("=" * 80)
    print(f"Direct Model Runs (Phase 2): {p2_res}")
    print(f"\nMultilingual Benchmark Table (Phase 3):")
    print(json.dumps(p3_res, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

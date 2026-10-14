#!/usr/bin/env python3
"""
Benchmark script for evaluating local Vision-Language Models (Qwen3-VL/Qwen2.5-VL)
on multi-column restaurant menus under diverse conditions.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import Settings
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.tests.fixtures.menu_generator import create_synthetic_menu
from backend.tests.fixtures.metrics import evaluate_extraction_batch


async def run_benchmark():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    settings = Settings()
    provider = OllamaVisionProvider(settings=settings)

    print("=" * 70)
    print("MENU TRANSLATOR - VLM BENCHMARK SUITE")
    print(f"Target Model:    {settings.vision_model}")
    print(f"Ollama Endpoint: {settings.ollama_base_url}")
    print("=" * 70)

    # 1. Check health
    is_healthy = await provider.check_health()
    if not is_healthy:
        print("\n[!] WARNING: Ollama is offline or model is not pulled.")
        print(f"    Please start Ollama:  'ollama serve'")
        print(f"    And pull the model:    'ollama pull {settings.vision_model}'")
        print("\nAborting live benchmark. To test offline parsing without Ollama, run pytest.")
        return

    print(f"[OK] Ollama online with model '{settings.vision_model}' ready.\n")

    # Allow specifying conditions via command line, e.g. python benchmark_vlm.py clear
    if len(sys.argv) > 1:
        conditions = [c.lower() for c in sys.argv[1:] if c.lower() in ["clear", "low_light", "noisy", "decorative"]]
    else:
        conditions = ["clear"]
    results = []

    for cond in conditions:
        print(f"--> Generating synthetic menu fixture [Condition: {cond}]...")
        img_bytes, gt_meta = create_synthetic_menu(width=1200, height=1600, condition=cond)
        apply_clahe = (cond == "low_light")

        print(f"    Executing VLM extraction (CLAHE={apply_clahe})...")
        t0 = time.perf_counter()
        try:
            extraction = await provider.extract_menu(
                image_bytes=img_bytes,
                mime_type="image/jpeg",
                apply_clahe=apply_clahe,
            )
            latency = round((time.perf_counter() - t0) * 1000, 2)

            pred_dicts = [item.model_dump() for item in extraction.items]
            metrics = evaluate_extraction_batch(pred_dicts, gt_meta["items"])
            metrics["condition"] = cond
            metrics["latency_ms"] = latency
            metrics["extracted_count"] = len(extraction.items)
            results.append(metrics)

            print(f"    [Done in {latency}ms] Extracted {len(extraction.items)} items.")
            print(f"    Dish Match Rate: {metrics['dish_match_rate']*100:.1f}%, Mean CER: {metrics['mean_cer']:.3f}, Mean IoU: {metrics['mean_iou']:.3f}\n")

        except Exception as e:
            print(f"    [!] Error during extraction: {str(e)}\n")
            results.append({
                "condition": cond,
                "error": str(e),
                "dish_match_rate": 0.0,
                "mean_cer": 1.0,
                "mean_iou": 0.0,
                "latency_ms": 0.0,
            })

    # Summary table
    print("=" * 70)
    print("BENCHMARK EVALUATION SUMMARY")
    print(f"{'Condition':<14} | {'Match %':<9} | {'Mean CER':<9} | {'Mean IoU':<9} | {'Latency':<10}")
    print("-" * 70)
    for r in results:
        if "error" in r and r.get("latency_ms") == 0.0:
            print(f"{r['condition']:<14} | ERROR: {r['error'][:40]}")
        else:
            print(
                f"{r['condition']:<14} | "
                f"{r['dish_match_rate']*100:>7.1f}% | "
                f"{r['mean_cer']:>9.3f} | "
                f"{r['mean_iou']:>9.3f} | "
                f"{r['latency_ms']:>8.1f}ms"
            )
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_benchmark())

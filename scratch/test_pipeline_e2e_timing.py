import sys
sys.path.insert(0, ".")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
import asyncio
import time

from backend.app.schemas.menu_analysis import SupportedLanguage
from backend.app.services.pipeline_orchestrator import MenuPipelineOrchestrator
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.app.services.translation.translator import CulinaryTranslatorService

async def main():
    image_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\8d3abd46-f5ca-4b56-bc66-6d4bdf865dcd\.user_uploaded\media_1792144379913.jpg"
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    print(f"Loaded image: {len(img_bytes)} bytes")
    # Initialize orchestrator with deterministic translation
    translator = CulinaryTranslatorService(use_deterministic_only=True)
    orchestrator = MenuPipelineOrchestrator(translator=translator)

    print("Executing pipeline on Korean Gong cha menu (with rotation=90)...")
    t0 = time.perf_counter()
    resp = await orchestrator.run_pipeline(
        image_bytes=img_bytes,
        mime_type="image/jpeg",
        target_language=SupportedLanguage.EN,
        rotation=90,
    )
    total_sec = time.perf_counter() - t0
    print(f"\nPipeline Finished in {total_sec:.2f}s!")
    print(f"Dishes extracted: {len(resp.dishes)}")
    print(f"Source Language: {resp.menu_metadata.source_language}")
    print("\nStage Timings:")
    for s in resp.processing_metadata.stages:
        print(f"  - {s.stage}: {s.duration_ms:.1f}ms ({s.duration_ms/1000:.2f}s)")

    print("\nFirst 10 Extracted Dishes:")
    for idx, d in enumerate(resp.dishes[:10]):
        print(f"  #{idx+1} [{d.section}] '{d.original_text}' -> '{d.translated_title}' | Price: {d.price} | Allergens: {[a.allergen for a in d.allergen_warnings]}")

if __name__ == "__main__":
    asyncio.run(main())

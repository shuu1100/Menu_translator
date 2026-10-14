"""Pipeline Orchestration service for Menu Analysis with hybrid RAG, contextual translation,
and evidence-grounded allergen safety evaluations.
"""

import time
import uuid
from typing import Any, List, Optional, Tuple

from backend.app.core.config import Settings, get_settings
from backend.app.db.models import DishRecord
from backend.app.schemas.extraction import MenuExtractionResult, MenuTextBlock
from backend.app.schemas.menu_analysis import (
    AllergenWarning,
    AnalyzedDish,
    DietaryCompatibility,
    EvidenceStatus,
    MenuAnalysisResponse,
    MenuMetadata,
    ProcessingMetadata,
    StageTiming,
    SupportedLanguage,
)
from backend.app.services.image_processor import ImageProcessor
from backend.app.services.rag.retriever import CulinaryRetriever
from backend.app.services.safety.safety_engine import CulinarySafetyEngine
from backend.app.services.translation.translator import CulinaryTranslatorService
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.app.services.vision.provider import MenuVisionProvider


class MenuPipelineOrchestrator:
    """Orchestrates ingestion, extraction, hybrid RAG enrichment, contextual translation,
    and rigorous allergen safety evaluations.
    """

    def __init__(
        self,
        vision_provider: Optional[MenuVisionProvider] = None,
        retriever: Optional[CulinaryRetriever] = None,
        translator: Optional[CulinaryTranslatorService] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.vision_provider = vision_provider or OllamaVisionProvider(settings=self.settings)
        self.retriever = retriever or CulinaryRetriever()
        self.translator = translator or CulinaryTranslatorService()

    async def run_pipeline(
        self,
        image_bytes: bytes,
        mime_type: str,
        target_language: SupportedLanguage = SupportedLanguage.EN,
        user_dietary_restrictions: Optional[List[str]] = None,
        restaurant_id: Optional[str] = None,
        apply_clahe: bool = False,
    ) -> MenuAnalysisResponse:
        """Execute end-to-end analysis with stage timing and evidence tracking."""
        total_start = time.perf_counter()
        request_id = str(uuid.uuid4())
        stages: List[StageTiming] = []
        user_restrictions = user_dietary_restrictions or []

        # Stage 1 & 2: Ingestion, Validation & Preprocessing
        t0 = time.perf_counter()
        pil_img = ImageProcessor.validate_and_decode(
            image_bytes=image_bytes,
            max_size_mb=self.settings.max_upload_size_mb,
        )
        preprocessed = ImageProcessor.preprocess_for_vlm(
            image=pil_img,
            max_dimension=self.settings.image_max_dimension,
            apply_clahe=apply_clahe,
        )
        stages.append(StageTiming(stage="preprocessing", duration_ms=round((time.perf_counter() - t0) * 1000, 2)))

        # Stage 3: Visual VLM Extraction
        t0 = time.perf_counter()
        extraction: MenuExtractionResult = await self.vision_provider.extract_menu(
            image_bytes=image_bytes,
            mime_type=mime_type,
            metadata={"menu_id": request_id},
            apply_clahe=apply_clahe,
        )
        stages.append(StageTiming(stage="visual_extraction", duration_ms=round((time.perf_counter() - t0) * 1000, 2)))

        # Stage 4: Hybrid RAG Culinary Knowledge Retrieval
        t0 = time.perf_counter()
        rag_matches: List[Optional[Any]] = []
        retrieval_hits = 0
        for item in extraction.items:
            retrieved = self.retriever.retrieve_dish(item.original_name, restaurant_id=restaurant_id)
            rag_matches.append(retrieved)
            if retrieved is not None and retrieved.is_authoritative:
                retrieval_hits += 1
        stages.append(StageTiming(stage="culinary_enrichment_rag", duration_ms=round((time.perf_counter() - t0) * 1000, 2)))

        # Stage 5: Contextual Culinary Translation
        t0 = time.perf_counter()
        translations = []
        for idx, item in enumerate(extraction.items):
            match = rag_matches[idx]
            rag_record: Optional[DishRecord] = match.dish if match else None
            trans = await self.translator.translate_dish(
                original_name=item.original_name,
                printed_desc=item.subtitle_or_description or "",
                target_language=target_language,
                rag_record=rag_record,
                price=item.price_display,
            )
            translations.append(trans)
        stages.append(StageTiming(stage="contextual_translation", duration_ms=round((time.perf_counter() - t0) * 1000, 2)))

        # Stage 6: Allergen Reasoning & Dietary Safety Cross-Check
        t0 = time.perf_counter()
        enriched_dishes: List[AnalyzedDish] = []
        all_verified = True

        for idx, item in enumerate(extraction.items):
            match = rag_matches[idx]
            rag_record = match.dish if match else None
            trans = translations[idx]

            is_verified = (rag_record is not None and rag_record.verification_status == "verified")
            if not is_verified:
                all_verified = False

            # Extract base ingredients
            if rag_record and rag_record.ingredients:
                ingredients = [i.name for i in rag_record.ingredients]
            elif rag_record and rag_record.base_ingredients:
                ingredients = rag_record.base_ingredients
            elif item.subtitle_or_description:
                ingredients = [i.strip() for i in item.subtitle_or_description.split(",") if i.strip()]
            else:
                ingredients = []

            # Grounded Allergen Assessment
            allergens = CulinarySafetyEngine.assess_allergens(
                original_name=item.original_name,
                printed_desc=item.subtitle_or_description or "",
                extracted_ingredients=ingredients,
                rag_record=rag_record,
            )

            # Tri-state dietary assessment
            dietary = CulinarySafetyEngine.evaluate_dietary_compatibility(
                original_name=item.original_name,
                printed_desc=item.subtitle_or_description or "",
                allergens=allergens,
                rag_record=rag_record,
            )

            # Calculate user dietary conflicts
            conflicts = CulinarySafetyEngine.calculate_user_conflicts(
                dietary=dietary,
                allergens=allergens,
                user_restrictions=user_restrictions,
            )
            dietary.user_conflicts = conflicts

            evidence_status = (
                EvidenceStatus.CONFIRMED if is_verified else EvidenceStatus.UNVERIFIED
            )

            analyzed = AnalyzedDish(
                dish_id=item.id,
                reading_order=item.reading_order,
                section=item.section,
                bounding_box=item.bounding_box,
                original_text=item.original_name,
                phonetic_transcription=trans.phonetic_transcription or item.phonetic_transcription,
                translated_title=trans.translated_title,
                culinary_description=trans.culinary_description or item.subtitle_or_description,
                flavor_profile=trans.flavor_profile,
                key_ingredients=ingredients,
                allergen_warnings=allergens,
                dietary_compatibility=dietary,
                price=item.price_display,
                currency=item.currency,
                evidence_status=evidence_status,
            )
            enriched_dishes.append(analyzed)

        stages.append(StageTiming(stage="dietary_safety_evaluation", duration_ms=round((time.perf_counter() - t0) * 1000, 2)))

        total_latency_ms = round((time.perf_counter() - total_start) * 1000, 2)

        # Determine retrieval status
        if len(enriched_dishes) == 0:
            retrieval_status = "no_dishes"
        elif retrieval_hits == len(enriched_dishes):
            retrieval_status = "rag_hybrid_complete"
        elif retrieval_hits > 0:
            retrieval_status = "rag_hybrid_partial"
        else:
            retrieval_status = "rag_no_matches_fallback_unverified"

        menu_meta = MenuMetadata(
            source_language=extraction.source_language,
            target_language=target_language,
            image_width=extraction.original_width,
            image_height=extraction.original_height,
            dish_count=len(enriched_dishes),
            restaurant_id=restaurant_id,
            warnings=extraction.warnings,
        )

        processing_meta = ProcessingMetadata(
            request_id=request_id,
            total_latency_ms=total_latency_ms,
            model_name=self.settings.vision_model,
            retrieval_status=retrieval_status,
            stages=stages,
            diagnostics={
                "applied_clahe": apply_clahe,
                "user_restrictions_evaluated": user_restrictions,
                "retrieval_hits": retrieval_hits,
                "all_verified": all_verified,
            },
        )

        safety_disclaimer = (
            "SAFETY NOTICE: Always confirm preparation details with restaurant staff if you have severe allergies."
            if all_verified
            else (
                "CRITICAL ALLERGEN NOTICE: Unverified ingredients and allergens are estimated from printed text. "
                "Never rely solely on automated translation for life-threatening allergies. Confirm all items with restaurant staff."
            )
        )

        return MenuAnalysisResponse(
            menu_metadata=menu_meta,
            dishes=enriched_dishes,
            processing_metadata=processing_meta,
            safety_disclaimer=safety_disclaimer,
        )

"""Pipeline Orchestration service for Menu Analysis with hybrid RAG enrichment."""

import time
import uuid
from typing import Any, List, Optional, Tuple
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.extraction import MenuExtractionResult, MenuTextBlock
from backend.app.schemas.menu_analysis import (
    AllergenWarning,
    AnalyzedDish,
    DietaryCompatibility,
    DietaryFlagStatus,
    EvidenceStatus,
    MenuAnalysisResponse,
    MenuMetadata,
    ProcessingMetadata,
    StageTiming,
    SupportedLanguage,
)
from backend.app.services.image_processor import ImageProcessor
from backend.app.services.rag.retriever import CulinaryRetriever
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.app.services.vision.provider import MenuVisionProvider


class MenuPipelineOrchestrator:
    """Orchestrates ingestion, extraction, hybrid RAG enrichment, and safety validation."""

    def __init__(
        self,
        vision_provider: Optional[MenuVisionProvider] = None,
        retriever: Optional[CulinaryRetriever] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.vision_provider = vision_provider or OllamaVisionProvider(settings=self.settings)
        self.retriever = retriever or CulinaryRetriever()

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

        # Stage 4: Hybrid RAG Culinary Knowledge Enrichment
        t0 = time.perf_counter()
        enriched_dishes: List[AnalyzedDish] = []
        retrieval_hits = 0
        for item in extraction.items:
            dish, was_hit = self._enrich_dish(item, target_language, user_restrictions, restaurant_id=restaurant_id)
            enriched_dishes.append(dish)
            if was_hit:
                retrieval_hits += 1
        stages.append(StageTiming(stage="culinary_enrichment_rag", duration_ms=round((time.perf_counter() - t0) * 1000, 2)))

        # Stage 5 & 6: Translation & Dietary Cross-Checking
        t0 = time.perf_counter()
        for dish in enriched_dishes:
            self._evaluate_dietary_conflicts(dish, user_restrictions)
        stages.append(StageTiming(stage="dietary_evaluation", duration_ms=round((time.perf_counter() - t0) * 1000, 2)))

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
            },
        )

        return MenuAnalysisResponse(
            menu_metadata=menu_meta,
            dishes=enriched_dishes,
            processing_metadata=processing_meta,
        )

    def _enrich_dish(
        self,
        item: MenuTextBlock,
        target_language: SupportedLanguage,
        user_restrictions: List[str],
        restaurant_id: Optional[str] = None,
    ) -> Tuple[AnalyzedDish, bool]:
        """Enrich extracted dish with authoritative culinary knowledge from hybrid RAG when available."""
        retrieved = self.retriever.retrieve_dish(item.original_name, restaurant_id=restaurant_id)

        if retrieved is not None and retrieved.is_authoritative:
            d = retrieved.dish
            is_verified = (d.verification_status == "verified")
            evidence_status = EvidenceStatus.CONFIRMED if is_verified else EvidenceStatus.UNVERIFIED

            # Key ingredients from structured record
            ingredients = [ing.name for ing in d.ingredients] or d.base_ingredients or []
            if not ingredients and item.subtitle_or_description:
                ingredients = [i.strip() for i in item.subtitle_or_description.split(",") if i.strip()]

            # Grounded allergen warnings
            allergens: List[AllergenWarning] = []
            for all_ev in d.allergen_evidence:
                st = EvidenceStatus.CONFIRMED if (is_verified and all_ev.status == "contains") else EvidenceStatus.POSSIBLE
                allergens.append(
                    AllergenWarning(
                        allergen=all_ev.allergen,
                        status=st,
                        source=all_ev.evidence_source,
                        notes=f"Culinary KB [{all_ev.status}]: {all_ev.reviewer_metadata or 'Verified Record'}",
                    )
                )

            # Map dietary flags
            flags = d.dietary_flags or {}
            def map_flag(val: Any) -> DietaryFlagStatus:
                if val is True:
                    return DietaryFlagStatus.YES
                elif val is False:
                    return DietaryFlagStatus.NO
                elif val == "possible":
                    return DietaryFlagStatus.POSSIBLE
                return DietaryFlagStatus.UNKNOWN

            dietary = DietaryCompatibility(
                vegan=map_flag(flags.get("is_vegan")),
                vegetarian=map_flag(flags.get("is_vegetarian")),
                gluten_free=map_flag(flags.get("is_gluten_free")),
                halal=map_flag(flags.get("is_halal")),
                confidence_notes=f"Grounded by culinary KB record '{d.dish_id}' ({d.verification_status}, RRF: {retrieved.rrf_score})",
            )

            analyzed = AnalyzedDish(
                dish_id=item.id,
                reading_order=item.reading_order,
                section=item.section,
                bounding_box=item.bounding_box,
                original_text=item.original_name,
                phonetic_transcription=d.phonetic_spelling or item.phonetic_transcription,
                translated_title=f"{item.original_name} (Target: {target_language.value})",
                culinary_description=d.cultural_narrative or item.subtitle_or_description,
                flavor_profile=d.flavor_profile,
                key_ingredients=ingredients,
                allergen_warnings=allergens,
                dietary_compatibility=dietary,
                price=item.price_display,
                currency=item.currency,
                evidence_status=evidence_status,
            )
            return analyzed, True

        # Fallback when no authoritative match is retrieved:
        # Ground strictly in printed text, mark evidence as UNVERIFIED, never claim false safety
        raw_desc = item.subtitle_or_description or ""
        ingredients = [i.strip() for i in raw_desc.split(",") if i.strip()] if raw_desc else []

        allergen_keywords = {
            "gluten": ["flour", "pasta", "bread", "wheat", "crust", "toast", "semolina"],
            "dairy": ["cream", "milk", "butter", "cheese", "parmigiano", "mozzarella", "ricotta"],
            "nuts": ["nut", "almond", "walnut", "hazelnut", "pistachio", "pine nut"],
            "shellfish": ["clam", "shrimp", "squid", "calamari", "prawn", "crab", "lobster"],
            "eggs": ["egg", "tagliatelle"],
        }

        allergens = []
        lower_desc = (item.original_name + " " + raw_desc).lower()
        for allergen, keywords in allergen_keywords.items():
            if any(k in lower_desc for k in keywords):
                allergens.append(
                    AllergenWarning(
                        allergen=allergen,
                        status=EvidenceStatus.POSSIBLE,
                        source="printed_menu_text",
                        notes=f"Keyword match from printed description: '{raw_desc}'",
                    )
                )

        is_meat = any(w in lower_desc for w in ["beef", "ragù", "ragu", "pork", "chicken", "meat", "bacon", "prosciutto", "squid", "clam", "fish"])
        is_dairy = any(w in lower_desc for w in ["cheese", "cream", "butter", "parmigiano", "mozzarella", "milk"])

        dietary = DietaryCompatibility(
            vegan=DietaryFlagStatus.NO if (is_meat or is_dairy) else DietaryFlagStatus.UNKNOWN,
            vegetarian=DietaryFlagStatus.NO if is_meat else DietaryFlagStatus.UNKNOWN,
            gluten_free=DietaryFlagStatus.NO if any(w in lower_desc for w in ["pasta", "bread", "flour"]) else DietaryFlagStatus.UNKNOWN,
            halal=DietaryFlagStatus.NO if "pork" in lower_desc else DietaryFlagStatus.UNKNOWN,
            confidence_notes="Unmatched against culinary KB; unverified machine extraction.",
        )

        analyzed = AnalyzedDish(
            dish_id=item.id,
            reading_order=item.reading_order,
            section=item.section,
            bounding_box=item.bounding_box,
            original_text=item.original_name,
            phonetic_transcription=item.phonetic_transcription,
            translated_title=f"{item.original_name} (Target: {target_language.value})",
            culinary_description=item.subtitle_or_description,
            flavor_profile=None,
            key_ingredients=ingredients,
            allergen_warnings=allergens,
            dietary_compatibility=dietary,
            price=item.price_display,
            currency=item.currency,
            evidence_status=EvidenceStatus.UNVERIFIED,
        )
        return analyzed, False

    def _evaluate_dietary_conflicts(
        self,
        dish: AnalyzedDish,
        user_restrictions: List[str],
    ) -> None:
        """Cross-check user restrictions and flag conflicts without claiming false safety."""
        conflicts: List[str] = []
        lower_text = (dish.original_text + " " + (dish.culinary_description or "")).lower()

        for restriction in user_restrictions:
            if "vegan" in restriction:
                if dish.dietary_compatibility.vegan == DietaryFlagStatus.NO:
                    conflicts.append("Non-vegan ingredients detected")
            elif "vegetarian" in restriction:
                if dish.dietary_compatibility.vegetarian == DietaryFlagStatus.NO:
                    conflicts.append("Meat or seafood detected")
            elif "gluten" in restriction:
                if any(w.allergen == "gluten" for w in dish.allergen_warnings) or "pasta" in lower_text or "wheat" in lower_text:
                    conflicts.append("Gluten containing ingredients detected")
            elif "dairy" in restriction:
                if any(w.allergen == "dairy" for w in dish.allergen_warnings) or "cheese" in lower_text or "butter" in lower_text:
                    conflicts.append("Dairy ingredients detected")
            elif "nut" in restriction:
                if any(w.allergen == "nuts" for w in dish.allergen_warnings):
                    conflicts.append("Nut ingredients detected")

        dish.dietary_compatibility.user_conflicts = conflicts

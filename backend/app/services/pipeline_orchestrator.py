"""Pipeline Orchestration service for Menu Analysis with hybrid RAG, contextual translation,
and evidence-grounded allergen safety evaluations.
"""

import logging
import re
import time
import uuid
from typing import Any, List, Optional, Tuple

logger = logging.getLogger("menu_translator.pipeline_orchestrator")

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
from backend.app.services.safety.description_sanitizer import DescriptionSanitizer
from backend.app.services.safety.safety_engine import CulinarySafetyEngine
from backend.app.services.translation.translator import (
    CulinaryTranslatorService,
    OllamaTranslationProvider,
)
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.app.services.vision.provider import MenuVisionProvider


def is_valid_rag_match(query_name: str, rag_record: Any) -> bool:
    """Ensure RAG record actually matches the query dish name or alias.
    Prevents cross-cuisine hijacking (e.g. Gong Cha milk tea matching Pizza Margherita or Matcha Ice Cream).
    """
    if not rag_record or not query_name:
        return False

    q = re.sub(r"[#*_:\-\[\]\(\)&/]", " ", query_name).strip().lower()
    q = re.sub(r"\s+", " ", q)
    if len(q) < 3:
        return False

    native = getattr(rag_record, "native_name", "") or ""
    n = re.sub(r"[#*_:\-\[\]\(\)&/]", " ", native).strip().lower()
    n = re.sub(r"\s+", " ", n)

    if q == n:
        return True

    aliases = getattr(rag_record, "aliases", []) or []
    for a in aliases:
        if isinstance(a, str):
            al = re.sub(r"[#*_:\-\[\]\(\)&/]", " ", a).strip().lower()
            al = re.sub(r"\s+", " ", al)
            if q == al:
                return True

    # Multi-token matching: prevent 1-word generic substrings ("tea", "ice") from hijacking dishes
    stopwords = {"the", "a", "an", "de", "la", "le", "and", "&", "special", "top", "row", "dish", "item", "tea", "iced", "hot"}
    q_tokens = set(q.split()) - stopwords
    n_tokens = set(n.split()) - stopwords

    if len(q_tokens) >= 2 and len(n_tokens) >= 2:
        if q_tokens == n_tokens:
            return True
        intersection = q_tokens.intersection(n_tokens)
        if len(intersection) >= 2 and len(intersection) / max(len(q_tokens), len(n_tokens)) >= 0.7:
            return True

    return False



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
        self.translator = translator or CulinaryTranslatorService(
            provider=OllamaTranslationProvider(settings=self.settings),
            use_deterministic_only=False,
        )

    async def run_pipeline(
        self,
        image_bytes: bytes,
        mime_type: str,
        target_language: SupportedLanguage = SupportedLanguage.EN,
        user_dietary_restrictions: Optional[List[str]] = None,
        restaurant_id: Optional[str] = None,
        apply_clahe: bool = False,
        rotation: int = 0,
    ) -> MenuAnalysisResponse:
        """Execute end-to-end analysis with stage timing and evidence tracking."""
        total_start = time.perf_counter()
        request_id = str(uuid.uuid4())
        stages: List[StageTiming] = []
        user_restrictions = user_dietary_restrictions or []

        # Stage 1: Upload and Decoding
        t0 = time.perf_counter()
        pil_img = ImageProcessor.validate_and_decode(
            image_bytes=image_bytes,
            max_size_mb=self.settings.max_upload_size_mb,
            rotation=rotation,
        )
        decoding_ms = round((time.perf_counter() - t0) * 1000, 2)
        stages.append(StageTiming(stage="upload_and_decoding", duration_ms=decoding_ms, request_id=request_id))
        logger.info(f"[{request_id}] Stage 'upload_and_decoding' completed in {decoding_ms}ms")

        # Stage 2: Image Preprocessing
        t0 = time.perf_counter()
        preprocessed = ImageProcessor.preprocess_for_vlm(
            image=pil_img,
            max_dimension=self.settings.image_max_dimension,
            apply_clahe=apply_clahe,
        )
        preprocessing_ms = round((time.perf_counter() - t0) * 1000, 2)
        stages.append(StageTiming(stage="preprocessing", duration_ms=preprocessing_ms, request_id=request_id))
        stages.append(StageTiming(stage="image_preprocessing", duration_ms=preprocessing_ms, request_id=request_id))
        logger.info(f"[{request_id}] Stage 'image_preprocessing' completed in {preprocessing_ms}ms")

        # Stage 3, 4, 5: Visual Extraction with Ollama Telemetry
        extract_kwargs = {
            "image_bytes": image_bytes,
            "mime_type": mime_type,
            "metadata": {"menu_id": request_id},
            "apply_clahe": apply_clahe,
            "rotation": rotation,
            "preprocessed": preprocessed,
        }
        try:
            extraction: MenuExtractionResult = await self.vision_provider.extract_menu(**extract_kwargs)
        except TypeError:
            extract_kwargs.pop("preprocessed", None)
            extraction = await self.vision_provider.extract_menu(**extract_kwargs)

        ext_meta = getattr(extraction, "metadata", {}) or {}
        model_startup_ms = float(ext_meta.get("load_duration_ms", 0.0))
        stages.append(StageTiming(stage="model_startup_or_loading", duration_ms=model_startup_ms, request_id=request_id))
        logger.info(f"[{request_id}] Stage 'model_startup_or_loading' completed in {model_startup_ms}ms")

        vision_inference_ms = float(ext_meta.get("inference_wall_ms", extraction.processing_time_ms))
        stages.append(StageTiming(stage="visual_extraction", duration_ms=vision_inference_ms, request_id=request_id))
        stages.append(StageTiming(stage="vision_inference", duration_ms=vision_inference_ms, request_id=request_id))
        logger.info(f"[{request_id}] Stage 'vision_inference' completed in {vision_inference_ms}ms")

        parsing_ms = float(ext_meta.get("parsing_duration_ms", 1.0))
        stages.append(StageTiming(stage="structured_output_parsing", duration_ms=parsing_ms, request_id=request_id))
        logger.info(f"[{request_id}] Stage 'structured_output_parsing' completed in {parsing_ms}ms")

        # Filter out watermarks, blog stamps, and clean section titles
        t_val_start = time.perf_counter()
        sanitized_items = []
        for it in extraction.items:
            if DescriptionSanitizer.is_watermark_or_artifact(it.original_name):
                logger.info(f"Filtered out watermark artifact: '{it.original_name}'")
                continue
            it.section = DescriptionSanitizer.clean_section_title(it.section)
            sanitized_items.append(it)
        extraction.items = sanitized_items

        # Deduplicate items across promotional and main categories
        promotional_sections = {"BEST SELLER", "BEST SELLERS", "SIGNATURE", "NEW", "SEASON MENU", "SEASONAL MENU"}
        unique_items = []
        seen_dishes = {}  # (norm_name, price) -> item_idx

        for item in extraction.items:
            norm_name = re.sub(r"\s+", " ", item.original_name.strip().lower())
            p_key = (norm_name, item.price_display or "")
            if p_key in seen_dishes:
                prev_idx = seen_dishes[p_key]
                prev_item = unique_items[prev_idx]
                if prev_item.section and prev_item.section.upper() in promotional_sections and item.section and item.section.upper() not in promotional_sections:
                    prev_item.section = item.section
                continue
            seen_dishes[p_key] = len(unique_items)
            unique_items.append(item)
        extraction.items = unique_items

        # Hybrid RAG Culinary Knowledge Retrieval
        t_rag_start = time.perf_counter()
        rag_matches: List[Optional[Any]] = []
        retrieval_hits = 0
        for item in extraction.items:
            retrieved = self.retriever.retrieve_dish(item.original_name, restaurant_id=restaurant_id)
            if retrieved is not None and retrieved.is_authoritative and is_valid_rag_match(item.original_name, retrieved.dish):
                rag_matches.append(retrieved)
                retrieval_hits += 1
            else:
                rag_matches.append(None)
        rag_ms = round((time.perf_counter() - t_rag_start) * 1000, 2)
        stages.append(StageTiming(stage="culinary_enrichment_rag", duration_ms=rag_ms, request_id=request_id))
        logger.info(f"[{request_id}] Stage 'culinary_enrichment_rag' completed in {rag_ms}ms")

        # Stage 6: Translation (Contextual & Universal Multilingual Engine)
        t_trans_start = time.perf_counter()
        batch_items = []
        for i, item in enumerate(extraction.items):
            is_valid_desc, clean_printed_desc, _ = DescriptionSanitizer.validate_and_clean_description(
                item.subtitle_or_description,
                dish_name=item.original_name,
                section=item.section,
            )
            batch_items.append(
                {
                    "original_name": item.original_name,
                    "printed_desc": clean_printed_desc if is_valid_desc else "",
                    "price": item.price_display,
                    "rag_record": rag_matches[i].dish if rag_matches[i] else None,
                }
            )

        translations = await self.translator.translate_batch(
            items=batch_items,
            target_language=target_language,
        )
        translation_ms = round((time.perf_counter() - t_trans_start) * 1000, 2)
        stages.append(StageTiming(stage="contextual_translation", duration_ms=translation_ms, request_id=request_id))
        stages.append(StageTiming(stage="translation", duration_ms=translation_ms, request_id=request_id))
        logger.info(f"[{request_id}] Stage 'translation' completed in {translation_ms}ms")

        # Stage 6: Allergen Reasoning & Dietary Safety Cross-Check & Strict Field Semantics
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

            # Extract promotional / category tags (e.g. Best Seller, New, Signature)
            tags = DescriptionSanitizer.extract_tags(item.original_name, item.section)

            # Sanitize original printed description
            is_valid_orig_desc, clean_orig_desc, _ = DescriptionSanitizer.validate_and_clean_description(
                item.subtitle_or_description,
                dish_name=item.original_name,
                section=item.section,
            )
            final_orig_desc = clean_orig_desc if is_valid_orig_desc else None

            # Determine translated culinary description
            final_culinary_desc = None
            generated_desc = None

            if final_orig_desc:
                # If there was an authentic printed description, validate and use translation
                is_valid_trans_desc, clean_trans_desc, _ = DescriptionSanitizer.validate_and_clean_description(
                    trans.culinary_description,
                    dish_name=item.original_name,
                    section=item.section,
                )
                final_culinary_desc = clean_trans_desc if is_valid_trans_desc else final_orig_desc
            else:
                # Case B: No printed description. Never invent one or use filler.
                final_culinary_desc = None

            # Optional AI/authoritative cultural narrative clearly segregated from printed description
            if is_verified and rag_record and getattr(rag_record, "cultural_narrative", None):
                generated_desc = rag_record.cultural_narrative

            # Extract base ingredients ONLY when verified by trusted RAG or explicitly printed
            # A dish description is NEVER treated as an ingredient list
            ingredients_verified_list = []
            ingredients_translated_list = []
            if is_verified and rag_record:
                if rag_record.ingredients:
                    ingredients_verified_list = [i.name for i in rag_record.ingredients]
                elif rag_record.base_ingredients:
                    ingredients_verified_list = rag_record.base_ingredients
                ingredients_translated_list = ingredients_verified_list
                ingredient_evidence_status = EvidenceStatus.CONFIRMED
            else:
                ingredient_evidence_status = EvidenceStatus.NOT_LISTED

            # Grounded Allergen Assessment
            allergens = CulinarySafetyEngine.assess_allergens(
                original_name=item.original_name,
                printed_desc=final_orig_desc or "",
                extracted_ingredients=ingredients_verified_list,
                rag_record=rag_record,
            )

            # Tri-state dietary assessment
            dietary = CulinarySafetyEngine.evaluate_dietary_compatibility(
                original_name=item.original_name,
                printed_desc=final_orig_desc or "",
                allergens=allergens,
                rag_record=rag_record,
            )

            # Calculate user dietary conflicts
            conflicts = CulinarySafetyEngine.calculate_user_conflicts(
                dietary=dietary,
                allergens=allergens,
                user_restrictions=user_restrictions,
                extracted_ingredients=ingredients_verified_list,
                rag_record=rag_record,
            )
            dietary.user_conflicts = conflicts

            evidence_status = (
                EvidenceStatus.CONFIRMED if is_verified else EvidenceStatus.UNVERIFIED
            )

            # Parse numeric price value and currency
            raw_price_str = item.price_display
            parsed_price_val = None
            price_currency_sym = item.currency
            if raw_price_str:
                num_match = re.search(r"(\d+(?:[.,]\d+)?)", raw_price_str)
                if num_match:
                    try:
                        parsed_price_val = float(num_match.group(1).replace(",", "."))
                    except ValueError:
                        parsed_price_val = None
                if not price_currency_sym:
                    for sym in ["₩", "$", "€", "£", "¥", "CHF"]:
                        if sym in raw_price_str:
                            price_currency_sym = sym
                            break

            dietary_evidence = {
                "vegan": "Verified by recipe database" if is_verified else "Ingredients not listed on menu; unverified",
                "vegetarian": "Verified by recipe database" if is_verified else "Ingredients not listed on menu; unverified",
                "gluten_free": "Verified by recipe database" if is_verified else "Ingredients not listed on menu; unverified",
                "halal": "Verified by recipe database" if is_verified else "Ingredients not listed on menu; unverified",
            }

            analyzed = AnalyzedDish(
                dish_id=item.id,
                id=item.id,
                reading_order=item.reading_order,
                section=item.section,
                category=item.section,
                section_original=item.section,
                tags=tags,
                bounding_box=item.bounding_box,
                original_text=item.original_name,
                original_name=item.original_name,
                original_description=final_orig_desc,
                phonetic_transcription=trans.phonetic_transcription or item.phonetic_transcription,
                transliteration=trans.phonetic_transcription or item.phonetic_transcription,
                translated_title=trans.translated_title,
                translated_name=trans.translated_title,
                culinary_description=final_culinary_desc,
                translated_description=final_culinary_desc,
                generated_description=generated_desc,
                flavor_profile=trans.flavor_profile,
                key_ingredients=ingredients_verified_list,
                ingredients_original=[],
                ingredients_translated=ingredients_translated_list,
                ingredients_verified=ingredients_verified_list,
                ingredient_evidence_status=ingredient_evidence_status,
                allergen_warnings=allergens,
                allergens=allergens,
                dietary_compatibility=dietary,
                dietary_evidence=dietary_evidence,
                price=raw_price_str,
                price_text_original=raw_price_str,
                price_value=parsed_price_val,
                currency=price_currency_sym,
                price_currency=price_currency_sym,
                confidence=0.95 if is_verified else 0.90,
                evidence_status=evidence_status,
            )
            enriched_dishes.append(analyzed)

        # Stage 7: Validation and Deduplication
        val_ms = round((time.perf_counter() - t0) * 1000, 2)
        stages.append(StageTiming(stage="dietary_safety_evaluation", duration_ms=val_ms, request_id=request_id))
        stages.append(StageTiming(stage="validation_and_deduplication", duration_ms=val_ms, request_id=request_id))
        logger.info(f"[{request_id}] Stage 'validation_and_deduplication' completed in {val_ms}ms")

        # Stage 8: API Serialization and Response Assembly
        t_ser_start = time.perf_counter()

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

        total_latency_ms = round((time.perf_counter() - total_start) * 1000, 2)
        ser_ms = round((time.perf_counter() - t_ser_start) * 1000, 2)
        stages.append(StageTiming(stage="api_serialization", duration_ms=ser_ms, request_id=request_id))
        logger.info(f"[{request_id}] Stage 'api_serialization' completed in {ser_ms}ms (Total latency: {total_latency_ms}ms)")

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
                "eval_tokens": ext_meta.get("eval_tokens", 0),
                "prompt_tokens": ext_meta.get("prompt_tokens", 0),
                "tokens_per_second": ext_meta.get("tokens_per_second", 0.0),
                "model_residency": ext_meta.get("model_residency", "unknown"),
                "done_reason": ext_meta.get("done_reason", "unknown"),
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

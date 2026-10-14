"""Defensive parsing, sanitization, and coordinate mapping for model JSON output."""

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from backend.app.core.exceptions import ModelInferenceError
from backend.app.schemas.extraction import (
    BoundingBox,
    ExtractionWarning,
    MenuTextBlock,
)
from backend.app.services.image_processor import ImageProcessor

logger = logging.getLogger("menu_translator.json_parser")

# Regex to find JSON object or array within conversational text
JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
TRAILING_COMMA_PATTERN = re.compile(r",\s*([}\]])")


class ModelJsonParser:
    """Robust parser that cleans, validates, and normalizes VLM extraction JSON."""

    @classmethod
    def clean_raw_output(cls, raw_text: str) -> str:
        """Strip markdown fences, leading/trailing commentary, and fix trailing commas."""
        text = raw_text.strip()

        # Check for markdown code fences
        match = JSON_BLOCK_PATTERN.search(text)
        if match:
            text = match.group(1).strip()
        else:
            # If no code fence, locate first '{' and last '}'
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1].strip()

        # Clean trailing commas which are invalid in JSON but common in LLM outputs
        text = TRAILING_COMMA_PATTERN.sub(r"\1", text)
        return text

    @classmethod
    def parse_and_validate(
        cls,
        raw_output: str,
        orig_width: int,
        orig_height: int,
    ) -> Tuple[Optional[str], List[MenuTextBlock], List[ExtractionWarning]]:
        """
        Parse model output into validated MenuTextBlock items and extraction warnings.
        Returns: (source_language, items, warnings)
        """
        cleaned_json = cls.clean_raw_output(raw_output)
        warnings: List[ExtractionWarning] = []

        try:
            data = json.loads(cleaned_json)
        except json.JSONDecodeError as err:
            logger.warning(f"Initial JSON parse failed: {err}. Attempting secondary recovery.")
            # Attempt basic single-quote replacement if double quotes were swapped
            try:
                fixed = cleaned_json.replace("'", '"')
                data = json.loads(fixed)
                warnings.append(
                    ExtractionWarning(
                        code="JSON_QUOTES_REPAIRED",
                        message="Recovered JSON by standardizing string quotes",
                    )
                )
            except Exception:
                raise ModelInferenceError(
                    message="Model returned malformed JSON that could not be parsed",
                    details={"error_snippet": str(err), "clean_length": len(cleaned_json)},
                )

        if not isinstance(data, dict):
            # If the model returned a bare list of items
            if isinstance(data, list):
                raw_items = data
                detected_lang = None
            else:
                raise ModelInferenceError(
                    message="Model output did not contain a valid JSON object or item list"
                )
        else:
            detected_lang = data.get("source_language")
            raw_items = data.get("items", [])

        if not isinstance(raw_items, list):
            raw_items = []

        items: List[MenuTextBlock] = []
        for idx, item in enumerate(raw_items):
            if not isinstance(item, dict):
                continue

            name = str(item.get("original_name") or item.get("name") or "").strip()
            if not name:
                warnings.append(
                    ExtractionWarning(
                        code="SKIPPED_EMPTY_NAME",
                        message=f"Item at index {idx} lacked dish name and was skipped",
                    )
                )
                continue

            # Extract box coordinates safely
            box = cls._parse_box(item, orig_width, orig_height, idx, warnings)

            reading_order = item.get("reading_order")
            if not isinstance(reading_order, int):
                reading_order = idx + 1

            price = item.get("price_display") or item.get("price")
            price_str = str(price).strip() if price is not None else None

            currency = item.get("currency")
            if not currency and price_str:
                for symbol in ["€", "$", "¥", "£", "CHF"]:
                    if symbol in price_str:
                        currency = symbol
                        break

            region_type = str(item.get("text_region_type") or "dish_item").strip().lower()
            if region_type not in ["dish_item", "heading", "description", "price", "other"]:
                region_type = "dish_item"

            menu_block = MenuTextBlock(
                id=str(uuid.uuid4())[:8],
                reading_order=reading_order,
                section=item.get("section"),
                original_name=name,
                phonetic_transcription=item.get("phonetic_transcription"),
                subtitle_or_description=item.get("subtitle_or_description") or item.get("description"),
                price_display=price_str,
                currency=currency,
                text_region_type=region_type,
                bounding_box=box,
                confidence=float(item["confidence"]) if "confidence" in item and isinstance(item["confidence"], (int, float)) else None,
                uncertainty_notes=item.get("uncertainty_notes"),
            )
            items.append(menu_block)

        # Ensure reading order is monotonically assigned if not set by model
        items.sort(key=lambda x: x.reading_order)
        for i, itm in enumerate(items):
            itm.reading_order = i + 1

        if not items:
            warnings.append(
                ExtractionWarning(
                    code="EMPTY_EXTRACTION",
                    message="No legible dishes could be extracted from the provided menu image",
                )
            )

        return detected_lang, items, warnings

    @classmethod
    def _parse_box(
        cls,
        item: Dict[str, Any],
        orig_width: int,
        orig_height: int,
        idx: int,
        warnings: List[ExtractionWarning],
    ) -> BoundingBox:
        """Parse box coordinates from diverse VLM formats (box_2d, bbox, xmin/ymin dict)."""
        box_data = item.get("box_2d") or item.get("bbox") or item.get("bounding_box")

        if isinstance(box_data, (list, tuple)) and len(box_data) >= 4:
            # Qwen-VL native format is [ymin, xmin, ymax, xmax]
            # Some other VLMs use [xmin, ymin, xmax, ymax]
            c1, c2, c3, c4 = float(box_data[0]), float(box_data[1]), float(box_data[2]), float(box_data[3])
            # Determine if it's [ymin, xmin, ymax, xmax] standard
            ymin, xmin, ymax, xmax = c1, c2, c3, c4
            return ImageProcessor.map_normalized_box(
                xmin=xmin,
                ymin=ymin,
                xmax=xmax,
                ymax=ymax,
                orig_width=orig_width,
                orig_height=orig_height,
            )

        if isinstance(box_data, dict):
            xmin = float(box_data.get("xmin", 0))
            ymin = float(box_data.get("ymin", 0))
            xmax = float(box_data.get("xmax", 1000))
            ymax = float(box_data.get("ymax", 1000))
            return ImageProcessor.map_normalized_box(
                xmin=xmin,
                ymin=ymin,
                xmax=xmax,
                ymax=ymax,
                orig_width=orig_width,
                orig_height=orig_height,
            )

        # Fallback bounding box if model omitted coordinates
        warnings.append(
            ExtractionWarning(
                code="MISSING_BBOX",
                message=f"Item '{item.get('original_name', '')}' omitted bounding box. Assigned default bounds.",
                details={"item_index": idx},
            )
        )
        return BoundingBox(xmin=0.0, ymin=0.0, xmax=1.0, ymax=1.0).to_pixel_box(orig_width, orig_height)

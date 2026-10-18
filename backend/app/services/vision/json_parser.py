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
from backend.app.services.safety.description_sanitizer import DescriptionSanitizer

logger = logging.getLogger("menu_translator.json_parser")

# Comprehensive multilingual section headers and category banners to prevent them becoming fake dishes
NORMALIZED_SECTION_HEADERS = {
    # English
    "new salty sweet",
    "new salty and sweet",
    "new",
    "season menu",
    "seasonal menu",
    "seasonal specials",
    "best seller",
    "best sellers",
    "signature",
    "signatures",
    "original tea",
    "milk tea",
    "smoothie",
    "coffee",
    "fruit tea more",
    "fruit tea",
    "sweet grade",
    "toppings",
    "beverages",
    "drinks",
    "appetizers",
    "mains",
    "main courses",
    "desserts",
    "starters",
    "salads",
    "soups",
    "sides",
    "specials",
    "chef special",
    "popular",
    # Italian
    "antipasti",
    "primi",
    "secondi",
    "dolci",
    "bevande",
    "pizze",
    "contorni",
    # French
    "entrees",
    "entrées",
    "plats",
    "boissons",
    "vins",
    "carte des vins",
    # German
    "vorspeisen",
    "hauptgerichte",
    "getranke",
    "getränke",
    "nachspeisen",
    "beilagen",
    # Spanish
    "tapas",
    "raciones",
    "postres",
    "bebidas",
    "entrantes",
    "platos principales",
    # Asian scripts (CJK)
    "신메뉴",
    "시즌메뉴",
    "베스트",
    "베스트메뉴",
    "베스트셀러",
    "추천메뉴",
    "음료",
    "디저트",
    "식사류",
    "안주류",
    "주류",
    "季節限定",
    "おすすめ",
    "ドリンク",
    "デザート",
    "一品料理",
    "新品推荐",
    "招牌",
    "热销",
    "饮品",
    "甜点",
    "主食",
    # Arabic
    "المقبلات",
    "الأطباق الرئيسية",
    "المشروبات",
    "الحلويات",
}


def is_section_header(name: str) -> bool:
    """Check if a string represents a category banner, promotional heading, or section title."""
    if not name or not name.strip():
        return False
    clean = re.sub(r"[#*_:\-\[\]\(\)&/]", " ", name).strip().lower()
    clean = re.sub(r"\s+", " ", clean)
    if clean in NORMALIZED_SECTION_HEADERS:
        return True
    for header in NORMALIZED_SECTION_HEADERS:
        if clean == header or clean.startswith(f"{header} "):
            return True
    return False


def sanitize_dish_item(
    raw_name: str,
    raw_desc: Optional[str] = None,
    raw_price: Optional[str] = None,
) -> Tuple[str, Optional[str], Optional[str], bool]:
    """
    Sanitize and separate dish name, description, price, and category headers.
    Returns (cleaned_name, cleaned_desc, cleaned_price, is_header).
    Prevents model reasoning, schema labels, and fused fields from polluting dish entities.
    """
    if not raw_name or not raw_name.strip():
        return "", None, None, False

    text = raw_name.strip()

    # 1. Quick check for category headers without price
    if is_section_header(text) and not raw_price:
        return text, None, None, True

    # 2. Strip model reasoning/commentary in parentheses or brackets
    text = re.sub(r"\((?:but\s+)?wait[^\)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[(?:but\s+)?wait[^\]]*\]", "", text, flags=re.IGNORECASE)

    # 3. Strip trailing commentary phrases
    text = re.sub(r"[\.,;]?\s*(?:wait\s+)?looking\s+at\s+the\s+menu\b.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\.,;]?\s*(?:wait\s+)?the\s+image\s+might\b.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\.,;]?\s*wait\s+looking\b.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\.,;]?\s*wait\b.*$", "", text, flags=re.IGNORECASE)

    # 4. Strip prefix labels like "Name:", "Dish:", "Item:"
    text = re.sub(r"^(?:name|dish\s*name|dish|item|title|original_name)\s*:\s*", "", text, flags=re.IGNORECASE).strip()

    # If it was just "Description: ...", it is a description, not a dish!
    if re.match(r"^(?:description|desc|subtitle)\s*:\s*", text, flags=re.IGNORECASE):
        cleaned_desc = re.sub(r"^(?:description|desc|subtitle)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
        return "", cleaned_desc, raw_price, False

    desc = raw_desc.strip() if raw_desc else None
    price = raw_price.strip() if raw_price else None

    # Check if text is a watermark or blog stamp (e.g. 티스토리)
    if DescriptionSanitizer.is_watermark_or_artifact(text):
        return "", None, None, False

    # Check if desc is a watermark or blog stamp
    if desc and DescriptionSanitizer.is_watermark_or_artifact(desc):
        desc = None

    # Check if desc is actually a price string (e.g. 'price L6.1 J', 'L 6.1 / J', 'L 5.8 / J', '4.5 / 5.6')
    if desc and DescriptionSanitizer.is_price_like_string(desc):
        clean_p = re.sub(r"^(?:price|가격|금액)\s*[:\s]*", "", desc, flags=re.IGNORECASE).strip()
        if not price and clean_p:
            price = clean_p
        desc = None

    if price:
        price = re.sub(r"^(?:price|가격|금액)\s*[:\s]*", "", price, flags=re.IGNORECASE).strip()

    # 5. Check if model fused dish + description + price into name
    # e.g.: "Tea 스 브라운 - description: 시그니처 Milk Tea + 케러멜 - price L6.1 J"
    fused_match = re.search(
        r"^(.*?)\s*[-–—|]\s*(?:description|printed_desc|desc)\s*:\s*(.*?)(?:\s*[-–—|]\s*(?:price|price_display)\s*:\s*(.*))?$",
        text,
        re.IGNORECASE,
    )
    if fused_match:
        text = fused_match.group(1).strip()
        extracted_desc = fused_match.group(2).strip()
        extracted_price = fused_match.group(3).strip() if fused_match.group(3) else None
        if not desc and extracted_desc:
            desc = extracted_desc
        if not price and extracted_price:
            price = extracted_price

    # Check if price was appended like: "Tea 스 브라운 - 시그니처 Milk Tea + 케러멜 (L6.1 J)" or "Dish - 15.00€"
    price_tag_match = re.search(
        r"(?:\(\s*([LMRSJ]?\s*\d+(?:[.,]\d+)?)\s*\)|(?:\s*[-–—]\s*|\s+)([LMRSJ]\s*\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s*(?:원|₩|\$|€|£|¥|CHF)))\s*$",
        text,
        re.IGNORECASE,
    )
    if price_tag_match and not price:
        price = (price_tag_match.group(1) or price_tag_match.group(2) or "").strip()
        text = text[: price_tag_match.start()].strip(" -–—|()")

    # Check if a description was appended after a dash: "Tea 스 브라운 - 시그니처 Milk Tea + 케러멜"
    if " - " in text or " – " in text:
        parts = re.split(r"\s*[-–]\s*", text, maxsplit=1)
        if len(parts) == 2 and not desc:
            text = parts[0].strip()
            desc = parts[1].strip()

    # Clean up leftover punctuation
    text = text.strip(" -–—:|(),")
    if desc:
        desc = desc.strip(" -–—:|(),")
        if DescriptionSanitizer.is_price_like_string(desc):
            if not price:
                price = re.sub(r"^(?:price|가격|금액)\s*[:\s]*", "", desc, flags=re.IGNORECASE).strip()
            desc = None
    if price:
        price = price.strip(" -–—:|(),")

    # Double check if cleaned text is now a section header
    if is_section_header(text) and not price:
        return text, None, None, True

    return text, desc, price, False

# Regex to find JSON object or array within conversational text
JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
TRAILING_COMMA_PATTERN = re.compile(r",\s*([}\]])")


class ModelJsonParser:
    """Robust parser that cleans, validates, and normalizes VLM extraction JSON."""

    @classmethod
    def clean_raw_output(cls, raw_text: str) -> str:
        """Strip markdown fences, thinking tags, comments, and normalize delimiters."""
        if not raw_text or not raw_text.strip():
            return ""

        text = raw_text.strip()

        # 1. Strip <think>...</think> blocks if present in content
        text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()

        # 2. Extract from markdown code fences (both closed and open-ended)
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)(?:```|$)", text, re.IGNORECASE)
        if fence_match and fence_match.group(1).strip():
            extracted = fence_match.group(1).strip()
            if "{" in extracted or "[" in extracted:
                text = extracted

        # 3. Locate the target JSON object containing "items" (or fallback to outermost { ... })
        items_pos = text.rfind('"items"')
        if items_pos == -1:
            items_pos = text.rfind("'items'")
        if items_pos == -1:
            items_pos = text.rfind("items:")

        if items_pos != -1:
            start = text.rfind("{", 0, items_pos)
            if start != -1:
                end = text.rfind("}")
                if end != -1 and end > start:
                    text = text[start : end + 1]
                else:
                    text = text[start:]
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1:
                if end != -1 and end > start:
                    text = text[start : end + 1]
                else:
                    text = text[start:]

        # 4. Remove single-line // comments (not inside strings)
        text = re.sub(r"(?m)^\s*//.*$", "", text)
        text = re.sub(r"(?<!:)\s*//.*$", "", text)

        # 5. Fix trailing commas before } or ]
        text = re.sub(r",\s*([}\]])", r"\1", text)

        # 6. Normalize Python literals to JSON
        text = re.sub(r':\s*None\b', ': null', text)
        text = re.sub(r':\s*True\b', ': true', text)
        text = re.sub(r':\s*False\b', ': false', text)

        return text.strip()

    @classmethod
    def fix_syntax_flaws(cls, text: str) -> str:
        """Heuristic repairs for unquoted keys, single quotes, and trailing commas."""
        # Fix unquoted keys: e.g. { original_name: "..." } or , original_name:
        fixed = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
        # Fix single-quoted keys and string values
        fixed = re.sub(r"([{,]\s*)'([^']+)'\s*:", r'\1"\2":', fixed)
        fixed = re.sub(r':\s*\'([^\']*?)\'(?=\s*[,}\]])', r': "\1"', fixed)
        # Fix trailing commas
        fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
        return fixed

    @classmethod
    def attempt_truncation_recovery(cls, text: str) -> Optional[Any]:
        """Salvage fully completed items from a truncated model response."""
        last_brace = text.rfind("}")
        if last_brace == -1:
            return None

        candidate = text[: last_brace + 1].strip()
        candidate = re.sub(r",\s*$", "", candidate)

        open_brackets = candidate.count("[") - candidate.count("]")
        open_braces = candidate.count("{") - candidate.count("}")

        if open_brackets > 0 or open_braces > 0:
            candidate += ("]" * max(0, open_brackets)) + ("}" * max(0, open_braces))

        try:
            return json.loads(candidate)
        except Exception:
            try:
                fixed = cls.fix_syntax_flaws(candidate)
                return json.loads(fixed)
            except Exception:
                return None

    @classmethod
    def parse_unstructured_text(
        cls, text: str, orig_width: int, orig_height: int
    ) -> Optional[Tuple[Optional[str], List[MenuTextBlock], List[ExtractionWarning]]]:
        """Fallback to extract dish lines and sections from plain-text or markdown lists."""
        if not text or not text.strip():
            return None
        lines = text.splitlines()
        items: List[MenuTextBlock] = []
        warnings: List[ExtractionWarning] = [
            ExtractionWarning(
                code="UNSTRUCTURED_FALLBACK",
                message="Extracted menu items from text format because JSON was absent or malformed",
            )
        ]
        current_section = None
        price_pattern = re.compile(r"([₩$€£₺₹฿₫]?\s*\d+(?:[.,]\d+)?(?:\s*[\/\|]\s*\d+(?:[.,]\d+)?)?\s*(?:원|yen|euro|usd|gbp|chf)?)", re.IGNORECASE)

        for line in lines:
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("```"):
                continue

            # Detect section headers like ## ORIGINAL TEA or **ORIGINAL TEA** or ORIGINAL TEA:
            header_match = re.match(r"^(?:#{1,4}\s*|\*{1,2}|)(\b[A-Z\s&/]{3,30}\b)(?:\*{1,2}|:)?$", trimmed)
            if header_match:
                candidate = header_match.group(1).strip()
                if candidate not in {"JSON", "NOTE", "THINKING", "ITEMS", "MENU", "OUTPUT", "RESPONSE", "CONTENT"}:
                    current_section = candidate
                    continue

            # Detect bullet or numbered items: e.g. - 블랙 밀크티 : 4.5 / 5.6
            item_match = re.match(r"^(?:[-*•]|\d+[\.\)])\s*(.+)$", trimmed)
            if not item_match:
                continue

            content = item_match.group(1).strip()
            # Find price if present
            found_prices = price_pattern.findall(content)
            price_display = None
            if found_prices:
                price_display = found_prices[-1].strip()
                name_part = content[: content.rfind(price_display)].strip(" -:–|")
            else:
                name_part = content

            raw_cand = re.sub(r"^\*+|\*+$", "", name_part).strip(" -:–|")
            if DescriptionSanitizer.is_prompt_commentary_dish_name(raw_cand):
                continue

            clean_name, clean_desc, clean_price, is_header = sanitize_dish_item(raw_cand, None, price_display)
            if is_header:
                current_section = clean_name
                continue

            if DescriptionSanitizer.is_prompt_commentary_dish_name(clean_name):
                continue

            if not clean_name or len(clean_name) < 2:
                continue

            lower_name = clean_name.lower()
            if lower_name in {"str", "example", "sample", "dish name", "none", "null"}:
                continue

            is_valid_desc, validated_desc, _ = DescriptionSanitizer.validate_and_clean_description(
                clean_desc, dish_name=clean_name, section=current_section
            )
            clean_desc = validated_desc if is_valid_desc else None

            items.append(
                MenuTextBlock(
                    id=str(uuid.uuid4())[:8],
                    reading_order=len(items) + 1,
                    text_region_type="dish_item",
                    bounding_box=BoundingBox(xmin=0.0, ymin=0.0, xmax=1.0, ymax=1.0).to_pixel_box(orig_width, orig_height),
                    original_name=clean_name,
                    subtitle_or_description=clean_desc,
                    section=current_section,
                    price_display=clean_price,
                    currency="₩" if (clean_price and ("₩" in clean_price or "원" in clean_price)) else None,
                    is_confident=True,
                    needs_review=False,
                )
            )

        if not items:
            return None

        # Detect language
        detected_lang = None
        full_text = " ".join([it.original_name for it in items])
        if re.search(r"[\uac00-\ud7a3]", full_text):
            detected_lang = "ko"
        elif re.search(r"[\u3040-\u30ff]", full_text):
            detected_lang = "ja"
        elif re.search(r"[\u4e00-\u9fff]", full_text):
            detected_lang = "zh"
        elif re.search(r"[\u0600-\u06ff]", full_text):
            detected_lang = "ar"
        elif re.search(r"[\u0400-\u04ff]", full_text):
            detected_lang = "ru"

        return detected_lang, items, warnings

    @classmethod
    def parse_and_validate(
        cls,
        raw_output: str,
        orig_width: int,
        orig_height: int,
    ) -> Tuple[Optional[str], List[MenuTextBlock], List[ExtractionWarning]]:
        """
        Parse model output into validated MenuTextBlock items and extraction warnings.
        Distinguishes empty responses, syntax errors, and schema errors.
        Returns: (source_language, items, warnings)
        """
        if not raw_output or not raw_output.strip():
            raise ModelInferenceError(
                message="Model returned an empty response",
                details={"code": "EMPTY_RESPONSE"},
            )

        cleaned_json = cls.clean_raw_output(raw_output)
        if not cleaned_json or ("{" not in cleaned_json and "[" not in cleaned_json):
            unstructured_result = cls.parse_unstructured_text(raw_output, orig_width, orig_height)
            if unstructured_result is not None:
                return unstructured_result
            raise ModelInferenceError(
                message="Model output did not contain any JSON objects or arrays",
                details={"code": "NO_JSON_FOUND", "raw_snippet": raw_output[:200]},
            )

        warnings: List[ExtractionWarning] = []
        data: Optional[Any] = None

        try:
            data = json.loads(cleaned_json)
        except json.JSONDecodeError as initial_err:
            logger.warning(f"Initial JSON parse failed: {initial_err}. Attempting recovery.")
            # 0. Check for valid JSON root with trailing extra data
            if "Extra data" in str(initial_err) and hasattr(initial_err, "pos") and initial_err.pos > 0:
                try:
                    data = json.loads(cleaned_json[: initial_err.pos].strip())
                    warnings.append(
                        ExtractionWarning(
                            code="JSON_EXTRA_DATA_TRIMMED",
                            message="Trimmed trailing content after valid JSON object",
                        )
                    )
                except Exception:
                    data = None

            if data is None:
                # 1. Attempt syntax repairs (unquoted keys, single quotes)
                try:
                    fixed = cls.fix_syntax_flaws(cleaned_json)
                    data = json.loads(fixed)
                    warnings.append(
                        ExtractionWarning(
                            code="JSON_SYNTAX_REPAIRED",
                            message="Recovered JSON by repairing formatting and string quotes",
                        )
                    )
                except Exception:
                    # 2. Attempt truncation recovery
                    recovered = cls.attempt_truncation_recovery(cleaned_json)
                    if recovered is not None:
                        data = recovered
                        warnings.append(
                            ExtractionWarning(
                                code="JSON_TRUNCATION_REPAIRED",
                                message="Recovered valid extraction items from truncated model response",
                            )
                        )
                    else:
                        unstructured_result = cls.parse_unstructured_text(raw_output, orig_width, orig_height)
                        if unstructured_result is not None:
                            return unstructured_result
                        raise ModelInferenceError(
                            message="Model returned malformed JSON that could not be parsed",
                            details={
                                "code": "JSON_SYNTAX_ERROR",
                                "error_snippet": str(initial_err),
                                "clean_length": len(cleaned_json),
                                "clean_snippet": cleaned_json[:200],
                                "clean_tail": cleaned_json[-200:],
                            },
                        )

        if not isinstance(data, (dict, list)):
            raise ModelInferenceError(
                message="Model output did not contain a valid JSON object or item list",
                details={"code": "SCHEMA_VALIDATION_ERROR"},
            )

        if isinstance(data, list):
            detected_lang = None
            raw_items = data
        else:
            detected_lang = data.get("source_language")
            if "items" in data and not isinstance(data["items"], list):
                raise ModelInferenceError(
                    message="Model response schema invalid: 'items' field must be a list",
                    details={"code": "SCHEMA_VALIDATION_ERROR"},
                )
            raw_items = data.get("items", [])

        if not isinstance(raw_items, list):
            raw_items = []

        items: List[MenuTextBlock] = []
        current_section: Optional[str] = None

        for idx, item in enumerate(raw_items):
            if not isinstance(item, dict):
                continue

            raw_name = str(item.get("original_name") or item.get("name") or "").strip()
            if not raw_name:
                warnings.append(
                    ExtractionWarning(
                        code="SKIPPED_EMPTY_NAME",
                        message=f"Item at index {idx} lacked dish name and was skipped",
                    )
                )
                continue

            raw_desc = item.get("subtitle_or_description") or item.get("description")
            raw_price = item.get("price_display") or item.get("price")
            price_str = str(raw_price).strip() if raw_price is not None else None

            # Update section context if provided explicitly
            if item.get("section") and str(item.get("section")).strip():
                sec_val = str(item.get("section")).strip()
                clean_sec = DescriptionSanitizer.clean_section_title(sec_val)
                if clean_sec:
                    current_section = clean_sec

            region_type = str(item.get("text_region_type") or "dish_item").strip().lower()
            if region_type not in ["dish_item", "heading", "description", "price", "other"]:
                region_type = "dish_item"

            # If marked explicitly as heading or commentary
            if region_type == "heading" or is_section_header(raw_name):
                clean_h = DescriptionSanitizer.clean_section_title(raw_name)
                current_section = clean_h or raw_name
                continue

            if DescriptionSanitizer.is_prompt_commentary_dish_name(raw_name):
                logger.info(f"Skipped model commentary masquerading as dish name: '{raw_name}'")
                continue

            # Defensive sanitization to strip model monologue, schema prefixes, and fused strings
            clean_name, clean_desc, clean_price, is_header = sanitize_dish_item(raw_name, raw_desc, price_str)
            if is_header:
                clean_h = DescriptionSanitizer.clean_section_title(clean_name)
                current_section = clean_h or clean_name
                continue

            # Ensure any price strings remaining in clean_desc are moved to clean_price
            if clean_desc and DescriptionSanitizer.is_price_like_string(clean_desc):
                clean_p = re.sub(r"^(?:price|가격|금액)\s*[:\s]*", "", clean_desc, flags=re.IGNORECASE).strip()
                if not clean_price and clean_p:
                    clean_price = clean_p
                clean_desc = None

            if DescriptionSanitizer.is_prompt_commentary_dish_name(clean_name):
                logger.info(f"Skipped model commentary after sanitization: '{clean_name}'")
                continue

            if not clean_name or len(clean_name) < 2:
                continue

            lower_name = clean_name.lower().strip()
            if lower_name in {
                "str",
                "example",
                "sample",
                "dish name",
                "dish_name",
                "item name",
                "null",
                "none",
                "dish name exactly as printed",
            }:
                continue

            # Validate and clean description to ensure source grounding
            is_valid_desc, validated_desc, desc_rejection_reason = DescriptionSanitizer.validate_and_clean_description(
                clean_desc, dish_name=clean_name, section=current_section
            )
            if not is_valid_desc:
                logger.info(f"Discarded invalid description '{clean_desc}' on dish '{clean_name}': {desc_rejection_reason}")
                clean_desc = None
            else:
                clean_desc = validated_desc

            # Extract box coordinates safely
            box = cls._parse_box(item, orig_width, orig_height, idx, warnings)

            reading_order = item.get("reading_order")
            if not isinstance(reading_order, int):
                reading_order = idx + 1

            currency = item.get("currency")
            if not currency and clean_price:
                for symbol in ["€", "$", "¥", "£", "₩", "CHF", "₺", "Rp", "฿", "₫", "₹", "AED", "SAR"]:
                    if symbol in clean_price:
                        currency = symbol
                        break
                if not currency and "원" in clean_price:
                    currency = "₩"

            menu_block = MenuTextBlock(
                id=str(uuid.uuid4())[:8],
                reading_order=reading_order,
                section=item.get("section") or current_section,
                original_name=clean_name,
                phonetic_transcription=item.get("phonetic_transcription"),
                subtitle_or_description=clean_desc,
                price_display=clean_price,
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

        # Auto-detect language if missing or unspecified
        if not detected_lang or str(detected_lang).lower() in ("null", "none", "unknown", ""):
            full_text = " ".join([itm.original_name for itm in items])
            if re.search(r"[\uac00-\ud7a3]", full_text):
                detected_lang = "ko"
            elif re.search(r"[\u3040-\u30ff]", full_text):
                detected_lang = "ja"
            elif re.search(r"[\u4e00-\u9fff]", full_text):
                detected_lang = "zh"
            elif re.search(r"[\u0600-\u06ff]", full_text):
                detected_lang = "ar"
            elif re.search(r"[\u0400-\u04ff]", full_text):
                detected_lang = "ru"

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

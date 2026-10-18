"""Description and Dish Name Sanitizer & Prompt Leakage Detector.

Enforces strict source-grounding:
1. Rejects model reasoning, internal monologue, and image analysis commentary.
2. Rejects prompt leakage, schema prefixes ('description:', 'price:').
3. Rejects category banners and section titles disguised as descriptions or dishes.
4. Preserves genuine multi-lingual culinary descriptions and ingredients.
"""

import re
from typing import Optional, Set, Tuple


# Metacognitive commentary & image analysis phrases across supported languages
PROMPT_LEAKAGE_PATTERNS = [
    # English commentary & instruction patterns
    re.compile(r"\b(?:let'?s\s+(?:check|look|see|extract|analyze|examine|go\s+through))\b", re.IGNORECASE),
    re.compile(r"\b(?:need\s+to\s+(?:extract|check|identify|look|find))\b", re.IGNORECASE),
    re.compile(r"\b(?:the\s+menu\s+has\s+(?:columns|sections|items|categories))\b", re.IGNORECASE),
    re.compile(r"\b(?:each\s+item\s+has\s+(?:a\s+)?(?:name|description|price))\b", re.IGNORECASE),
    re.compile(r"\b(?:items\s+like\s+.*,\s*(?:etc|with\s+prices))\b", re.IGNORECASE),
    re.compile(r"\b(?:looking\s+at\s+the\s+(?:image|menu|text|problem))\b", re.IGNORECASE),
    re.compile(r"\b(?:wait\s+no\b|wait[,\s—-]+looking|wait\s+looking)\b", re.IGNORECASE),
    re.compile(r"\b(?:user\s+provided\s+text|problem\s+statement)\b", re.IGNORECASE),
    re.compile(r"\b(?:the\s+task\s+is\s+to\s+(?:extract|translate))\b", re.IGNORECASE),
    re.compile(r"\b(?:first[,\s]+(?:I|we)\s+need\s+to)\b", re.IGNORECASE),
    re.compile(r"\b(?:this\s+section\s+has\s+items)\b", re.IGNORECASE),
    re.compile(r"\b(?:in\s+this\s+(?:image|photo|menu|section))\b", re.IGNORECASE),
    re.compile(r"\b(?:might\s+have\s+different\s+descriptions)\b", re.IGNORECASE),
    re.compile(r"\b(?:columns\s+for\s+different\s+sizes)\b", re.IGNORECASE),
    re.compile(r"\b(?:base\s+teas?\b.*check\s+the\s+prices)\b", re.IGNORECASE),
    re.compile(r"\b(?:probably\s+the\s+base\s+teas)\b", re.IGNORECASE),
    # Korean commentary patterns
    re.compile(r"(?:메뉴(?:를|의)?\s*확인|구조를\s*확인|컬럼이\s*있|추출해야|확인해보자|이미지(?:에서|를)|문제(?:에서|의))", re.IGNORECASE),
    # Japanese commentary patterns
    re.compile(r"(?:メニューを(?:確認|見ると)|画像を(?:確認|見ると)|列がある|抽出す(?:る|べき))", re.IGNORECASE),
    # Chinese commentary patterns
    re.compile(r"(?:提取菜单|查看菜单|分析图片|菜单有列|我们需要)", re.IGNORECASE),
    # European commentary patterns
    re.compile(r"\b(?:analysons\s+le\s+menu|vérifions\s+la\s+structure|il\s+faut\s+extraire)\b", re.IGNORECASE),
    re.compile(r"\b(?:revisemos\s+la\s+estructura|hay\s+que\s+extraer|en\s+la\s+imagen)\b", re.IGNORECASE),
    re.compile(r"\b(?:die\s+struktur\s+überprüfen|wir\s+müssen\s+extrahieren)\b", re.IGNORECASE),
]

# Schema prefixes and prompt field leakage
SCHEMA_PREFIX_PATTERN = re.compile(
    r"^(?:description|desc|subtitle|original_name|name|dish|item|price|price_display|reading_order|json)\s*:\s*",
    re.IGNORECASE,
)

# Known promotional headings and section titles
KNOWN_SECTION_HEADINGS: Set[str] = {
    "new", "new salty sweet", "season menu", "seasonal menu", "best seller",
    "best sellers", "signature", "signatures", "original tea", "milk tea",
    "smoothie", "coffee", "fruit tea more", "fruit tea", "sweet grade",
    "toppings", "ice grade", "beverages", "drinks", "appetizers", "mains",
    "desserts", "starters", "antipasti", "primi", "secondi", "dolci",
    "bevande", "pizze", "entrees", "entrées", "plats", "boissons",
    "vorspeisen", "hauptgerichte", "getranke", "getränke", "tapas",
    "raciones", "postres", "bebidas", "신메뉴", "시즌메뉴", "베스트셀러",
    "추천메뉴", "음료", "디저트", "식사류", "季節限定", "おすすめ", "ドリンク",
    "新品推荐", "招牌", "热销", "饮品", "المقبلات", "الأطباق الرئيسية", "المشروبات",
}

# Generic fabricated fallback filler phrases to strictly reject
FABRICATED_FILLER_PATTERNS = [
    re.compile(r"artisan\s+regional\s+culinary\s+preparation", re.IGNORECASE),
    re.compile(r"traditional\s+regional\s+culinary\s+preparation", re.IGNORECASE),
    re.compile(r"classic\s+korean\s+preparation\s+of", re.IGNORECASE),
    re.compile(r"prepared\s+with\s+quality\s+tea\s+leaves", re.IGNORECASE),
    re.compile(r"prepared\s+with\s+quality\s+ingredients", re.IGNORECASE),
    re.compile(r"balanced,\s*authentic\s+regional\s+flavors", re.IGNORECASE),
    re.compile(r"refreshing,\s*balanced\s+sweetness,\s*aromatic\s+notes", re.IGNORECASE),
]


# Known blogging platform and photo watermark artifacts that are not food items
WATERMARK_PATTERNS = [
    re.compile(r"^(?:티스토리|tistory(?:\.com)?|네이버|naver(?:\.com)?|다음|daum(?:\.net)?|블로그|blog(?:\.me)?|velog|brunch)$", re.IGNORECASE),
    re.compile(r"\b(?:tistory\.com|blog\.naver\.com|daum\.net|instagram\.com)\b", re.IGNORECASE),
]

# Patterns detecting price expressions or size-price annotations masquerading as descriptions
PRICE_EXPRESSION_PATTERNS = [
    re.compile(r"^\s*(?:price|가격|금액)?\s*[:\s]*[LMRSJ]?\s*\d+(?:[.,]\d+)?(?:\s*[\/|]\s*[LMRSJ]?\s*\d+(?:[.,]\d+)?)*(?:\s*[LMRSJ])?\s*(?:원|₩|\$|€|£|¥|CHF)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*[LMRSJ]\s*\d+(?:[.,]\d+)?\s*(?:[\/|]\s*[LMRSJ])?\s*$", re.IGNORECASE),
    re.compile(r"^\s*price\s+[LMRSJ]?\s*\d+", re.IGNORECASE),
]


class DescriptionSanitizer:
    """Rigorous validator enforcing authentic, source-grounded menu text."""

    @classmethod
    def is_watermark_or_artifact(cls, text: str) -> bool:
        """Check if a text string is a blog watermark, platform stamp, or camera artifact."""
        if not text or not text.strip():
            return False
        clean = text.strip()
        for pat in WATERMARK_PATTERNS:
            if pat.search(clean):
                return True
        return False

    @classmethod
    def is_price_like_string(cls, text: Optional[str]) -> bool:
        """Check if a string represents price or size-price notation rather than a culinary description."""
        if not text or not text.strip():
            return False
        clean = text.strip()
        # Direct pattern match
        for pat in PRICE_EXPRESSION_PATTERNS:
            if pat.match(clean):
                return True
        # Check if stripped of punctuation it's just size letters and digits
        norm = re.sub(r"[₩$€£¥/|\-:,.\s]", "", clean).upper()
        if norm and re.match(r"^(?:PRICE)?[LMRSJ\d]+$", norm):
            return True
        return False

    @classmethod
    def clean_section_title(cls, section: Optional[str]) -> Optional[str]:
        """Strip prompt instructions like '(not to be included as an item)' from section headings."""
        if not section or not section.strip():
            return None
        clean = section.strip()
        clean = re.sub(r"\s*\(\s*not\s+to\s+be\s+included[^\)]*\)", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*section\s*\(\s*not\s+to\s+be\s+included[^\)]*\)", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*\(not\s+an\s+item\)", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s+section$", "", clean, flags=re.IGNORECASE)
        clean = clean.strip(" -–—:|,\t\n")
        return clean if clean else None

    @classmethod
    def is_prompt_commentary_dish_name(cls, name: str) -> bool:
        """
        Check if an extracted 'dish name' is actually model thinking, prompt leakage,
        watermark, or an image analysis instruction rather than an authentic dish item.
        """
        if not name or not name.strip():
            return True

        clean = name.strip()

        # 0. Check for watermarks (e.g. 티스토리 / Tistory blog watermark)
        if cls.is_watermark_or_artifact(clean):
            return True

        # 1. Check against metacognitive prompt leakage patterns
        for pattern in PROMPT_LEAKAGE_PATTERNS:
            if pattern.search(clean):
                return True

        # 2. Check if text contains conversational questioning/reasoning
        if re.search(r"\?\s*(?:wait|no|user|looking)\b", clean, re.IGNORECASE):
            return True

        # 3. Check if name is purely a section header without price
        norm = re.sub(r"[#*_:\-\[\]\(\)&/]", " ", clean).strip().lower()
        norm = re.sub(r"\s+", " ", norm)
        if norm in KNOWN_SECTION_HEADINGS:
            return True

        # 4. Check if string is excessively long with multiple clauses (monologue sentences)
        if len(clean) > 80 and any(w in clean.lower() for w in ["menu", "extract", "section", "columns", "items"]):
            return True

        # 5. Check if string is purely price
        if cls.is_price_like_string(clean):
            return True

        return False

    @classmethod
    def validate_and_clean_description(
        cls,
        raw_description: Optional[str],
        dish_name: str = "",
        section: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates and sanitizes a dish description.
        Returns: (is_valid, cleaned_description_or_none, rejection_reason_or_none)

        Enforces:
        - Rejection of prompt commentary and image analysis text.
        - Rejection of section headings posing as descriptions.
        - Rejection of generic fabricated filler sentences.
        - Stripping of accidental schema prefixes ('Description:', 'Printed desc:').
        - Preservation of authentic ingredient lists and culinary notes.
        """
        if not raw_description or not raw_description.strip():
            return True, None, None

        text = raw_description.strip()

        # 1. Strip schema labels (e.g. 'Description:', 'desc:', 'subtitle:')
        text = SCHEMA_PREFIX_PATTERN.sub("", text).strip(" -–—:|(),")

        # 2. Reject fabricated filler phrases
        for pattern in FABRICATED_FILLER_PATTERNS:
            if pattern.search(text):
                return False, None, "FABRICATED_FILLER_DETECTED"

        # 3. Check for prompt leakage or model thinking
        for pattern in PROMPT_LEAKAGE_PATTERNS:
            if pattern.search(text):
                return False, None, "PROMPT_LEAKAGE_DETECTED"

        # 4. Reject conversational question/correction fragments
        if re.search(r"\?\s*(?:wait|no|user|looking|the image)\b", text, re.IGNORECASE):
            return False, None, "CONVERSATIONAL_FRAGMENT_DETECTED"

        # 5. Reject if description is identical or near-identical to dish name or section
        norm_desc = re.sub(r"[#*_:\-\[\]\(\)&/]", " ", text).strip().lower()
        norm_desc = re.sub(r"\s+", " ", norm_desc)

        if dish_name:
            norm_name = re.sub(r"[#*_:\-\[\]\(\)&/]", " ", dish_name).strip().lower()
            norm_name = re.sub(r"\s+", " ", norm_name)
            if norm_desc == norm_name:
                return False, None, "DESCRIPTION_DUPLICATES_DISH_NAME"

        if section:
            norm_sec = re.sub(r"[#*_:\-\[\]\(\)&/]", " ", section).strip().lower()
            norm_sec = re.sub(r"\s+", " ", norm_sec)
            if norm_desc == norm_sec:
                return False, None, "DESCRIPTION_DUPLICATES_SECTION_TITLE"

        if norm_desc in KNOWN_SECTION_HEADINGS:
            return False, None, "SECTION_HEADING_USED_AS_DESCRIPTION"

        # 6. Reject if description is just a single number, price, or empty
        if len(text) < 2 or re.match(r"^[₩$€£¥\d\s.,/-]+$", text):
            return False, None, "INVALID_NUMERIC_DESCRIPTION"

        # 7. Strictly reject if description is price or size-price expression (e.g. 'price L6.1 J', 'L 6.1 / J', 'L 5.8')
        if cls.is_price_like_string(text):
            return False, None, "PRICE_DATA_IN_DESCRIPTION"

        # 8. Strictly reject watermarks or blog stamps
        if cls.is_watermark_or_artifact(text):
            return False, None, "WATERMARK_IN_DESCRIPTION"

        return True, text, None

    @classmethod
    def extract_tags(cls, name: str, section: Optional[str] = None) -> List[str]:
        """Extract promotional labels (Best Seller, New, Signature, Seasonal) from name or section context."""
        tags: List[str] = []
        combined = f"{name} {section or ''}".lower()
        if any(w in combined for w in ["best seller", "베스트", "best sellers", "bestseller", "top seller", "popular"]):
            tags.append("Best Seller")
        if any(w in combined for w in ["new", "신메뉴", "신제품", "nuevo", "nouveau", "neu", "season menu with"]):
            if "Best Seller" not in tags:
                tags.append("New")
        if any(w in combined for w in ["signature", "시그니처", "chef special", "specialty"]):
            if "Signature" not in tags:
                tags.append("Signature")
        if any(w in combined for w in ["season menu", "seasonal", "시즌메뉴", "가을", "autumn", "limited edition", "limited"]):
            if "Seasonal" not in tags:
                tags.append("Seasonal")
        return tags


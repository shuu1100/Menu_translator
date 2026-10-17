"""Intelligent Dish-to-Image Query Builder and Category Matcher.

Extracts semantic culinary features, cleans noisy OCR text and URL encodings,
predicts cuisine and dish category across multilingual scripts, enforces strict
incompatible category rejection (e.g. sushi for milk tea/desserts), and constructs
targeted search queries for image providers.
"""

import html
import re
import urllib.parse
from typing import Dict, List, Optional, Set, Tuple

# Common noise words to strip from dish names before image querying
NOISE_PATTERNS = [
    r"\b(new|special|signature|chef'?s? special|best seller|popular|hot|recommended|must try)\b",
    r"\b(set|combo|menu|course|platter|plate|size|regular|large|small|half|full)\b",
    r"\b(homemade|house-made|authentic|traditional|fresh|daily)\b",
    r"\b(\d+[\s\-]?(pcs?|pieces?|g|ml|oz|cl|won|원|krw))\b",
    r"[\(\[\{][^\)\]\}]*[\)\]\}]",  # Remove parenthetical info like "(6 pcs)" or "(spicy)"
    r"[\*\#\$\€\£\¥\₩\d+\.\,\-\/\:]+", # Remove standalone numbers, prices, bullet points
    r"\b(price\s+[a-z0-9\.\s/]+)\b", # OCR price noise like 'price L6.1 J'
    r"\b(section|item|table|page)\b",
]

# Korean culinary term to English search term bridge for image providers
KOREAN_FOOD_TERM_MAP: Dict[str, str] = {
    "소프트": "soft serve ice cream",
    "아이스크림": "ice cream",
    "밀크티": "milk tea",
    "버블티": "bubble tea",
    "보바": "boba tea",
    "브라운슈가": "brown sugar",
    "브라운": "brown sugar",
    "흑당": "brown sugar boba",
    "블랙티": "black tea",
    "우롱티": "oolong tea",
    "우롱": "oolong tea",
    "얼그레이": "earl grey tea",
    "녹차": "green tea",
    "말차": "matcha",
    "홍차": "black tea",
    "타로": "taro milk tea",
    "에이드": "fruit ade soda",
    "스무디": "smoothie",
    "라떼": "latte",
    "커피": "coffee",
    "디저트": "dessert",
    "와플": "waffle",
    "크로플": "croffle",
    "빙수": "bingsu shaved ice",
    "케이크": "cake",
    "파르페": "parfait",
    "초밥": "sushi",
    "스시": "sushi",
    "사시미": "sashimi",
    "회": "raw fish sashimi",
    "삼겹살": "pork belly samgyeopsal",
    "차돌박이": "beef brisket chadolbaki",
    "불고기": "bulgogi marinated beef",
    "갈비": "galbi beef short ribs",
    "치킨": "korean fried chicken",
    "닭갈비": "dakgalbi spicy chicken",
    "떡볶이": "tteokbokki spicy rice cakes",
    "김밥": "kimbap rice roll",
    "비빔밥": "bibimbap",
    "찌개": "korean stew jjigae",
    "라멘": "ramen",
    "우동": "udon",
    "국수": "noodles",
}

# Cuisine keyword mappings
CUISINE_MAP: Dict[str, List[str]] = {
    "japanese": [
        "ramen", "tonkotsu", "miso", "shoyu", "tsukemen", "sushi", "sashimi", "nigiri",
        "maki", "tempura", "udon", "soba", "yakitori", "donburi", "gyoza", "edamame",
        "matcha", "karaage", "teriyaki", "katsu", "takoyaki", "onigiri", "okonomiyaki"
    ],
    "korean": [
        "kimchi", "bulgogi", "bibimbap", "tteokbokki", "croffle", "samgyeopsal", "kimbap",
        "bingsu", "soju", "japchae", "mandù", "mandoo", "galbi", "jjigae", "chimaek",
        "milk tea", "boba", "bubble tea", "cheese foam", "dakgalbi", "chadolbaki"
    ],
    "italian": [
        "pasta", "pizza", "spaghetti", "carbonara", "bolognese", "lasagna", "risotto",
        "bruschetta", "carpaccio", "tiramisu", "gnocchi", "cacio e pepe", "ravioli",
        "tagliatelle", "focaccia", "gelato", "panna cotta", "mozzarella", "burrata", "margherita"
    ],
    "indian": [
        "curry", "tikka", "masala", "biryani", "naan", "tandoori", "paneer", "dal",
        "samosa", "makhani", "korma", "roti", "paratha", "gulab jamun", "chaat",
        "butter chicken", "chana", "dosa", "lassi"
    ],
    "thai": [
        "pad thai", "tom yum", "green curry", "red curry", "som tum", "massaman",
        "pad see ew", "mango sticky rice", "satay", "thai iced tea", "khao soi"
    ],
    "mexican": [
        "taco", "tacos", "burrito", "quesadilla", "enchilada", "guacamole", "salsa",
        "fajita", "nachos", "churros", "carnitas", "al pastor", "birria"
    ],
    "chinese": [
        "dim sum", "dumpling", "bao", "wonton", "peking duck", "kung pao", "mapo tofu",
        "chow mein", "lo mein", "spring roll", "fried rice", "char siu", "hot pot"
    ],
}

# Category classification keywords (multilingual)
CATEGORY_MAP: Dict[str, List[str]] = {
    "beverage": [
        "tea", "coffee", "latte", "drink", "smoothie", "juice", "shake", "milk tea",
        "cocktail", "lemonade", "soda", "bubble tea", "boba", "oolong", "matcha",
        "earl grey", "black tea", "green tea", "espresso", "cappuccino", "macchiato",
        "밀크티", "버블티", "보바", "티", "차", "커피", "라떼", "에이드", "스무디", "음료",
        "우롱티", "블랙티", "얼그레이", "녹차", "홍차"
    ],
    "dessert": [
        "dessert", "cake", "ice cream", "soft serve", "soft", "gelato", "parfait",
        "croffle", "souffle", "tiramisu", "pudding", "waffle", "sweet", "pastry",
        "cookie", "bingsu", "brownie", "tart", "pie",
        "소프트", "아이스크림", "빙수", "디저트", "케이크", "와플", "크로플", "파르페",
        "푸딩", "쿠키", "타르트", "마카롱"
    ],
    "sushi_seafood": [
        "sushi", "sashimi", "nigiri", "maki", "roll", "raw fish", "salmon", "tuna",
        "seafood", "fish", "shrimp", "crab", "lobster",
        "초밥", "스시", "사시미", "회", "연어", "참치", "생선"
    ],
    "soup": [
        "soup", "broth", "ramen", "udon", "tom yum", "pho", "stew", "chowder",
        "jjigae", "bisque", "tang", "guk",
        "찌개", "탕", "국", "라멘", "우동", "스프", "수프"
    ],
    "noodles": [
        "noodle", "noodles", "pasta", "spaghetti", "tagliatelle", "pad thai",
        "tsukemen", "soba", "chow mein", "carbonara", "ramen",
        "면", "국수", "파스타", "스파게티", "소바", "짜장면", "짬뽕"
    ],
    "meat_bbq": [
        "yakitori", "bbq", "barbecue", "grilled", "steak", "kebab", "samgyeopsal",
        "tandoori", "bulgogi", "galbi", "pork", "beef", "chicken", "ribs",
        "삼겹살", "갈비", "불고기", "차돌박이", "치킨", "고기", "구이", "스테이크"
    ],
    "rice": [
        "rice", "biryani", "fried rice", "risotto", "donburi", "bibimbap", "kimbap",
        "밥", "비빔밥", "김밥", "볶음밥", "덮밥"
    ],
    "curry": ["curry", "masala", "makhani", "tikka", "korma", "dal", "카레", "커리"],
    "appetizer": ["appetizer", "salad", "bruschetta", "gyoza", "dumpling", "samosa", "tapas", "샐러드", "만두", "교자"],
    "pizza_bread": ["pizza", "naan", "bread", "focaccia", "roti", "croissant", "taco", "피자", "빵", "난"],
}

# Strict Incompatible Category Blacklists to prevent cross-category mismatch
# (e.g. sushi showing up for milk tea or dessert)
INCOMPATIBLE_WITH_BEVERAGE = {
    "sushi", "sashimi", "maki", "nigiri", "raw fish", "fish", "salmon", "tuna",
    "seafood", "shrimp", "crab", "meat", "beef", "pork", "chicken", "steak",
    "burger", "pizza", "soup", "stew", "ramen", "noodle", "noodles", "pasta",
    "spaghetti", "curry", "rice bowl", "dim sum", "dumpling", "taco", "sandwich",
    "potstickers", "gyoza", "kebab"
}

INCOMPATIBLE_WITH_DESSERT = {
    "sushi", "sashimi", "maki", "nigiri", "raw fish", "fish", "salmon", "tuna",
    "seafood", "shrimp", "crab", "meat", "beef", "pork", "chicken", "steak",
    "burger", "pizza", "soup", "stew", "ramen", "curry", "taco", "salad",
    "pasta", "spaghetti", "dim sum", "dumpling", "sandwich"
}

INCOMPATIBLE_WITH_SAVORY = {
    "smoothie", "milkshake", "cocktail", "milk tea", "boba", "bubble tea",
    "cake", "ice cream", "cookie", "cupcake", "pudding", "parfait", "dessert"
}


def clean_dish_name(name: str) -> str:
    """Strip URL encoding, noise words, prices, parentheticals, and OCR artifacts."""
    if not name:
        return ""
    # 1. Unquote any URL encodings (e.g. %20, %EB...)
    try:
        cleaned = urllib.parse.unquote(str(name))
    except Exception:
        cleaned = str(name)

    cleaned = cleaned.lower()
    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    # Remove OCR symbol noise
    cleaned = re.sub(r"[#*_:\-\[\]\(\)&/]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def infer_cuisine(dish_name: str, native_name: Optional[str] = None, hint: Optional[str] = None) -> str:
    """Infer the cuisine or regional origin from dish text and script."""
    if hint and hint.lower() not in ("universal", "international", "general", "unknown", "none"):
        return hint.title()

    combined = f"{dish_name or ''} {native_name or ''}".lower()

    if re.search(r"[\u3040-\u309F\u30A0-\u30FF]", combined):
        return "Japanese"
    if re.search(r"[\uAC00-\uD7AF]", combined):
        return "Korean"
    if re.search(r"[\u0900-\u097F]", combined):
        return "Indian"
    if re.search(r"[\u4E00-\u9FFF]", combined):
        if any(w in combined for w in CUISINE_MAP.get("japanese", [])):
            return "Japanese"
        return "Chinese"
    if re.search(r"[\u0E00-\u0E7F]", combined):
        return "Thai"

    for cuisine, keywords in CUISINE_MAP.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", combined):
                return cuisine.title()

    return ""


def infer_dish_category(dish_name: str, section: Optional[str] = None, ingredients: Optional[List[str]] = None) -> str:
    """Categorize dish type across Korean, Japanese, and English culinary markers."""
    text = f"{dish_name or ''} {section or ''} {' '.join(ingredients or [])}".lower()
    for cat, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in text:
                return cat
    return "main_dish"


def build_image_search_query(
    dish_name: str,
    native_name: Optional[str] = None,
    transliteration: Optional[str] = None,
    cuisine: Optional[str] = None,
    section: Optional[str] = None,
    ingredients: Optional[List[str]] = None,
) -> Tuple[str, str, str]:
    """Generate high-precision primary and fallback image search queries.

    Avoids sending raw Hangul mixed with English into external photo search
    engines (which causes Unsplash to return sushi for any 'Korean' query).

    Returns:
        Tuple of (primary_query, fallback_query, inferred_category)
    """
    clean_dish = clean_dish_name(dish_name)
    clean_native = clean_dish_name(native_name or "")
    clean_trans = clean_dish_name(transliteration or "")

    detected_cuisine = infer_cuisine(clean_dish, native_name, hint=cuisine)
    category = infer_dish_category(f"{clean_dish} {clean_native}", section, ingredients)

    # 1. Translate Korean culinary keywords if present
    translated_tokens: List[str] = []
    combined_source = f"{clean_native} {clean_dish}"
    for k_term, eng_term in KOREAN_FOOD_TERM_MAP.items():
        if k_term in combined_source:
            if eng_term not in translated_tokens:
                translated_tokens.append(eng_term)

    # 2. Extract English / Latin tokens from dish_name or transliteration
    latin_tokens = [w for w in re.findall(r"[a-zA-Z]{3,}", f"{clean_dish} {clean_trans}") if w.lower() not in {"the", "and", "with", "for", "signature", "special"}]

    query_parts: List[str] = []
    if detected_cuisine and detected_cuisine.lower() not in " ".join(translated_tokens + latin_tokens).lower():
        query_parts.append(detected_cuisine)

    if translated_tokens:
        query_parts.extend(translated_tokens[:2])
    elif latin_tokens:
        query_parts.extend(latin_tokens[:3])
    else:
        # Ambiguous native text with no known culinary noun:
        # Do NOT construct a vague query like "Korean food" which yields random sushi!
        # Return empty primary query to force safe neutral placeholder.
        return "", clean_dish or clean_native, category

    # Category suffix for disambiguation
    if category == "beverage" and not any(w in " ".join(query_parts).lower() for w in ["tea", "drink", "coffee", "boba", "smoothie"]):
        query_parts.append("drink")
    elif category == "dessert" and not any(w in " ".join(query_parts).lower() for w in ["dessert", "ice cream", "cake", "sweet"]):
        query_parts.append("dessert")

    primary_query = " ".join(query_parts).strip()
    fallback_query = " ".join(translated_tokens or latin_tokens).strip()

    return primary_query, fallback_query, category


GENERIC_STOPWORDS = {
    "dish", "dishes", "food", "foods", "plate", "plates", "bowl", "bowls",
    "item", "items", "meal", "meals", "fresh", "hot", "cold", "special",
    "traditional", "authentic", "style", "recipe", "order", "portion",
    "with", "and", "the", "for", "delicious", "tasty", "signature", "homemade",
    "korean", "asian", "japanese", "chinese"
}


def calculate_match_relevance(
    query_dish_name: str,
    query_category: str,
    candidate_title: str,
    candidate_tags: Optional[List[str]] = None,
) -> float:
    """Calculate confidence score (0.0 to 1.0) of a candidate image match.

    Enforces hard rejection for cross-category mismatches (e.g. sushi for beverages/desserts).
    """
    title_lower = (candidate_title or "").lower()
    tags_lower = [t.lower() for t in (candidate_tags or [])]
    cand_text = f"{title_lower} {' '.join(tags_lower)}"

    # 1. HARD REJECTION: Incompatible category items
    if query_category == "beverage":
        if any(w in cand_text for w in INCOMPATIBLE_WITH_BEVERAGE):
            return 0.0
    elif query_category == "dessert":
        if any(w in cand_text for w in INCOMPATIBLE_WITH_DESSERT):
            return 0.0
    elif query_category in ("soup", "noodles", "meat_bbq"):
        if any(w in cand_text for w in INCOMPATIBLE_WITH_SAVORY):
            return 0.0

    # 2. Extract meaningful query tokens
    dish_clean = clean_dish_name(query_dish_name)
    meaningful_tokens = [
        w for w in re.findall(r"[a-zA-Z]{3,}", dish_clean)
        if w not in GENERIC_STOPWORDS
    ]

    # Also check if query had known Korean food terms
    for k_term, eng_term in KOREAN_FOOD_TERM_MAP.items():
        if k_term in query_dish_name:
            meaningful_tokens.extend(eng_term.split())

    if not meaningful_tokens:
        # If all tokens were stopwords or ambiguous:
        return 0.0

    # 3. Check for specific token overlap in candidate metadata
    matched_tokens = 0
    for tok in set(meaningful_tokens):
        if tok in title_lower or any(tok in tag for tag in tags_lower):
            matched_tokens += 1

    if matched_tokens == 0:
        return 0.0

    ratio = matched_tokens / len(set(meaningful_tokens))

    # Score scaling
    if ratio >= 0.70:
        score = 0.75 + (ratio * 0.25)
    elif ratio >= 0.40:
        score = 0.55 + (ratio * 0.25)
    else:
        score = 0.30 + (ratio * 0.20)

    # Positive category reinforcement
    if query_category == "beverage" and any(w in cand_text for w in ["drink", "beverage", "tea", "coffee", "boba", "smoothie"]):
        score += 0.10
    elif query_category == "dessert" and any(w in cand_text for w in ["dessert", "sweet", "cake", "ice cream", "pastry"]):
        score += 0.10

    return max(0.0, min(1.0, round(score, 2)))

import re
from typing import Optional, Tuple, Dict, Any

NORMALIZED_SECTION_HEADERS = {
    "new salty sweet",
    "new",
    "season menu",
    "seasonal menu",
    "best seller",
    "best sellers",
    "signature",
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
    "antipasti",
    "primi",
    "secondi",
    "dolci",
    "bevande",
    "entrees",
    "entrées",
    "plats",
    "boissons",
    "vorspeisen",
    "hauptgerichte",
    "getranke",
    "getränke",
    "tapas",
    "raciones",
    "postres",
    "bebidas",
}

def is_section_header(name: str) -> bool:
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
    raw_price: Optional[str] = None
) -> Tuple[str, Optional[str], Optional[str], bool]:
    """
    Returns (cleaned_name, cleaned_desc, cleaned_price, is_header)
    """
    if not raw_name or not raw_name.strip():
        return "", None, None, False

    text = raw_name.strip()

    # 1. Check if it's a section header
    if is_section_header(text) and not raw_price:
        return text, None, None, True

    # 2. Strip model reasoning/commentary in parentheses or brackets
    text = re.sub(r"\((?:but\s+)?wait[^\)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[(?:but\s+)?wait[^\]]*\]", "", text, flags=re.IGNORECASE)

    # 3. Strip trailing commentary
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

    # 5. Check if model fused dish + description + price into name
    # e.g.: "Tea 스 브라운 - description: 시그니처 Milk Tea + 케러멜 - price L6.1 J"
    fused_match = re.search(
        r"^(.*?)\s*[-–—|]\s*(?:description|printed_desc|desc)\s*:\s*(.*?)(?:\s*[-–—|]\s*(?:price|price_display)\s*:\s*(.*))?$",
        text,
        re.IGNORECASE
    )
    if fused_match:
        text = fused_match.group(1).strip()
        extracted_desc = fused_match.group(2).strip()
        extracted_price = fused_match.group(3).strip() if fused_match.group(3) else None
        if not desc and extracted_desc:
            desc = extracted_desc
        if not price and extracted_price:
            price = extracted_price

    # Check if price was appended like: "Tea 스 브라운 - 시그니처 Milk Tea + 케러멜 (L6.1 J"
    price_tag_match = re.search(r"[\(]?\s*([LMRSJ]\s*\d+(?:\.\d+)?|\d+(?:,\d+)?\s*(?:원|₩|\$|€|£|¥))\s*[\)]?$", text, re.IGNORECASE)
    if price_tag_match and not price:
        price = price_tag_match.group(1).strip()
        text = text[: price_tag_match.start()].strip(" -–—|()")

    # Check if a description was appended after a dash: "Tea 스 브라운 - 시그니처 Milk Tea + 케러멜"
    if " - " in text or " – " in text:
        parts = re.split(r"\s*[-–]\s*", text, maxsplit=1)
        if len(parts) == 2 and not desc:
            # If second part looks like ingredients or description
            text = parts[0].strip()
            desc = parts[1].strip()

    # Clean up leftover punctuation
    text = text.strip(" -–—:|(),")
    if desc:
        desc = desc.strip(" -–—:|(),")
    if price:
        price = price.strip(" -–—:|(),")

    # Double check if cleaned text is now a section header
    if is_section_header(text) and not price:
        return text, None, None, True

    return text, desc, price, False


test_cases = [
    "NEW (SALTY& SWEET)",
    "SEASON MENU",
    "Tea 스 브라운 - description: 시그니처 Milk Tea + 케러멜 (but wait the image might have different descriptions). Wait looking at the menu image",
    "Tea 스 브라운 - 시그니처 Milk Tea + 케러멜 (L6.1 J",
    "Name: Tea 스 브라운",
    "Description: 시그니처 Milk Tea + 케러멜",
    "블랙 밀크티",
    "Carpaccio di Manzo",
    "Pizza Margherita - Fresh mozzarella, basil, tomato sauce - €14.50"
]

import sys

out_str = "--- SANITIZATION TEST ---\n"
for t in test_cases:
    name, desc, price, is_header = sanitize_dish_item(t)
    out_str += f"INPUT:  '{t}'\nOUTPUT: name='{name}', desc='{desc}', price='{price}', is_header={is_header}\n\n"

sys.stdout.buffer.write(out_str.encode("utf-8"))

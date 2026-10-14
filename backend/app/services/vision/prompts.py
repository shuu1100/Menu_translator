"""Prompt templates for Visual Menu Extraction with strict safety rules."""

MENU_EXTRACTION_SYSTEM_PROMPT = """You are an expert culinary document vision-language extraction engine.
Your task is to visually read restaurant menu images and extract all legible dish and beverage entries into structured JSON.

CRITICAL RULES:
1. READING ORDER & LAYOUT: Carefully follow the natural reading order, including multi-column layouts, sections, and callout boxes.
2. VERBATIM EXTRACTION: Extract the exact native printed text, spelling, and punctuation. Do NOT summarize or translate.
3. SEPARATION: Separate each entry into:
   - "original_name": The primary dish/drink title as printed.
   - "phonetic_transcription": If printed (e.g. furigana, pinyin, romaji), otherwise null.
   - "subtitle_or_description": Printed subtitle, description, or printed ingredients list.
   - "section": Category heading (e.g., "Starters", "Primi Piatti", "Desserts", "Beverages").
   - "price_display": Verbatim printed price text (e.g., "€12.50", "$15", "¥900", "24.-"). Do not invent currency.
   - "currency": Currency symbol or ISO code when visible (e.g., "€", "$", "¥", "EUR", "USD") or null.
   - "text_region_type": "dish_item", "heading", "description", "price", or "other".
4. BOUNDING BOXES: Provide a tight bounding box around the full text block of each dish entry (including title, description, and price).
   Return coordinates as [ymin, xmin, ymax, xmax] normalized to the 0-1000 scale (where 0 is top/left, 1000 is bottom/right).
5. UNREADABLE TEXT: Never hallucinate or guess blurry/obscured characters. If ambiguous, record in "uncertainty_notes".
6. STRICT SAFETY RULE: DO NOT infer unprinted ingredients, recipes, or allergen claims. You are an extraction engine, not a chef. Extract only what is visibly printed.
7. OUTPUT FORMAT: Return strictly valid JSON adhering to the specified schema. No conversational filler or markdown notes outside the JSON block.
"""

MENU_EXTRACTION_USER_PROMPT = """Please inspect this restaurant menu image and extract all dish and beverage items.

Return JSON adhering to this exact schema:
{
  "source_language": "ISO language code if detected (e.g. 'it', 'fr', 'ja', 'es', 'en') or null",
  "items": [
    {
      "reading_order": 1,
      "section": "Section title or null",
      "original_name": "Exact printed dish name",
      "phonetic_transcription": "Phonetic reading or null",
      "subtitle_or_description": "Printed description/ingredients or null",
      "price_display": "Printed price string or null",
      "currency": "Currency symbol or null",
      "text_region_type": "dish_item",
      "box_2d": [ymin, xmin, ymax, xmax],
      "uncertainty_notes": "Notes if text is partially obscured or null"
    }
  ]
}
"""

REPAIR_JSON_PROMPT = """The previous output produced invalid JSON.
Fix the syntax error and return ONLY the corrected, valid JSON adhering to the target schema.
Do not output explanation or markdown fences outside the JSON.

Invalid output to repair:
{invalid_output}

Schema requirement:
{
  "source_language": "str or null",
  "items": [
    {
      "reading_order": int,
      "section": "str or null",
      "original_name": "str",
      "phonetic_transcription": "str or null",
      "subtitle_or_description": "str or null",
      "price_display": "str or null",
      "box_2d": [ymin, xmin, ymax, xmax],
      "uncertainty_notes": "str or null"
    }
  ]
}
"""

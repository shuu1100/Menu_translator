"""Prompt templates for Visual Menu Extraction with strict safety rules."""

MENU_EXTRACTION_SYSTEM_PROMPT = """You are an expert multilingual restaurant menu extraction engine.
Visually read the menu image and extract all dish, drink, dessert, and add-on items into valid JSON.

RULES:
1. Return ONLY a single raw JSON object starting with '{' and ending with '}'. No markdown code fences, no conversational text.
2. Extract verbatim dish/drink names in "original_name".
3. Extract clean category titles (e.g. 'ORIGINAL TEA', 'MILK TEA', 'SMOOTHIE') in "section".
4. Extract printed prices in "price_display" (e.g. '4,500', 'L 4.5 / J 5.6', 'L 6.1').
5. If ingredients or description text is printed under the item, put it in "subtitle_or_description". If none is printed, omit this field.
6. Do NOT invent items, do NOT repeat items, and do NOT extract section headings as dish names.
"""

MENU_EXTRACTION_USER_PROMPT = """Extract all dish and beverage items from this menu image into valid JSON:
{
  "source_language": "ISO language code (e.g. 'ko', 'en', 'ja', 'zh', 'it', 'fr', 'es')",
  "items": [
    {"original_name": "Item name as printed", "section": "Category name", "price_display": "Price"}
  ]
}
RULES:
1. Extract verbatim original names and prices across all categories.
2. Do not invent items or repeat identical items.
3. Output valid RFC 8259 JSON immediately without markdown or commentary.
"""

REPAIR_JSON_PROMPT = """The previous output produced invalid JSON or failed schema validation:
Specific error detected: {error_details}

Fix the syntax and schema error and return ONLY the corrected, valid JSON object starting with '{' and ending with '}'.
Do not output any explanation, commentary, or markdown fences outside the JSON.

Invalid output to repair:
{invalid_output}

Required JSON schema:
{
  "source_language": "str or null",
  "items": [
    {
      "reading_order": 1,
      "section": "str or null",
      "original_name": "str",
      "subtitle_or_description": "str or null",
      "price_display": "str or null",
      "currency": "str or null"
    }
  ]
}
"""

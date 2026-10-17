import json
import sys
sys.path.insert(0, ".")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.services.vision.json_parser import ModelJsonParser

sample_with_extra = """{
  "source_language": "ko",
  "items": [
    {"reading_order": 1, "section": "ORIGINAL TEA", "original_name": "블랙 밀크티", "price_display": "4.5 / 5.6"}
  ]
}
Additional text from model after closing brace
"""

cleaned = ModelJsonParser.clean_raw_output(sample_with_extra)
try:
    data = json.loads(cleaned)
    print("Direct success!")
except json.JSONDecodeError as e:
    print("Error:", e)
    if "Extra data" in str(e):
        valid = json.loads(cleaned[:e.pos])
        print("Recovered with extra data slice! Items:", len(valid["items"]))

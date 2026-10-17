import sys
sys.path.insert(0, ".")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
from backend.app.services.vision.json_parser import ModelJsonParser

with open("scratch/last_thinking.txt", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

# Let's check if there is an existing json file or let's run test_prompt_without_boxes with utf-8 encoding

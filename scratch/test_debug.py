import json
from backend.app.services.vision.json_parser import ModelJsonParser

with open("scratch/batch_result.txt", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

print("File len:", len(text))
print("Sample:", text[:300])

import sys
sys.path.insert(0, '.')
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
from backend.app.services.translation.multilingual_engine import MultilingualCulinaryEngine
from backend.app.schemas.menu_analysis import SupportedLanguage

test_items = [
    "가을 향기 라떼",
    "아이스 브랜드",
    "스윗 그레이드",
    "토핑 메뉴",
    "시즌 메뉴",
    "사탕가루 스윗",
    "블랙 밀크티",
    "Pizza Margherita"
]

for name in test_items:
    trans_title, phonetic, desc, flavor = MultilingualCulinaryEngine.translate_dish(name, None, SupportedLanguage.EN)
    print(f"{name} -> {trans_title} (phonetic: {phonetic})")

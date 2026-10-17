"""Contextual culinary translation service with anti-hallucination and prompt injection defenses."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import DishRecord
from backend.app.schemas.menu_analysis import SupportedLanguage
from backend.app.services.safety.safety_engine import CulinarySafetyEngine
from backend.app.services.translation.multilingual_engine import MultilingualCulinaryEngine
from backend.app.services.translation.prompts import (
    TRANSLATION_SYSTEM_PROMPT,
    TRANSLATION_USER_PROMPT,
)
from backend.app.services.vision.json_parser import ModelJsonParser

logger = get_logger(__name__)


class DishTranslationResult(BaseModel):
    """Normalized output from culinary translation."""

    translated_title: str
    phonetic_transcription: Optional[str] = None
    culinary_description: Optional[str] = None
    flavor_profile: Optional[str] = None


class BaseTranslationProvider(ABC):
    """Abstract interface for culinary translation."""

    @abstractmethod
    async def translate_dish(
        self,
        original_name: str,
        printed_desc: str,
        target_language: SupportedLanguage,
        rag_record: Optional[DishRecord] = None,
        price: Optional[str] = None,
    ) -> DishTranslationResult:
        """Translate and contextualize a single dish."""
        pass

    @abstractmethod
    async def translate_batch(
        self,
        items: List[Dict[str, Any]],
        target_language: SupportedLanguage,
    ) -> List[DishTranslationResult]:
        """Translate and contextualize a batch of dishes in one pass."""
        pass


# Curated multilingual repository of idiomatic dishes for high accuracy & offline deterministic testing
IDIOMATIC_DISH_REGISTRY: Dict[str, Dict[str, Any]] = {
    "螞蟻上樹": {
        "phonetic": "Mǎ Yǐ Shàng Shù",
        "translations": {
            "en": "Ants Climbing a Tree (Sichuan Cellophane Noodles with Minced Pork)",
            "es": "Hormigas Subiendo a un Árbol (Fideos Celofán de Sichuan con Cerdo)",
            "fr": "Fourmis Grimpant à un Arbre (Nouilles Cellophane au Porc Épicé)",
            "de": "Ameisen auf dem Baum (Glasnudeln mit Hackfleisch nach Sichuan-Art)",
            "ja": "アンツ・クライミング・ア・ツリー (四川風春雨と豚挽き肉のピリ辛炒め)",
            "zh": "螞蟻上樹 (傳統四川肉末粉絲)",
            "ar": "نمل يتسلق شجرة (نودلز سيتشوان مع لحم مفروم متبل)",
        },
        "description": "Classic Sichuan dish named poetically for bits of minced meat clinging to bean-thread noodles resembling ants on tree branches.",
        "flavor_profile": "savory, spicy, fermented bean paste aroma, umami",
    },
    "親子丼": {
        "phonetic": "Oyakodon",
        "translations": {
            "en": "Oyakodon (Chicken and Egg Rice Bowl)",
            "es": "Oyakodon (Tazón de Arroz con Pollo y Huevo)",
            "fr": "Oyakodon (Bol de Riz au Poulet et aux Œufs)",
            "de": "Oyakodon (Reisschale mit Huhn und Ei)",
            "ja": "親子丼",
            "zh": "親子丼 (日式雞肉雞蛋蓋飯)",
            "ar": "أوياكودون (وعاء أرز ياباني مع الدجاج والبيض)",
        },
        "description": "Comforting Japanese rice bowl dish featuring tender simmered chicken, softly cooked eggs, and scallions over steamed rice.",
        "flavor_profile": "sweet savory, dashi umami, comforting",
    },
    "醤油ラーメン": {
        "phonetic": "Shōyu Rāmen",
        "translations": {
            "en": "Shoyu Ramen (Tokyo Soy Sauce Broth Noodles)",
            "es": "Shoyu Ramen (Fideos Ramen en Caldo de Soja)",
            "fr": "Shoyu Ramen (Ramen au Bouillon de Sauce Soja)",
            "de": "Shoyu Ramen (Nudelsuppe mit Sojasaucenbrühe)",
            "ja": "醤油ラーメン",
            "zh": "醬油拉麵 (經典東京醬油高湯麵)",
            "ar": "شويو رامن (نودلز في مرق صلصة الصويا)",
        },
        "description": "Tokyo-style wheat ramen served in a clear seasoned soy sauce broth with chashu pork and scallions.",
        "flavor_profile": "savory, aromatic soy, rich umami",
    },
    "味噌ラーメン": {
        "phonetic": "Miso Rāmen",
        "translations": {
            "en": "Miso Ramen (Hokkaido Fermented Miso Broth Noodles)",
            "es": "Miso Ramen (Fideos Ramen en Caldo de Miso)",
            "fr": "Miso Ramen (Ramen au Bouillon de Miso)",
            "de": "Miso Ramen (Nudelsuppe mit fermentierter Misobrühe)",
            "ja": "味噌ラーメン",
            "zh": "味噌拉麵 (北海道特製味噌湯麵)",
            "ar": "ميسو رامن (نودلز في مرق الميسو المخمر)",
        },
        "description": "Hearty Hokkaido noodle soup enriched with fermented red miso paste, stir-fried vegetables, and sweet corn.",
        "flavor_profile": "hearty, robust, earthy miso savoriness",
    },
    "秘伝特製豚骨スープ": {
        "phonetic": "Hiden Tokusei Tonkotsu Sūpu",
        "translations": {
            "en": "House Secret Tonkotsu Pork Broth Special",
            "es": "Especial de Caldo Secreto Tonkotsu de Cerdo de la Casa",
            "fr": "Bouillon Spécial Secret de Porc Tonkotsu Maison",
            "de": "Spezielle Tonkotsu-Schweinebrühe nach Hausrezept",
            "ja": "秘伝特製豚骨スープ",
            "zh": "秘傳特製豚骨高湯",
            "ar": "مرق لحم الخنزير تونكوتسو السري الخاص بالمنزل",
        },
        "description": "Intensively simmered pork collagen broth formulated according to private house recipes.",
        "flavor_profile": "intense, rich collagen, garlicky",
    },
    "Spaghetti alla Carbonara": {
        "phonetic": "Spaghetti alla Karbonara",
        "translations": {
            "en": "Spaghetti alla Carbonara (Roman Cured Pork & Egg Pasta)",
            "es": "Espaguetis a la Carbonara (Pasta Romana con Guanciale y Huevo)",
            "fr": "Spaghetti à la Carbonara (Pâtes Romaines au Guanciale et Jaune d'Œuf)",
            "de": "Spaghetti alla Carbonara (Römische Pasta mit Guanciale und Eigelb)",
            "ja": "スパゲッティ・アッラ・カルボナーラ (ローマ風グアンチャーレと卵のパスタ)",
            "zh": "羅馬傳統培根蛋醬意大利麵",
            "ar": "سباغيتي كاربونارا (باستا رومانية مع البيض والجبن واللحم المقدد)",
        },
        "description": "Classic Roman pasta dish prepared with durum wheat spaghetti, cured pork jowl (guanciale), Pecorino Romano, and egg yolk.",
        "flavor_profile": "peppery, rich egg yolk, aged savory sheep cheese",
    },
    "Tiramisù della Nonna": {
        "phonetic": "Teeramisu della Nonna",
        "translations": {
            "en": "Grandmother's Tiramisu (Espresso & Mascarpone Dessert)",
            "es": "Tiramisú de la Abuela (Postre de Café Espresso y Mascarpone)",
            "fr": "Tiramisu de Grand-Mère (Dessert au Mascarpone et Café)",
            "de": "Tiramisu der Großmutter (Espresso-Mascarpone-Dessert)",
            "ja": "おばあちゃんのティラミス (エスプレッソとマスカルポーネのデザート)",
            "zh": "傳統意式提拉米蘇 (濃縮咖啡與馬斯卡彭奶酪甜點)",
            "ar": "تيراميسو الجدة (حلوى الإسبريسو والماسكاربوني)",
        },
        "description": "Layered Italian confection of espresso-soaked savoiardi ladyfingers and whipped mascarpone cream dusted with cocoa.",
        "flavor_profile": "bittersweet cocoa, espresso, rich creamy finish",
    },
    "فلافل": {
        "phonetic": "Falāfil",
        "translations": {
            "en": "Falafel (Crisp Herbed Chickpea Fritters)",
            "es": "Falafel (Bocaditos Crujientes de Garbanzos y Hierbas)",
            "fr": "Falafels (Beignets Croustillants de Pois Chiches aux Herbes)",
            "de": "Falafel (Knusprige Kichererbsenbällchen mit frischen Kräutern)",
            "ja": "ファラフェル (香草ひよこ豆のクリスピーコロッケ)",
            "zh": "法拉費 (中東香脆炸鷹嘴豆餅)",
            "ar": "فلافل (أقراص الحمص والأعشاب المقلية المقرمشة)",
        },
        "description": "Deep-fried croquettes made from ground spiced chickpeas and aromatic herbs, a cherished street food across the Levant.",
        "flavor_profile": "crisp, nutty, fragrant cumin and fresh coriander",
    },
    "حمص بالطحينة": {
        "phonetic": "Hummus bi-t-Tahīna",
        "translations": {
            "en": "Hummus with Tahini (Smooth Chickpea & Sesame Dip)",
            "es": "Hummus con Tahini (Puré Suave de Garbanzos y Sésamo)",
            "fr": "Houmous au Tahini (Crème de Pois Chiches et Sésame)",
            "de": "Hummus mit Tahini (Feine Kichererbsen-Sesam-Creme)",
            "ja": "フムス (ひよこ豆とタヒニのクリーミーディップ)",
            "zh": "鷹嘴豆芝麻醬 (中東傳統鷹嘴豆泥)",
            "ar": "حمص بالطحينة (مقبلات الحمص والطحينة وزيت الزيتون)",
        },
        "description": "Velvety purée of cooked chickpeas blended with roasted sesame tahini, fresh lemon juice, and extra virgin olive oil.",
        "flavor_profile": "creamy, nutty sesame, tangy citrus, garlic",
    },
    "Pizza Margherita": {
        "phonetic": "Pizza Margherita",
        "translations": {
            "en": "Pizza Margherita (Neapolitan Tomato, Mozzarella & Basil Pizza)",
            "es": "Pizza Margarita (Pizza Napolitana con Tomate, Mozzarella y Albahaca)",
            "fr": "Pizza Margherita (Pizza Napolitaine Tomates, Mozzarella et Basilic)",
            "de": "Pizza Margherita (Neapolitanische Pizza mit Tomate, Mozzarella und Basilikum)",
            "ja": "ピッツァ・マルゲリータ (トマト、モッツァレラ、バジルのピッツァ)",
            "zh": "瑪格麗特披薩 (經典意式番茄水牛芝士羅勒披薩)",
            "ar": "بيتزا مارغريتا (بيتزا نابوليتانية مع الطماطم والموزاريلا والريحان)",
        },
        "description": "Traditional Neapolitan wood-fired pizza topped with San Marzano tomato sauce, fresh mozzarella, and fresh basil.",
        "flavor_profile": "bright tomato acidity, milky cheese, aromatic basil, blistered crust",
    },
    "Tacos al Pastor": {
        "phonetic": "Tah-kohs ahl Pahs-tohr",
        "translations": {
            "en": "Tacos al Pastor (Spit-Roasted Marinated Pork Tacos)",
            "es": "Tacos al Pastor (Tacos de Cerdo Adobado al Trompo)",
            "fr": "Tacos al Pastor (Tacos de Porc Mariné et Rôti à la Broche)",
            "de": "Tacos al Pastor (Marinierte Schweinefleisch-Tacos vom Drehspieß)",
            "ja": "タコス・アル・パストール (回転串焼き味付け豚肉のタコス)",
            "zh": "墨西哥烤豬肉卷餅 (特製醃料旋轉烤肉卷餅)",
            "ar": "تاكوس أل باستور (تاكو لحم خنزير متبل ومحمص على السيخ)",
        },
        "description": "Iconic Mexican corn tortilla tacos filled with thinly sliced pork marinated in achiote and chiles, served with pineapple and cilantro.",
        "flavor_profile": "smoky, sweet pineapple acidity, citrusy achiote spice",
    },
    "Guacamole Tradicional": {
        "phonetic": "Gwah-kah-moh-leh",
        "translations": {
            "en": "Traditional Guacamole (Hand-Crushed Fresh Avocado Dip)",
            "es": "Guacamole Tradicional (Dip de Aguacate Machacado a Mano)",
            "fr": "Guacamole Traditionnel (Écrasé d'Avocat Frais au Citron Vert)",
            "de": "Traditionelle Guacamole (Frisch zerstoßene Avocado mit Limette)",
            "ja": "トラディショナル・ワカモレ (手つぶしフレッシュアボカドディップ)",
            "zh": "傳統特製牛油果醬 (手搗新鮮鱷梨青檸蘸醬)",
            "ar": "غواكامولي تقليدي (غموس الأفوكادو الطازج المهروس يدوياً)",
        },
        "description": "Pre-Columbian Mexican avocado preparation hand-crushed in a molcajete with lime, cilantro, and serrano chile.",
        "flavor_profile": "buttery avocado, bright lime, fresh herbal cilantro",
    },
    "抹茶アイスクリーム": {
        "phonetic": "Matcha Aisu Kurīmu",
        "translations": {
            "en": "Matcha Green Tea Ice Cream",
            "es": "Helado de Té Verde Matcha",
            "fr": "Glace au Thé Vert Matcha",
            "de": "Matcha-Grüntee-Eis",
            "ja": "抹茶アイスクリーム",
            "zh": "日式宇治抹茶冰淇淋",
            "ar": "آيس كريم الشاي الأخضر ماتشا",
        },
        "description": "Chilled dairy ice cream flavored with stone-ground Japanese green tea powder.",
        "flavor_profile": "bittersweet green tea, rich creamy sweetness",
    },
}


def romanize_hangul(text: str) -> str:
    """Standard Revised Romanization for Korean Hangul syllables."""
    CHOSEONG = ['g', 'kk', 'n', 'd', 'tt', 'r', 'm', 'b', 'pp', 's', 'ss', '', 'j', 'jj', 'ch', 'k', 't', 'p', 'h']
    JUNGSEONG = ['a', 'ae', 'ya', 'yae', 'eo', 'e', 'yeo', 'ye', 'o', 'wa', 'wae', 'oe', 'yo', 'u', 'wo', 'we', 'wi', 'yu', 'eu', 'ui', 'i']
    JONGSEONG = ['', 'k', 'k', 'ks', 'n', 'nj', 'nh', 'd', 'l', 'lg', 'lm', 'lb', 'ls', 'lt', 'lp', 'lh', 'm', 'b', 'bs', 's', 'ss', 'ng', 'j', 'ch', 'k', 't', 'p', 'h']
    result = []
    for char in text:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            s_idx = code - 0xAC00
            cho = s_idx // 588
            jung = (s_idx % 588) // 28
            jong = s_idx % 28
            syllable = CHOSEONG[cho] + JUNGSEONG[jung] + JONGSEONG[jong]
            result.append(syllable)
        else:
            result.append(char)
    romanized = "".join(result).strip()
    return " ".join(word.capitalize() for word in romanized.split() if word)


KOREAN_TERMS: Dict[str, str] = {
    "블랙": "Black",
    "아이스": "Iced",
    "핫": "Hot",
    "밀크티": "Milk Tea",
    "스무디": "Smoothie",
    "페인트": "Paint (Marbled Tea)",
    "가을": "Autumn Special",
    "우롱": "Oolong",
    "그린": "Green",
    "타로": "Taro",
    "초코": "Chocolate",
    "망고": "Mango",
    "딸기": "Strawberry",
    "자몽": "Grapefruit",
    "레몬": "Lemon",
    "복숭아": "Peach",
    "포도": "Grape",
    "티": "Tea",
    "커피": "Coffee",
    "라떼": "Latte",
    "아메리카노": "Americano",
    "치즈폼": "Cheese Foam",
    "펄": "Tapioca Pearls",
    "비빔밥": "Bibimbap (Mixed Rice)",
    "불고기": "Bulgogi (Marinated Beef)",
    "김치": "Kimchi",
    "떡볶이": "Tteokbokki (Spicy Rice Cakes)",
    "만두": "Dumplings",
    "삼겹살": "Grilled Pork Belly",
    "갈비": "Short Ribs",
    "치킨": "Korean Fried Chicken",
    "라면": "Ramen",
    "볶음밥": "Fried Rice",
    "찌개": "Stew",
    "탕": "Soup",
}


class DeterministicCulinaryTranslator(BaseTranslationProvider):
    """Reliable offline deterministic translator with curated cultural registries."""

    async def translate_dish(
        self,
        original_name: str,
        printed_desc: str,
        target_language: SupportedLanguage,
        rag_record: Optional[DishRecord] = None,
        price: Optional[str] = None,
    ) -> DishTranslationResult:
        results = await self.translate_batch(
            items=[
                {
                    "original_name": original_name,
                    "printed_desc": printed_desc,
                    "target_language": target_language,
                    "rag_record": rag_record,
                    "price": price,
                }
            ],
            target_language=target_language,
        )
        return results[0]

    async def translate_batch(
        self,
        items: List[Dict[str, Any]],
        target_language: SupportedLanguage,
    ) -> List[DishTranslationResult]:
        lang = target_language.value.lower()
        results: List[DishTranslationResult] = []

        for item in items:
            orig = item.get("original_name") or ""
            printed_desc = item.get("printed_desc") or ""
            rag_record = item.get("rag_record")
            clean_name = CulinarySafetyEngine.sanitize_untrusted_text(orig.strip())

            # 1. Match against idiomatic dish registry - strictly by dish name, never unverified RAG record
            matched = False
            for canonical_name, entry in IDIOMATIC_DISH_REGISTRY.items():
                if clean_name.lower() == canonical_name.lower():
                    translated_title = entry["translations"].get(lang, entry["translations"].get("en", clean_name))
                    # Only attach description if printed or verified
                    desc = printed_desc.strip() if printed_desc.strip() else entry.get("description")
                    results.append(
                        DishTranslationResult(
                            translated_title=translated_title,
                            phonetic_transcription=entry.get("phonetic"),
                            culinary_description=desc,
                            flavor_profile=entry.get("flavor_profile"),
                        )
                    )
                    matched = True
                    break
            if matched:
                continue

            # 2. Match against RAG record only if verified and validated
            if rag_record is not None and getattr(rag_record, "verification_status", None) == "verified":
                title = f"{rag_record.native_name}"
                if getattr(rag_record, "aliases", None):
                    title += f" ({rag_record.aliases[0]})"
                results.append(
                    DishTranslationResult(
                        translated_title=title,
                        phonetic_transcription=getattr(rag_record, "phonetic_spelling", None),
                        culinary_description=getattr(rag_record, "cultural_narrative", None) or (printed_desc if printed_desc else None),
                        flavor_profile=getattr(rag_record, "flavor_profile", None),
                    )
                )
                continue

            # 3. Universal Multilingual Culinary Engine across all supported languages
            clean_desc_input = printed_desc.strip() if printed_desc and printed_desc.strip() else None
            trans_title, phonetic, trans_desc, flavor = MultilingualCulinaryEngine.translate_dish(
                original_name=clean_name,
                printed_desc=clean_desc_input,
                target_lang=target_language,
            )

            results.append(
                DishTranslationResult(
                    translated_title=trans_title,
                    phonetic_transcription=phonetic,
                    culinary_description=trans_desc,
                    flavor_profile=flavor,
                )
            )

        return results


TARGET_LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "ja": "Japanese",
    "zh": "Chinese Simplified",
    "ar": "Arabic",
    "pt": "Portuguese",
    "ko": "Korean",
    "hi": "Hindi",
    "ru": "Russian",
}

_TRANSLATION_CACHE: Dict[str, DishTranslationResult] = {}


class OllamaTranslationProvider(BaseTranslationProvider):
    """Live LLM translator via Ollama with low temperature and anti-injection guardrails."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.model_name = self.settings.translation_model or self.settings.vision_model
        self.temperature = 0.1
        self.timeout = 45.0
        self.fallback = DeterministicCulinaryTranslator()

    def _make_cache_key(self, lang_code: str, orig_name: str, printed_desc: str) -> str:
        clean_name = (orig_name or "").strip().lower()
        clean_desc = (printed_desc or "").strip().lower()
        return f"{lang_code}:{clean_name}:{clean_desc}"

    async def translate_dish(
        self,
        original_name: str,
        printed_desc: str,
        target_language: SupportedLanguage,
        rag_record: Optional[DishRecord] = None,
        price: Optional[str] = None,
    ) -> DishTranslationResult:
        batch_res = await self.translate_batch(
            items=[
                {
                    "original_name": original_name,
                    "printed_desc": printed_desc,
                    "target_language": target_language,
                    "rag_record": rag_record,
                    "price": price,
                }
            ],
            target_language=target_language,
        )
        return batch_res[0]

    async def translate_batch(
        self,
        items: List[Dict[str, Any]],
        target_language: SupportedLanguage,
    ) -> List[DishTranslationResult]:
        if not items:
            return []

        lang_code = target_language.value if hasattr(target_language, "value") else str(target_language)
        lang_name = TARGET_LANGUAGE_NAMES.get(lang_code, lang_code.upper())

        # Check in-memory cache first
        final_results: List[Optional[DishTranslationResult]] = [None] * len(items)
        uncached_indices: List[int] = []

        for i, itm in enumerate(items):
            c_key = self._make_cache_key(
                lang_code=lang_code,
                orig_name=str(itm.get("original_name") or ""),
                printed_desc=str(itm.get("printed_desc") or ""),
            )
            if c_key in _TRANSLATION_CACHE:
                final_results[i] = _TRANSLATION_CACHE[c_key]
            else:
                uncached_indices.append(i)

        # If everything was cached, return instantly
        if not uncached_indices:
            return [r for r in final_results if r is not None]

        # First obtain fallback results for uncached items as safe baseline
        uncached_items_list = [items[idx] for idx in uncached_indices]
        fallback_results = await self.fallback.translate_batch(items=uncached_items_list, target_language=target_language)

        # Build prompt for uncached items
        prompt_items = []
        for local_id, orig_idx in enumerate(uncached_indices):
            itm = items[orig_idx]
            prompt_items.append(
                {
                    "id": local_id,
                    "original_name": CulinarySafetyEngine.sanitize_untrusted_text(str(itm.get("original_name") or "")),
                    "description": CulinarySafetyEngine.sanitize_untrusted_text(str(itm.get("printed_desc") or "")),
                    "price": str(itm.get("price") or ""),
                }
            )

        system_prompt = (
            f"You are a professional culinary translator. Translate all menu items into natural, idiomatic {lang_name} ({lang_code}).\n"
            "CRITICAL ACCURACY RULES:\n"
            f"- Translate every descriptive dish name ('translated_title') and printed description ('culinary_description') into natural {lang_name}.\n"
            f"- NEVER simply return the romanized source text or source script as the translated_title if a natural translation exists in {lang_name}.\n"
            "- Preserve verified brand names or recognized proper nouns, but translate all descriptive words around them.\n"
            "- If an item has NO description on the printed menu (description is empty or null), you MUST set culinary_description to null. NEVER invent recipes, ingredients, or descriptions.\n"
            "- If an item has a printed description, translate it faithfully into {lang_name}.\n"
            "- Do not produce <think> tags or reasoning commentary.\n"
            "- Return an RFC 8259 JSON object matching this schema:\n"
            '{"items": [{"id": 0, "translated_title": "Translated dish name", "phonetic_transcription": "Pronunciation in Latin alphabet", "culinary_description": "Translated description or null"}]}'
        )

        CHUNK_SIZE = 6
        for chunk_offset in range(0, len(uncached_indices), CHUNK_SIZE):
            chunk_slice = uncached_indices[chunk_offset : chunk_offset + CHUNK_SIZE]
            chunk_prompt_items = []
            for sub_id, orig_idx in enumerate(chunk_slice):
                itm = items[orig_idx]
                chunk_prompt_items.append(
                    {
                        "id": sub_id,
                        "original_name": CulinarySafetyEngine.sanitize_untrusted_text(str(itm.get("original_name") or "")),
                        "description": CulinarySafetyEngine.sanitize_untrusted_text(str(itm.get("printed_desc") or "")),
                        "price": str(itm.get("price") or ""),
                    }
                )

            prefill = '{\n  "items": [\n    {\n      "id": 0,'
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps({"items": chunk_prompt_items}, ensure_ascii=False)},
                    {"role": "assistant", "content": prefill},
                ],
                "options": {
                    "temperature": self.temperature,
                    "num_predict": min(2048, 220 * len(chunk_prompt_items) + 128),
                    "num_ctx": 4096,
                },
                "stream": False,
            }

            try:
                async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                    logger.info(
                        f"Dispatching batch translation chunk ({len(chunk_prompt_items)} items to {lang_name}) to Ollama..."
                    )
                    resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        msg_content = data.get("message", {}).get("content", "")
                        full_json_str = prefill + msg_content
                        clean_text = ModelJsonParser.clean_raw_output(full_json_str)

                        # In case of unclosed array or braces, attempt recovery
                        if not clean_text.rstrip().endswith("}"):
                            if not clean_text.rstrip().endswith("]"):
                                clean_text = clean_text.rstrip().rstrip(",") + "\n    }\n  ]\n}"
                            else:
                                clean_text = clean_text.rstrip().rstrip(",") + "\n}"

                        parsed = json.loads(clean_text)
                        if isinstance(parsed, dict) and "items" in parsed and isinstance(parsed["items"], list):
                            ollama_map: Dict[int, Dict[str, Any]] = {}
                            for o_item in parsed["items"]:
                                if isinstance(o_item, dict) and "id" in o_item:
                                    ollama_map[int(o_item["id"])] = o_item

                            for sub_id, orig_idx in enumerate(chunk_slice):
                                itm = items[orig_idx]
                                fb_idx = chunk_offset + sub_id
                                clean_desc_orig = str(itm.get("printed_desc") or "").strip()
                                c_key = self._make_cache_key(
                                    lang_code=lang_code,
                                    orig_name=str(itm.get("original_name") or ""),
                                    printed_desc=clean_desc_orig,
                                )
                                if sub_id in ollama_map and ollama_map[sub_id].get("translated_title"):
                                    oi = ollama_map[sub_id]
                                    # Never invent description if original menu had no printed description
                                    resolved_desc = None
                                    if clean_desc_orig:
                                        resolved_desc = oi.get("culinary_description") or fallback_results[fb_idx].culinary_description

                                    res = DishTranslationResult(
                                        translated_title=str(oi.get("translated_title")),
                                        phonetic_transcription=oi.get("phonetic_transcription") or fallback_results[fb_idx].phonetic_transcription,
                                        culinary_description=resolved_desc,
                                        flavor_profile=oi.get("flavor_profile") or fallback_results[fb_idx].flavor_profile,
                                    )
                                    final_results[orig_idx] = res
                                    _TRANSLATION_CACHE[c_key] = res
                                else:
                                    final_results[orig_idx] = fallback_results[fb_idx]
                                    _TRANSLATION_CACHE[c_key] = fallback_results[fb_idx]

            except Exception as exc:
                logger.warning(f"Live Ollama translation chunk failed ({exc}); applying verified cultural fallback")

            # Fallback for any items in this chunk that remain unpopulated
            for sub_id, orig_idx in enumerate(chunk_slice):
                if final_results[orig_idx] is None:
                    fb_idx = chunk_offset + sub_id
                    itm = items[orig_idx]
                    fb_res = fallback_results[fb_idx]
                    final_results[orig_idx] = fb_res
                    c_key = self._make_cache_key(
                        lang_code=lang_code,
                        orig_name=str(itm.get("original_name") or ""),
                        printed_desc=str(itm.get("printed_desc") or ""),
                    )
                    _TRANSLATION_CACHE[c_key] = fb_res

        return [r for r in final_results if r is not None]


class CulinaryTranslatorService:
    """Unified service dispatching culinary translation with offline deterministic guarantee."""

    def __init__(
        self,
        provider: Optional[BaseTranslationProvider] = None,
        settings: Optional[Any] = None,
        use_deterministic_only: bool = False,
    ):
        if use_deterministic_only:
            self.provider: BaseTranslationProvider = provider or DeterministicCulinaryTranslator()
        else:
            self.provider = provider or OllamaTranslationProvider(settings=settings)

    def invalidate_cache(self) -> None:
        """Clear translation in-memory cache."""
        global _TRANSLATION_CACHE
        _TRANSLATION_CACHE.clear()

    async def translate_dish(
        self,
        original_name: str,
        printed_desc: str,
        target_language: SupportedLanguage,
        rag_record: Optional[DishRecord] = None,
        price: Optional[str] = None,
    ) -> DishTranslationResult:
        return await self.provider.translate_dish(
            original_name=original_name,
            printed_desc=printed_desc,
            target_language=target_language,
            rag_record=rag_record,
            price=price,
        )

    async def translate_batch(
        self,
        items: List[Dict[str, Any]],
        target_language: SupportedLanguage,
    ) -> List[DishTranslationResult]:
        return await self.provider.translate_batch(
            items=items,
            target_language=target_language,
        )


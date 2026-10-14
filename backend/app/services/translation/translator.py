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
        lang = target_language.value.lower()
        clean_name = CulinarySafetyEngine.sanitize_untrusted_text(original_name.strip())

        # 1. Match against idiomatic dish registry
        for canonical_name, entry in IDIOMATIC_DISH_REGISTRY.items():
            if clean_name.lower() == canonical_name.lower() or (
                rag_record and rag_record.native_name.lower() == canonical_name.lower()
            ):
                translated_title = entry["translations"].get(lang, entry["translations"].get("en", clean_name))
                return DishTranslationResult(
                    translated_title=translated_title,
                    phonetic_transcription=entry.get("phonetic"),
                    culinary_description=entry.get("description"),
                    flavor_profile=entry.get("flavor_profile"),
                )

        # 2. Match against RAG record if available
        if rag_record is not None:
            title = f"{rag_record.native_name}"
            if rag_record.aliases:
                title += f" ({rag_record.aliases[0]})"
            return DishTranslationResult(
                translated_title=title,
                phonetic_transcription=rag_record.phonetic_spelling,
                culinary_description=rag_record.cultural_narrative or (printed_desc if printed_desc else None),
                flavor_profile=rag_record.flavor_profile,
            )

        # 3. Fallback for unlisted dishes
        clean_desc = CulinarySafetyEngine.sanitize_untrusted_text(printed_desc.strip()) if printed_desc else None
        return DishTranslationResult(
            translated_title=f"{clean_name}",
            phonetic_transcription=None,
            culinary_description=clean_desc or "Traditional regional preparation.",
            flavor_profile=None,
        )


class OllamaTranslationProvider(BaseTranslationProvider):
    """Live LLM translator via Ollama with low temperature and anti-injection guardrails."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.model_name = self.settings.translation_model or self.settings.vision_model
        self.temperature = self.settings.translation_temperature
        self.timeout = self.settings.translation_timeout_seconds
        self.fallback = DeterministicCulinaryTranslator()

    async def translate_dish(
        self,
        original_name: str,
        printed_desc: str,
        target_language: SupportedLanguage,
        rag_record: Optional[DishRecord] = None,
        price: Optional[str] = None,
    ) -> DishTranslationResult:
        # Sanitize input against prompt injections
        sanitized_name = CulinarySafetyEngine.sanitize_untrusted_text(original_name)
        sanitized_desc = CulinarySafetyEngine.sanitize_untrusted_text(printed_desc)

        kb_evidence = "None"
        if rag_record:
            kb_evidence = json.dumps(
                {
                    "dish_id": rag_record.dish_id,
                    "native_name": rag_record.native_name,
                    "phonetic": rag_record.phonetic_spelling,
                    "category": rag_record.canonical_category,
                    "base_ingredients": rag_record.base_ingredients,
                    "cooking_technique": rag_record.cooking_technique,
                    "cultural_narrative": rag_record.cultural_narrative,
                    "flavor_profile": rag_record.flavor_profile,
                    "verification_status": rag_record.verification_status,
                },
                ensure_ascii=False,
            )

        user_content = (
            TRANSLATION_USER_PROMPT
            .replace("{target_language}", target_language.value)
            .replace("{original_name}", sanitized_name)
            .replace("{printed_desc}", sanitized_desc)
            .replace("{price}", price or "Not listed")
            .replace("{kb_evidence}", kb_evidence)
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "options": {
                "temperature": self.temperature,
                "num_predict": 256,
            },
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data.get("message", {}).get("content", "")
                    clean_text = ModelJsonParser.clean_raw_output(raw_text)
                    parsed = json.loads(clean_text)
                    if isinstance(parsed, dict) and "translated_title" in parsed:
                        return DishTranslationResult(
                            translated_title=str(parsed.get("translated_title")),
                            phonetic_transcription=parsed.get("phonetic_transcription"),
                            culinary_description=parsed.get("culinary_description"),
                            flavor_profile=parsed.get("flavor_profile"),
                        )
        except Exception as exc:
            logger.debug("Ollama translation call bypassed or failed; using deterministic fallback: %s", exc)

        # Graceful fallback to deterministic engine
        return await self.fallback.translate_dish(
            original_name=original_name,
            printed_desc=printed_desc,
            target_language=target_language,
            rag_record=rag_record,
            price=price,
        )


class CulinaryTranslatorService:
    """Unified service dispatching culinary translation with offline deterministic guarantee."""

    def __init__(
        self,
        provider: Optional[BaseTranslationProvider] = None,
        use_deterministic_only: bool = False,
    ):
        if use_deterministic_only:
            self.provider: BaseTranslationProvider = DeterministicCulinaryTranslator()
        else:
            self.provider = provider or OllamaTranslationProvider()

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

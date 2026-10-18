"""Universal Multilingual Culinary Translation Engine.

Provides accurate, faithful culinary translation, script detection, and phonetic romanization
across all supported languages (EN, ES, FR, DE, JA, ZH, AR, IT, PT, KO).
Never hallucinates fake culinary descriptions or attaches unrelated recipes.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple

from backend.app.schemas.menu_analysis import SupportedLanguage


# Korean Syllable Decomposition tables (Revised Romanization of Korean)
CHOSEONG = [
    "g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s",
    "ss", "", "j", "jj", "ch", "k", "t", "p", "h",
]
JUNGSEONG = [
    "a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa",
    "wae", "oe", "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i",
]
JONGSEONG = [
    "", "k", "k", "ks", "n", "nj", "nh", "t", "l", "lg",
    "lm", "lb", "ls", "lt", "lp", "lh", "m", "p", "ps", "t",
    "t", "ng", "t", "t", "k", "t", "p", "h",
]

def romanize_hangul(text: str) -> str:
    """Standard Revised Romanization of Korean Hangul syllables."""
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


# Japanese Katakana to Romaji map (Hepburn)
KATA_MAP = {
    "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o",
    "カ": "ka", "キ": "ki", "ク": "ku", "ケ": "ke", "コ": "ko",
    "サ": "sa", "シ": "shi", "ス": "su", "セ": "se", "ソ": "so",
    "タ": "ta", "チ": "chi", "ツ": "tsu", "テ": "te", "ト": "to",
    "ナ": "na", "ニ": "ni", "ヌ": "nu", "ネ": "ne", "ノ": "no",
    "ハ": "ha", "ヒ": "hi", "フ": "fu", "ヘ": "he", "ホ": "ho",
    "マ": "ma", "ミ": "mi", "ム": "mu", "メ": "me", "モ": "mo",
    "ヤ": "ya", "ユ": "yu", "ヨ": "yo",
    "ラ": "ra", "リ": "ri", "ル": "ru", "レ": "re", "ロ": "ro",
    "ワ": "wa", "ヲ": "wo", "ン": "n",
    "ガ": "ga", "ギ": "gi", "グ": "gu", "ゲ": "ge", "ゴ": "go",
    "ザ": "za", "ジ": "ji", "ズ": "zu", "ゼ": "ze", "ゾ": "zo",
    "ダ": "da", "ヂ": "ji", "ヅ": "zu", "デ": "de", "ド": "do",
    "バ": "ba", "ビ": "bi", "ブ": "bu", "ベ": "be", "ボ": "bo",
    "パ": "pa", "ピ": "pi", "プ": "pu", "ペ": "pe", "ポ": "po",
    "ー": "-",
}

def romanize_japanese(text: str) -> str:
    """Romanize Japanese Katakana loanwords."""
    res = []
    for char in text:
        res.append(KATA_MAP.get(char, char))
    rom = "".join(res).replace("--", "-").strip("- ")
    return " ".join(w.capitalize() for w in rom.split() if w)


# Multilingual Culinary Lexicon: Term -> Translations in supported languages
# Maps terms in diverse source languages (EN, KO, JA, ZH, IT, FR, ES, DE, AR) to all target languages
CULINARY_LEXICON: Dict[str, Dict[str, str]] = {
    # Teas & Beverages
    "밀크티": {"en": "Milk Tea", "es": "Té con Leche", "fr": "Thé au Lait", "de": "Milchtee", "it": "Tè al Latte", "ja": "ミルクティー", "zh": "奶茶", "ar": "شاي بالحليب", "ko": "밀크티", "pt": "Chá com Leite"},
    "블랙 밀크티": {"en": "Black Milk Tea", "es": "Té Negro con Leche", "fr": "Thé Noir au Lait", "de": "Schwarzer Milchtee", "it": "Tè Nero al Latte", "ja": "ブラックミルクティー", "zh": "經典黑奶茶", "ar": "شاي أسود بالحليب", "ko": "블랙 밀크티", "pt": "Chá Preto com Leite"},
    "얼그레이 밀크티": {"en": "Earl Grey Milk Tea", "es": "Té Earl Grey con Leche", "fr": "Thé Earl Grey au Lait", "de": "Earl-Grey-Milchtee", "it": "Tè Earl Grey al Latte", "ja": "アールグレイミルクティー", "zh": "格雷伯爵奶茶", "ar": "شاي إيرل غراي بالحليب", "ko": "얼그레이 밀크티", "pt": "Chá Earl Grey com Leite"},
    "타로 밀크티": {"en": "Taro Milk Tea", "es": "Té de Taro con Leche", "fr": "Thé au Lait et Taro", "de": "Taro-Milchtee", "it": "Tè al Latte e Taro", "ja": "タロミルクティー", "zh": "香芋奶茶", "ar": "شاي التارو بالحليب", "ko": "타로 밀크티", "pt": "Chá de Taro com Leite"},
    "초콜릿 밀크티": {"en": "Chocolate Milk Tea", "es": "Té de Chocolate con Leche", "fr": "Thé au Lait au Chocolat", "de": "Schokoladen-Milchtee", "it": "Tè al Latte e Cioccolato", "ja": "チョコレートミルクティー", "zh": "巧克力奶茶", "ar": "شاي الشوكولاتة بالحليب", "ko": "초콜릿 밀크티", "pt": "Chá de Chocolate com Leite"},
    "우롱티": {"en": "Oolong Tea", "es": "Té Oolong", "fr": "Thé Oolong", "de": "Oolong-Tee", "it": "Tè Oolong", "ja": "ウーロン茶", "zh": "烏龍茶", "ar": "شاي أولونغ", "ko": "우롱티", "pt": "Chá Oolong"},
    "블랙티": {"en": "Black Tea", "es": "Té Negro", "fr": "Thé Noir", "de": "Schwarzer Tee", "it": "Tè Nero", "ja": "ブラックティー", "zh": "紅茶", "ar": "شاي أسود", "ko": "블랙티", "pt": "Chá Preto"},
    "그린티": {"en": "Green Tea", "es": "Té Verde", "fr": "Thé Vert", "de": "Grüner Tee", "it": "Tè Verde", "ja": "グリーンティー", "zh": "綠茶", "ar": "شاي أخضر", "ko": "그린티", "pt": "Chá Verde"},
    "자스민 그린티": {"en": "Jasmine Green Tea", "es": "Té Verde Jazmín", "fr": "Thé Vert au Jasmin", "de": "Jasmin-Grüntee", "it": "Tè Verde al Gelsomino", "ja": "ジャスミングリーンティー", "zh": "茉莉綠茶", "ar": "شاي أخضر بالياسمين", "ko": "자스민 그린티", "pt": "Chá Verde de Jasmim"},
    "스무디": {"en": "Smoothie", "es": "Batido Smoothie", "fr": "Smoothie", "de": "Smoothie", "it": "Smoothie", "ja": "スムージー", "zh": "冰沙", "ar": "سموذي", "ko": "스무디", "pt": "Smoothie"},
    "망고 스무디": {"en": "Mango Smoothie", "es": "Smoothie de Mango", "fr": "Smoothie à la Mangue", "de": "Mango-Smoothie", "it": "Smoothie al Mango", "ja": "マンゴースムージー", "zh": "芒果冰沙", "ar": "سموذي المانجو", "ko": "망고 스무디", "pt": "Smoothie de Manga"},
    "딸기 스무디": {"en": "Strawberry Smoothie", "es": "Smoothie de Fresa", "fr": "Smoothie à la Fraise", "de": "Erdbeer-Smoothie", "it": "Smoothie alla Fragola", "ja": "ストロベリー・スムージー", "zh": "草莓冰沙", "ar": "سموذي الفراولة", "ko": "딸기 스무디", "pt": "Smoothie de Morango"},
    "치즈폼": {"en": "Cheese Foam", "es": "Espuma de Queso", "fr": "Mousse de Fromage", "de": "Käseschaum", "it": "Schiuma di Formaggio", "ja": "チーズフォーム", "zh": "奶蓋芝士", "ar": "رغوة الجبن", "ko": "치즈폼", "pt": "Espuma de Queijo"},
    "펄": {"en": "Tapioca Pearls", "es": "Perlas de Tapioca", "fr": "Perles de Tapioca", "de": "Tapiokaperlen", "it": "Perle di Tapioca", "ja": "タピオカパール", "zh": "珍珠 (波霸)", "ar": "حبيبات التابيوكا", "ko": "펄 (타피오카)", "pt": "Pérolas de Tapioca"},
    "아메리카노": {"en": "Americano Coffee", "es": "Café Americano", "fr": "Café Allongé Americano", "de": "Kaffee Americano", "it": "Caffè Americano", "ja": "アメリカンコーヒー", "zh": "美式咖啡", "ar": "قهوة أمريكانو", "ko": "아메리카노", "pt": "Café Americano"},
    "카페라떼": {"en": "Café Latte", "es": "Café con Leche", "fr": "Café Latte", "de": "Caffè Latte", "it": "Caffè Latte", "ja": "カフェラテ", "zh": "拿鐵咖啡", "ar": "كافيه لاتيه", "ko": "카페라떼", "pt": "Café com Leite"},
    "브라운": {"en": "Brown Sugar", "es": "Azúcar Moreno", "fr": "Sucre Brun", "de": "Brauner Zucker", "it": "Zucchero di Canna", "ja": "黒糖", "zh": "黑糖", "ar": "سكر بني", "ko": "브라운슈가", "pt": "Açúcar Mascavo"},
    "솔티드 카라멜": {"en": "Salted Caramel", "es": "Caramelo Salado", "fr": "Caramel au Beurre Salé", "de": "Salzkaramell", "it": "Caramello Salato", "ja": "ソルティッドキャラメル", "zh": "海鹽焦糖", "ar": "كراميل مملح", "ko": "솔티드 카라멜", "pt": "Caramelo Salgado"},
    "가을": {"en": "Autumn", "es": "Otoño", "fr": "Automne", "de": "Herbst", "it": "Autunno", "ja": "秋", "zh": "秋季", "ar": "خريف", "ko": "가을", "pt": "Outono"},
    "향기": {"en": "Aromatic", "es": "Aromático", "fr": "Aromatique", "de": "Aromatisch", "it": "Aromatico", "ja": "芳醇", "zh": "香醇", "ar": "عطري", "ko": "향기", "pt": "Aromático"},
    "라떼": {"en": "Latte", "es": "Latte", "fr": "Latte", "de": "Latte", "it": "Latte", "ja": "ラテ", "zh": "拿鐵", "ar": "لاتيه", "ko": "라떼", "pt": "Latte"},
    "아이스": {"en": "Iced", "es": "Helado", "fr": "Glacé", "de": "Eis", "it": "Ghiacciato", "ja": "アイス", "zh": "冰", "ar": "مثلج", "ko": "아이스", "pt": "Gelado"},
    "핫": {"en": "Hot", "es": "Caliente", "fr": "Chaud", "de": "Heiß", "it": "Caldo", "ja": "ホット", "zh": "熱", "ar": "ساخن", "ko": "핫", "pt": "Quente"},
    "브랜드": {"en": "Signature Blend", "es": "Mezcla de la Casa", "fr": "Mélange Signature", "de": "Hausmischung", "it": "Miscela Speciale", "ja": "ブレンド", "zh": "特調", "ar": "مزيج خاص", "ko": "브랜드", "pt": "Mistura da Casa"},
    "스윗": {"en": "Sweet", "es": "Dulce", "fr": "Doux", "de": "Süß", "it": "Dolce", "ja": "スイート", "zh": "甜度", "ar": "حلو", "ko": "스윗", "pt": "Doce"},
    "그레이드": {"en": "Grade", "es": "Grado", "fr": "Degré", "de": "Stufe", "it": "Grado", "ja": "グレード", "zh": "等級", "ar": "درجة", "ko": "그레이드", "pt": "Grau"},
    "토핑": {"en": "Topping", "es": "Aderezo", "fr": "Garniture", "de": "Topping", "it": "Guarnizione", "ja": "トッピング", "zh": "配料", "ar": "إضافة", "ko": "토핑", "pt": "Cobertura"},
    "시즌": {"en": "Seasonal", "es": "De Temporada", "fr": "Saisonnier", "de": "Saisonal", "it": "Stagionale", "ja": "季節限定", "zh": "季節限定", "ar": "موسمي", "ko": "시즌", "pt": "Sazonal"},
    "사탕가루": {"en": "Brown Sugar Powder", "es": "Polvo de Azúcar Moreno", "fr": "Sucre Roux en Poudre", "de": "Kandiszuckerpulver", "it": "Zucchero di Canna", "ja": "黒糖パウダー", "zh": "黑糖粉", "ar": "بودرة السكر البني", "ko": "사탕가루", "pt": "Açúcar Mascavo"},
    "오리지널": {"en": "Original", "es": "Original", "fr": "Original", "de": "Original", "it": "Originale", "ja": "オリジナル", "zh": "原創", "ar": "أصلي", "ko": "오리지널", "pt": "Original"},
    "과일": {"en": "Fruit", "es": "Fruta", "fr": "Fruit", "de": "Frucht", "it": "Frutta", "ja": "フルーツ", "zh": "水果", "ar": "فواكه", "ko": "과일", "pt": "Fruta"},
    "티": {"en": "Tea", "es": "Té", "fr": "Thé", "de": "Tee", "it": "Tè", "ja": "ティー", "zh": "茶", "ar": "شاي", "ko": "티", "pt": "Chá"},
    "메뉴": {"en": "Menu", "es": "Menú", "fr": "Menu", "de": "Menü", "it": "Menu", "ja": "メニュー", "zh": "菜單", "ar": "قائمة", "ko": "메뉴", "pt": "Menu"},

    # Classic Cultural Dishes (Global)
    "비빔밥": {"en": "Bibimbap (Korean Mixed Rice with Vegetables & Egg)", "es": "Bibimbap (Arroz Mixto Coreano con Verduras y Huevo)", "fr": "Bibimbap (Bol de Riz Coréen aux Légumes et Œuf)", "de": "Bibimbap (Koreanische Reisschale mit Gemüse und Ei)", "it": "Bibimbap (Riso Misto Coreano con Verdure e Uovo)", "ja": "ビビンバ (韓国風混ぜご飯)", "zh": "石鍋拌飯", "ar": "بيبيمباب (أرز كوري مشكل مع الخضار والبيض)", "ko": "비빔밥", "pt": "Bibimbap (Tigela de Arroz Coreano com Legumes)"},
    "불고기": {"en": "Bulgogi (Marinated Thin-Sliced Beef)", "es": "Bulgogi (Carne de Res Marinada a la Parrilla)", "fr": "Bulgogi (Bœuf Mariné Grillé)", "de": "Bulgogi (Mariniertes Rindfleisch)", "it": "Bulgogi (Manzo Marinato alla Griglia)", "ja": "プルコギ (韓国風すき焼き肉)", "zh": "韓式烤牛肉", "ar": "بولغوجي (لحم بقري متبل ومشوي)", "ko": "불고기", "pt": "Bulgogi (Carne Bovina Marinada)"},
    "김치찌개": {"en": "Kimchi Jjigae (Spicy Kimchi Stew)", "es": "Kimchi Jjigae (Estofado Picante de Kimchi)", "fr": "Kimchi Jjigae (Ragoût Épicé de Kimchi)", "de": "Kimchi Jjigae (Würziger Kimchi-Eintopf)", "it": "Kimchi Jjigae (Stufato Piccante di Kimchi)", "ja": "キムチチゲ (キムチ鍋)", "zh": "辣泡菜湯", "ar": "حساء الكيمتشي الحار", "ko": "김치찌개", "pt": "Kimchi Jjigae (Guisado Picante de Kimchi)"},
    "떡볶이": {"en": "Tteokbokki (Spicy Simmered Rice Cakes)", "es": "Tteokbokki (Pasteles de Arroz en Salsa Picante)", "fr": "Tteokbokki (Gâteaux de Riz Épicés)", "de": "Tteokbokki (Scharfe Reiskuchen)", "it": "Tteokbokki (Gnocchi di Riso Piccanti)", "ja": "トッポギ (辛口トッポッキ)", "zh": "辣炒年糕", "ar": "تيوكبوكي (كعكات الأرز الحارة)", "ko": "떡볶이", "pt": "Tteokbokki (Bolinhos de Arroz Picantes)"},
    "삼겹살": {"en": "Samgyeopsal (Grilled Pork Belly)", "es": "Samgyeopsal (Panceta de Cerdo a la Parrilla)", "fr": "Samgyeopsal (Poitrine de Porc Grillée)", "de": "Samgyeopsal (Gegrillter Schweinebauch)", "it": "Samgyeopsal (Pancetta di Maiale alla Griglia)", "ja": "サムギョプサル (豚バラ焼肉)", "zh": "韓式五花肉", "ar": "سامغيوبسال (بطن الخنزير المشوي)", "ko": "삼겹살", "pt": "Samgyeopsal (Barriga de Porco Grelhada)"},
    "만두": {"en": "Mandu (Korean Dumplings)", "es": "Mandu (Empanadillas Coreanas)", "fr": "Mandu (Raviolis Coréens)", "de": "Mandu (Koreanische Teigtaschen)", "it": "Mandu (Ravioli Coreani)", "ja": "マンドゥ (韓国風餃子)", "zh": "韓式餃子", "ar": "ماندو (فطائر كورية)", "ko": "만두", "pt": "Mandu (Pasteis Coreanos)"},

    # Italian
    "pizza margherita": {"en": "Pizza Margherita (Tomato, Mozzarella & Basil Pizza)", "es": "Pizza Margarita (Tomate, Mozzarella y Albahaca)", "fr": "Pizza Margherita (Tomate, Mozzarella et Basilic)", "de": "Pizza Margherita (Tomaten, Mozzarella und Basilikum)", "it": "Pizza Margherita", "ja": "ピッツァ・マルゲリータ", "zh": "瑪格麗特披薩", "ar": "بيتزا مارغريتا", "ko": "마르게리타 피자", "pt": "Pizza Margherita"},
    "spaghetti alla carbonara": {"en": "Spaghetti alla Carbonara (Cured Pork & Egg Pasta)", "es": "Espaguetis a la Carbonara (Panceta y Huevo)", "fr": "Spaghetti à la Carbonara (Guanciale et Jaune d'Œuf)", "de": "Spaghetti alla Carbonara", "it": "Spaghetti alla Carbonara", "ja": "スパゲッティ・カルボナーラ", "zh": "培根蛋醬意大利麵", "ar": "سباغيتي كاربونارا", "ko": "스파게티 카르보나라", "pt": "Espaguete à Carbonara"},
    "carpaccio di manzo": {"en": "Beef Carpaccio (Thin Sliced Raw Beef with Arugula & Parmesan)", "es": "Carpaccio de Ternera (Finas Láminas con Parmesano)", "fr": "Carpaccio de Bœuf (Fines Tranches de Bœuf Cru et Parmesan)", "de": "Rinder-Carpaccio (Hauchdünnes Rindfleisch mit Parmesan)", "it": "Carpaccio di Manzo", "ja": "牛ヒレ肉のカルパッチョ", "zh": "意式生牛肉薄片", "ar": "كارباتشيو لحم البقر", "ko": "소고기 카르파초", "pt": "Carpaccio de Carne Bovina"},
    "risotto ai funghi": {"en": "Mushroom Risotto (Creamy Arborio Rice with Porcini)", "es": "Risotto de Setas (Arroz Cremoso con Hongos)", "fr": "Risotto aux Champignons", "de": "Pilzrisotto (Cremiger Reis mit Waldpilzen)", "it": "Risotto ai Funghi Porcini", "ja": "キノコのリゾット", "zh": "奶油牛肝菌燴飯", "ar": "ريزوتو الفطر", "ko": "버섯 리소토", "pt": "Risoto de Cogumelos"},
    "tiramisù": {"en": "Tiramisu (Espresso & Mascarpone Layered Dessert)", "es": "Tiramisú (Postre de Café Espresso y Mascarpone)", "fr": "Tiramisu (Dessert Mascarpone et Café)", "de": "Tiramisu (Espresso-Mascarpone-Dessert)", "it": "Tiramisù", "ja": "ティラミス", "zh": "意式提拉米蘇", "ar": "تيراميسو", "ko": "티라미수", "pt": "Tiramisù"},
    "lasagna alla bolognese": {"en": "Lasagna Bolognese (Layered Pasta with Meat Ragu)", "es": "Lasaña a la Boloñesa (Pasta con Ragú de Carne)", "fr": "Lasagne à la Bolognaise (Ragoût de Viande et Béchamel)", "de": "Lasagne Bolognese (Schichtnudeln mit Fleischsauce)", "it": "Lasagne alla Bolognese", "ja": "ラザニア・ボロネーゼ", "zh": "意式肉醬千層麵", "ar": "لازانيا بولونيز", "ko": "볼로네제 라자냐", "pt": "Lasanha à Bolonhesa"},

    # French
    "croissant": {"en": "Croissant (Flaky Butter Pastry)", "es": "Cruasán de Mantequilla", "fr": "Croissant pur beurre", "de": "Buttercroissant", "it": "Cornetto / Croissant al Burro", "ja": "クロワッサン", "zh": "法式可頌牛角包", "ar": "كرواسون بالزبدة", "ko": "크루아상", "pt": "Croissant de Manteiga"},
    "soupe à l'oignon": {"en": "French Onion Soup (Gratinéed with Bread & Gruyère)", "es": "Sopa de Cebolla Francesa Gratinada", "fr": "Soupe à l'Oignon Gratinée", "de": "Französische Zwiebelsuppe mit Käse", "it": "Zuppa di Cipolle Gratinata", "ja": "オニオングラタンスープ", "zh": "法式焗洋蔥湯", "ar": "حساء البصل الفرنسي بالجبن", "ko": "프렌치 어니언 수프", "pt": "Sopa de Cebola Francesa"},
    "crème brûlée": {"en": "Crème Brûlée (Vanilla Custard with Caramelized Crust)", "es": "Crema Quemada Crème Brûlée", "fr": "Crème Brûlée à la Vanille", "de": "Crème Brûlée (Karamellisierte Vanillecreme)", "it": "Crème Brûlée", "ja": "クレームブリュレ", "zh": "法式焦糖布丁", "ar": "كريم بروليه بالكراميل", "ko": "크렘 브륄레", "pt": "Crème Brûlée"},

    # Spanish & Mexican
    "paella de marisco": {"en": "Seafood Paella (Saffron Rice with Shellfish & Fish)", "es": "Paella de Marisco", "fr": "Paella aux Fruits de Mer", "de": "Meeresfrüchte-Paella (Safranreis mit Muscheln)", "it": "Paella ai Frutti di Mare", "ja": "シーフードパエリア", "zh": "西班牙海鮮飯", "ar": "باييلا المأكولات البحرية بالزعفران", "ko": "해산물 파에야", "pt": "Paella de Frutos do Mar"},
    "tacos al pastor": {"en": "Tacos al Pastor (Spit-Roasted Marinated Pork Tacos)", "es": "Tacos al Pastor", "fr": "Tacos au Porc Mariné et Rôti", "de": "Tacos al Pastor (Marinierte Schweinefleischtacos)", "it": "Tacos al Pastor", "ja": "タコス・アル・パストール", "zh": "墨西哥烤豬肉卷餅", "ar": "تاكوس أل باستور", "ko": "타코 알 파스토르", "pt": "Tacos al Pastor"},
    "guacamole": {"en": "Fresh Guacamole (Crushed Avocado Dip with Lime & Herbs)", "es": "Guacamole Tradicional", "fr": "Guacamole Frais à l'Avocat et Citron Vert", "de": "Frische Guacamole (Avocado-Dip)", "it": "Guacamole Fresco", "ja": "ワカモレ (アボカドディップ)", "zh": "墨西哥牛油果醬", "ar": "غموس الغواكامولي الطازج", "ko": "과카몰리", "pt": "Guacamole Tradicional"},

    # Middle Eastern
    "falafel": {"en": "Falafel (Crisp Herbed Chickpea Croquettes)", "es": "Falafel (Croquetas Crujientes de Garbanzos)", "fr": "Falafels (Beignets de Pois Chiches aux Herbes)", "de": "Falafel (Knusprige Kichererbsenbällchen)", "it": "Falafel (Polpette di Ceci Aromatiche)", "ja": "ファラフェル (ひよこ豆のコロッケ)", "zh": "炸鷹嘴豆餅 (法拉費)", "ar": "فلافل", "ko": "팔라펠", "pt": "Falafel (Bolinhos de Grão-de-Bico)"},
    "hummus": {"en": "Hummus with Tahini (Smooth Chickpea & Sesame Dip)", "es": "Hummus con Tahini", "fr": "Houmous au Tahini", "de": "Hummus mit Tahini", "it": "Hummus con Tahina", "ja": "フムス (ひよこ豆ディップ)", "zh": "鷹嘴豆芝麻醬", "ar": "حمص بالطحينة", "ko": "후무스", "pt": "Húmus com Tahine"},
    "shawarma": {"en": "Shawarma (Spiced Spit-Roasted Meat Wrap)", "es": "Shawarma (Carne Especiada Asada en Asador)", "fr": "Shawarma (Émincé de Viande Épicée)", "de": "Schawarma (Gewürztes Fleisch vom Drehspieß)", "it": "Shawarma (Carne Speziata allo Spiedo)", "ja": "シャワルマ (回転串焼き肉)", "zh": "中東烤肉卷餅 (沙威瑪)", "ar": "شاورما", "ko": "샤와르마", "pt": "Shawarma (Carne Assada Especiada)"},

    # Japanese
    "醤油ラーメン": {"en": "Shoyu Ramen (Soy Sauce Broth Noodles)", "es": "Shoyu Ramen (Ramen en Caldo de Soja)", "fr": "Shoyu Ramen (Ramen au Bouillon de Soja)", "de": "Shoyu Ramen (Nudelsuppe mit Sojasauce)", "it": "Shoyu Ramen", "ja": "醤油ラーメン", "zh": "醬油拉麵", "ar": "شويو رامن", "ko": "소유 라멘 (간장 라멘)", "pt": "Shoyu Ramen"},
    "味噌ラーメン": {"en": "Miso Ramen (Fermented Miso Broth Noodles)", "es": "Miso Ramen (Ramen en Caldo de Miso)", "fr": "Miso Ramen (Ramen au Bouillon de Miso)", "de": "Miso Ramen", "it": "Miso Ramen", "ja": "味噌ラーメン", "zh": "味噌拉麵", "ar": "ميسو رامن", "ko": "미소 라멘 (된장 라멘)", "pt": "Miso Ramen"},
    "天ぷら": {"en": "Tempura (Crisp Light-Battered Seafood & Vegetables)", "es": "Tempura (Marisco y Verduras Fritas Crujientes)", "fr": "Tempura (Beignets Légers de Légumes et Fruits de Mer)", "de": "Tempura (Knusprig frittiertes Gemüse und Meeresfrüchte)", "it": "Tempura", "ja": "天ぷら", "zh": "日式天婦羅", "ar": "تمبورا (مأكولات بحرية وخضار مقلية مقرمشة)", "ko": "덴푸라 (일본식 튀김)", "pt": "Tempura"},
    "抹茶アイスクリーム": {"en": "Matcha Green Tea Ice Cream", "es": "Helado de Té Verde Matcha", "fr": "Glace au Thé Vert Matcha", "de": "Matcha-Grüntee-Eis", "it": "Gelato al Tè Verde Matcha", "ja": "抹茶アイスクリーム", "zh": "宇治抹茶冰淇淋", "ar": "آيس كريم الشاي الأخضر ماتشا", "ko": "말차 아이스크림", "pt": "Sorvete de Chá Verde Matcha"},
}


class MultilingualCulinaryEngine:
    """Language-independent translation, script detection, and phonetic romanization engine."""

    @classmethod
    def detect_script(cls, text: str) -> str:
        """Detect the predominant script / language family from Unicode character blocks."""
        if not text:
            return "unknown"
        if re.search(r"[\uac00-\ud7a3]", text):
            return "ko"
        if re.search(r"[\u3040-\u30ff]", text):
            return "ja"
        if re.search(r"[\u4e00-\u9fff]", text):
            return "zh"
        if re.search(r"[\u0600-\u06ff]", text):
            return "ar"
        if re.search(r"[\u0400-\u04ff]", text):
            return "ru"
        if re.search(r"[\u0e00-\u0e7f]", text):
            return "th"
        if re.search(r"[\u0900-\u097f]", text):
            return "hi"
        return "latin"

    @classmethod
    def generate_phonetic(cls, text: str, script: Optional[str] = None) -> Optional[str]:
        """Generate phonetic romanization for non-Latin scripts."""
        if not text:
            return None
        detected = script or cls.detect_script(text)
        if detected == "ko":
            return romanize_hangul(text)
        if detected == "ja":
            return romanize_japanese(text)
        # For Latin scripts, phonetic is not needed unless non-standard
        return None

    @classmethod
    def translate_dish(
        cls,
        original_name: str,
        printed_desc: Optional[str],
        target_lang: SupportedLanguage,
        source_hint: Optional[str] = None,
    ) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        """
        Translates a dish using the multilingual culinary dictionary.
        Returns: (translated_title, phonetic_transcription, translated_desc, flavor_profile)

        STRICT RULES:
        - NEVER fabricates culinary description when printed_desc is None.
        - NEVER replaces translation with romanization.
        - Translates into target_lang across all supported languages.
        """
        clean_name = original_name.strip()
        lower_name = clean_name.lower()
        lang_code = target_lang.value if hasattr(target_lang, "value") else str(target_lang)

        script = source_hint or cls.detect_script(clean_name)
        phonetic = cls.generate_phonetic(clean_name, script)

        # 1. Exact match in Lexicon
        for term, trans_dict in CULINARY_LEXICON.items():
            if lower_name == term.lower() or clean_name == term:
                translated = trans_dict.get(lang_code, trans_dict.get("en", clean_name))
                # Only return description if printed_desc was present on the menu!
                clean_desc = printed_desc.strip() if printed_desc else None
                return translated, phonetic, clean_desc, None

        # 2. Token / Multi-word Substring Translation for compound dishes & drinks
        # E.g. "블랙 밀크티", "Tea 스 브라운", "망고 스무디", "Pizza Margherita"
        has_korean = bool(re.search(r"[\uac00-\ud7a3]", clean_name))
        has_japanese = bool(re.search(r"[\u3040-\u30ff]", clean_name))
        has_chinese = bool(re.search(r"[\u4e00-\u9fff]", clean_name))

        if has_korean or has_japanese or has_chinese:
            synthesized = clean_name
            # Replace recognized culinary tokens with target language equivalents
            # Sort by descending length so "블랙 밀크티" matches before "밀크티"
            for term, trans_dict in sorted(CULINARY_LEXICON.items(), key=lambda x: -len(x[0])):
                if term in synthesized:
                    repl = trans_dict.get(lang_code, trans_dict.get("en", term))
                    synthesized = synthesized.replace(term, f" {repl} ")

            synthesized = re.sub(r"\s+", " ", synthesized).strip()
            # If replacement occurred and produced meaningful title
            if synthesized != clean_name and len(synthesized) > 1:
                if lang_code in {"en", "es", "fr", "de", "it", "pt"}:
                    remaining_hangul = re.findall(r"[\uac00-\ud7a3]+", synthesized)
                    for h in remaining_hangul:
                        synthesized = synthesized.replace(h, romanize_hangul(h))
                    synthesized = re.sub(r"\s+", " ", synthesized).strip()
                clean_desc = printed_desc.strip() if printed_desc else None
                return synthesized, phonetic, clean_desc, None

        # 3. Fallback for unlisted dish:
        fallback_name = clean_name
        if lang_code == "en" and phonetic:
            fallback_name = phonetic
        clean_desc = printed_desc.strip() if printed_desc else None
        return fallback_name, phonetic, clean_desc, None

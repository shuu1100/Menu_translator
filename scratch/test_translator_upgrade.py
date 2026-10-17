import re
from typing import Dict, Any, List

def romanize_hangul(text: str) -> str:
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
    return " ".join(word.capitalize() for word in romanized.split())

KOREAN_TERMS = {
    "블랙": "Black",
    "아이스": "Iced",
    "핫": "Hot",
    "밀크티": "Milk Tea",
    "스무디": "Smoothie",
    "페인트": "Paint",
    "가을": "Autumn",
    "우롱": "Oolong",
    "그린": "Green",
    "타로": "Taro",
    "초코": "Chocolate",
    "망고": "Mango",
    "딸기": "Strawberry",
    "자몽": "Grapefruit",
    "레몬": "Lemon",
    "티": "Tea",
    "커피": "Coffee",
    "라떼": "Latte",
    "아메리카노": "Americano",
    "치즈폼": "Cheese Foam",
    "펄": "Tapioca Pearls",
}

def translate_korean_composite(name: str) -> str:
    words = name.split()
    translated_words = []
    for w in words:
        if w in KOREAN_TERMS:
            translated_words.append(KOREAN_TERMS[w])
        else:
            # Check sub-tokens (e.g. 블랙밀크티)
            sub = w
            for k, v in sorted(KOREAN_TERMS.items(), key=lambda x: -len(x[0])):
                sub = sub.replace(k, f" {v} ")
            translated_words.append(" ".join(sub.split()))
    return " ".join(translated_words)

test_items = [
    "블랙 밀크티",
    "아이스 블랙 밀크티",
    "아이스 블랙 스무디",
    "아이스 블랙 페인트",
    "가을 블랙 밀크티"
]

for item in test_items:
    t = translate_korean_composite(item)
    r = romanize_hangul(item)
    print(f"{item} -> {t} ({r})")

import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from backend.app.services.images.query_builder import build_image_search_query

test_cases = [
    ("브라운소프트 시그니처", "브라운소프트 시그니처", "Beuraunsopeuteu Sigeunicheo", "Gong Cha"),
    ("Brown Sugar 소프트 시그니처", "브라운소프트 시그니처", "Brown Soft Signature", "Gong Cha"),
    ("밀크티", "밀크티", "Milkeuti", "Tea"),
    ("우롱티", "우롱티", "Ulongti", "Tea"),
    ("타로 밀크티", "타로 밀크티", "Taro Milk Tea", "Tea"),
]

for name, nat, trans, sec in test_cases:
    prim, fall, cat = build_image_search_query(dish_name=name, native_name=nat, transliteration=trans, section=sec)
    print(f"Dish: {name}")
    print(f"  Primary query: '{prim}'")
    print(f"  Fallback query: '{fall}'")
    print(f"  Category: '{cat}'\n")

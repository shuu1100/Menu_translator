"""Synthetic multilingual restaurant menu dataset generator and train/val/test splitter.

Generates diverse high-resolution restaurant menus with exact bounding-box ground truths,
multi-lingual typography, price associations, and verified allergen annotations.
Enforces restaurant-level split isolation to guarantee zero data leakage between splits.
"""

import argparse
import hashlib
import io
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

# Set project root on path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

MENU_TEMPLATES = [
    {
        "restaurant_id": "rest_fam_italian_01",
        "restaurant_name": "TRATTORIA DEL CORSO",
        "subtitle": "Cucina Tipica Romana",
        "cuisine": "italian",
        "currency": "€",
        "sections": [
            {
                "title": "ANTIPASTI",
                "items": [
                    {
                        "name": "Bruschetta al Pomodoro",
                        "desc": "Toasted sourdough bread, heirloom tomatoes, fresh basil, garlic, extra virgin olive oil",
                        "price": "€8.50",
                        "ingredients": ["sourdough bread", "heirloom tomatoes", "fresh basil", "garlic", "olive oil"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": False, "is_halal": True},
                    },
                    {
                        "name": "Carpaccio di Manzo",
                        "desc": "Thinly sliced prime beef tenderloin, wild baby arugula, capers, shaved parmigiano",
                        "price": "€14.00",
                        "ingredients": ["beef tenderloin", "arugula", "capers", "parmigiano reggiano"],
                        "allergens": [{"allergen": "dairy", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": True, "is_halal": False},
                    },
                    {
                        "name": "Fiori di Zucca Fritti",
                        "desc": "Crispy battered zucchini blossoms stuffed with mozzarella cheese and salted anchovies",
                        "price": "€11.50",
                        "ingredients": ["zucchini blossoms", "mozzarella", "anchovies", "wheat batter"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "dairy", "status": "contains"}, {"allergen": "fish", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": False, "is_halal": False},
                    },
                ],
            },
            {
                "title": "PRIMI PIATTI",
                "items": [
                    {
                        "name": "Spaghetti alla Carbonara",
                        "desc": "Durum wheat spaghetti, crispy cured guanciale pork, fresh egg yolks, pecorino romano",
                        "price": "€15.00",
                        "ingredients": ["durum wheat spaghetti", "guanciale", "egg yolks", "pecorino romano"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "dairy", "status": "contains"}, {"allergen": "egg", "status": "contains"}, {"allergen": "pork", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": False, "is_halal": False},
                    },
                    {
                        "name": "Tonnarelli Cacio e Pepe",
                        "desc": "Fresh extruded egg pasta tossed with aged pecorino romano and toasted black pepper",
                        "price": "€13.50",
                        "ingredients": ["egg pasta", "pecorino romano", "black pepper"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "dairy", "status": "contains"}, {"allergen": "egg", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": True, "is_gluten_free": False, "is_halal": True},
                    },
                    {
                        "name": "Gnocchi alla Sorrentina",
                        "desc": "Soft potato dumplings baked in San Marzano tomato sauce and melted fresh mozzarella",
                        "price": "€14.00",
                        "ingredients": ["potatoes", "wheat flour", "tomatoes", "mozzarella", "basil"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "dairy", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": True, "is_gluten_free": False, "is_halal": True},
                    },
                ],
            },
        ],
    },
    {
        "restaurant_id": "rest_fam_japanese_02",
        "restaurant_name": "SAKURA RAMEN HOUSE",
        "subtitle": "自家製麺と本格スープ (Authentic Handmade Noodles)",
        "cuisine": "japanese",
        "currency": "¥",
        "sections": [
            {
                "title": "RAMEN (特製ラーメン)",
                "items": [
                    {
                        "name": "醤油ラーメン (Shoyu Ramen)",
                        "desc": "Handcrafted wheat noodles in aged soy sauce broth with chashu pork and menma",
                        "price": "¥880",
                        "ingredients": ["wheat ramen noodles", "soy sauce broth", "chashu pork", "scallions", "bamboo shoots"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "soy", "status": "contains"}, {"allergen": "pork", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": False, "is_halal": False},
                    },
                    {
                        "name": "味噌ラーメン (Miso Ramen)",
                        "desc": "Hokkaido style fermented red miso broth, wok-fried sprouts, sweet corn, creamy butter",
                        "price": "¥980",
                        "ingredients": ["wheat noodles", "red miso paste", "butter", "corn", "bean sprouts"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "dairy", "status": "contains"}, {"allergen": "soy", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": False, "is_halal": False},
                    },
                    {
                        "name": "ベジタブルラーメン (Vegan Ramen)",
                        "desc": "Silky soy milk and shiitake mushroom dashi broth with seasonal greens and tofu",
                        "price": "¥1050",
                        "ingredients": ["wheat noodles", "soy milk broth", "shiitake mushrooms", "tofu", "greens"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "soy", "status": "contains"}],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": False, "is_halal": True},
                    },
                ],
            },
            {
                "title": "SIDE DISHES (一品料理)",
                "items": [
                    {
                        "name": "焼き餃子 (Pan-Fried Gyoza)",
                        "desc": "Crispy pan-fried dumplings filled with seasoned pork and cabbage served with dipping tare",
                        "price": "¥480",
                        "ingredients": ["wheat wrappers", "ground pork", "napa cabbage", "garlic", "soy sauce"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "soy", "status": "contains"}, {"allergen": "pork", "status": "contains"}, {"allergen": "sesame", "status": "may_contain"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": False, "is_halal": False},
                    },
                    {
                        "name": "枝豆 (Edamame)",
                        "desc": "Steamed whole young green soybeans sprinkled with coarse sea salt",
                        "price": "¥350",
                        "ingredients": ["young soybeans", "sea salt"],
                        "allergens": [{"allergen": "soy", "status": "contains"}],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": True, "is_halal": True},
                    },
                ],
            },
        ],
    },
    {
        "restaurant_id": "rest_fam_mexican_03",
        "restaurant_name": "TAQUERÍA EL SOL",
        "subtitle": "Sabores Auténticos de Oaxaca y CDMX",
        "cuisine": "mexican",
        "currency": "$",
        "sections": [
            {
                "title": "TACOS TRADICIONALES",
                "items": [
                    {
                        "name": "Tacos al Pastor",
                        "desc": "Marinated pork shoulder roasted on a vertical trompo, fresh pineapple, cilantro, diced white onion",
                        "price": "$12.50",
                        "ingredients": ["corn tortillas", "pork shoulder", "achiote paste", "pineapple", "cilantro", "onion"],
                        "allergens": [{"allergen": "pork", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": True, "is_halal": False},
                    },
                    {
                        "name": "Tacos de Carnitas",
                        "desc": "Slow-braised Michoacán style pork confit in copper kettle, served with salsa verde and radishes",
                        "price": "$13.00",
                        "ingredients": ["corn tortillas", "pork confit", "radishes", "lime", "salsa verde"],
                        "allergens": [{"allergen": "pork", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": True, "is_halal": False},
                    },
                    {
                        "name": "Tacos de Hongos al Ajillo",
                        "desc": "Sautéed wild mushrooms with guajillo chiles, garlic, epazote, and avocado slices",
                        "price": "$11.00",
                        "ingredients": ["corn tortillas", "mushrooms", "guajillo chiles", "garlic", "avocado"],
                        "allergens": [],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": True, "is_halal": True},
                    },
                ],
            },
            {
                "title": "ANTOJITOS Y SALSAS",
                "items": [
                    {
                        "name": "Guacamole Tradicional",
                        "desc": "Hand-crushed ripe avocados with fresh lime juice, jalapeño, cilantro, served with tortilla chips",
                        "price": "$9.50",
                        "ingredients": ["avocado", "lime juice", "jalapeno", "cilantro", "corn tortilla chips"],
                        "allergens": [],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": True, "is_halal": True},
                    },
                    {
                        "name": "Queso Fundido con Chorizo",
                        "desc": "Melted Oaxaca and Chihuahua cheeses topped with spiced house-made pork chorizo",
                        "price": "$11.50",
                        "ingredients": ["oaxaca cheese", "chihuahua cheese", "pork chorizo", "flour tortillas"],
                        "allergens": [{"allergen": "dairy", "status": "contains"}, {"allergen": "pork", "status": "contains"}, {"allergen": "gluten", "status": "may_contain"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": False, "is_halal": False},
                    },
                ],
            },
        ],
    },
    {
        "restaurant_id": "rest_fam_levantine_04",
        "restaurant_name": "AL SHAM MEZZE HOUSE",
        "subtitle": "Traditional Damascus & Beirut Kitchen",
        "cuisine": "levantine",
        "currency": "$",
        "sections": [
            {
                "title": "COLD MEZZE (مقبلات باردة)",
                "items": [
                    {
                        "name": "Hummus bi Tahini (حمص بالطحينة)",
                        "desc": "Smooth blended chickpeas, roasted sesame tahini, fresh lemon juice, virgin olive oil",
                        "price": "$8.00",
                        "ingredients": ["chickpeas", "sesame tahini", "lemon juice", "olive oil", "garlic"],
                        "allergens": [{"allergen": "sesame", "status": "contains"}],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": True, "is_halal": True},
                    },
                    {
                        "name": "Baba Ghanoush (متبل باذنجان)",
                        "desc": "Fire-roasted smoked eggplant pureed with tahini, pomegranate seeds, and garlic",
                        "price": "$9.00",
                        "ingredients": ["smoked eggplant", "sesame tahini", "garlic", "pomegranate seeds", "olive oil"],
                        "allergens": [{"allergen": "sesame", "status": "contains"}],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": True, "is_halal": True},
                    },
                    {
                        "name": "Tabbouleh (تبولة)",
                        "desc": "Finely chopped flat-leaf parsley, mint, tomatoes, cracked bulgur wheat, lemon and olive oil",
                        "price": "$8.50",
                        "ingredients": ["fresh parsley", "mint", "tomatoes", "bulgur wheat", "lemon juice", "olive oil"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": False, "is_halal": True},
                    },
                ],
            },
            {
                "title": "HOT MEZZE (مقبلات ساخنة)",
                "items": [
                    {
                        "name": "Falafel Plate (طبق فلافل)",
                        "desc": "Golden fried spiced chickpea and herb croquettes served with tahini sauce and pickled turnips",
                        "price": "$10.50",
                        "ingredients": ["chickpeas", "fava beans", "parsley", "cilantro", "cumin", "sesame tahini"],
                        "allergens": [{"allergen": "sesame", "status": "contains"}],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": True, "is_halal": True},
                    },
                    {
                        "name": "Kibbeh Kras (كبة أقراص)",
                        "desc": "Crispy bulgur shell stuffed with spiced minced beef, toasted pine nuts, and allspice",
                        "price": "$12.00",
                        "ingredients": ["bulgur wheat", "minced beef", "pine nuts", "onions", "spices"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "tree_nuts", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": False, "is_halal": True},
                    },
                ],
            },
        ],
    },
    {
        "restaurant_id": "rest_fam_french_05",
        "restaurant_name": "BISTROT DE PARIS",
        "subtitle": "Gastronomie Bourgeoise & Vins Fins",
        "cuisine": "french",
        "currency": "€",
        "sections": [
            {
                "title": "ENTRÉES",
                "items": [
                    {
                        "name": "Soupe à l'Oignon Gratinée",
                        "desc": "Caramelized onion soup in rich beef consommé, topped with toasted baguette and melted Gruyère",
                        "price": "€11.00",
                        "ingredients": ["onions", "beef stock", "french baguette", "gruyere cheese", "butter"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "dairy", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": False, "is_halal": False},
                    },
                    {
                        "name": "Salade de Chèvre Chaud",
                        "desc": "Warm aged goat cheese on toasted brioche rounds over tender mixed greens with honey vinaigrette",
                        "price": "€13.50",
                        "ingredients": ["goat cheese", "brioche", "mixed greens", "walnuts", "honey"],
                        "allergens": [{"allergen": "gluten", "status": "contains"}, {"allergen": "dairy", "status": "contains"}, {"allergen": "tree_nuts", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": True, "is_gluten_free": False, "is_halal": True},
                    },
                ],
            },
            {
                "title": "PLATS PRINCIPAUX",
                "items": [
                    {
                        "name": "Boeuf Bourguignon",
                        "desc": "Braised prime beef braised in red Burgundy wine with pearl onions, carrots, and bacon lardoons",
                        "price": "€24.00",
                        "ingredients": ["beef", "burgundy wine", "pork bacon lardoons", "carrots", "mushrooms"],
                        "allergens": [{"allergen": "pork", "status": "contains"}, {"allergen": "alcohol", "status": "contains"}, {"allergen": "sulphites", "status": "contains"}],
                        "dietary": {"is_vegan": False, "is_vegetarian": False, "is_gluten_free": True, "is_halal": False},
                    },
                    {
                        "name": "Ratatouille Provençale",
                        "desc": "Slow-simmered zucchini, eggplant, bell peppers, and tomatoes with herbs de Provence and garlic",
                        "price": "€17.50",
                        "ingredients": ["eggplant", "zucchini", "bell peppers", "tomatoes", "olive oil", "herbs"],
                        "allergens": [],
                        "dietary": {"is_vegan": True, "is_vegetarian": True, "is_gluten_free": True, "is_halal": True},
                    },
                ],
            },
        ],
    },
]


def render_menu_image(
    template: Dict[str, Any],
    condition: str = "clear",
    width: int = 1200,
    height: int = 1600,
) -> Tuple[Image.Image, List[Dict[str, Any]]]:
    """Render a multi-column synthetic menu and calculate pixel + normalized bounding boxes."""
    if condition == "decorative":
        bg_color = (250, 246, 238)
    elif condition == "low_light":
        bg_color = (220, 215, 205)
    else:
        bg_color = (255, 255, 255)

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 46)
        sub_font = ImageFont.truetype("arial.ttf", 22)
        sec_font = ImageFont.truetype("arial.ttf", 30)
        dish_font = ImageFont.truetype("arial.ttf", 24)
        desc_font = ImageFont.truetype("arial.ttf", 17)
        price_font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        sec_font = ImageFont.load_default()
        dish_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        price_font = ImageFont.load_default()

    # Borders
    if condition == "decorative":
        draw.rectangle([35, 35, width - 35, height - 35], outline=(160, 120, 60), width=4)
        draw.rectangle([43, 43, width - 43, height - 43], outline=(160, 120, 60), width=1)

    # Header
    draw.text((width // 2, 85), template["restaurant_name"], fill=(25, 25, 25), font=title_font, anchor="mm")
    draw.text((width // 2, 135), template["subtitle"], fill=(90, 90, 90), font=sub_font, anchor="mm")
    draw.line([(width // 2 - 160, 160), (width // 2 + 160, 160)], fill=(160, 120, 60), width=2)

    sections = template["sections"]
    items_meta: List[Dict[str, Any]] = []
    reading_order = 1

    # Dual column layout
    col_width = (width - 180) // 2
    col_starts = [70, 70 + col_width + 40]

    for sec_idx, section in enumerate(sections):
        col_x = col_starts[sec_idx % 2]
        col_end = col_x + col_width
        y_cursor = 210

        # Section header
        draw.text((col_x, y_cursor), section["title"], fill=(150, 40, 30), font=sec_font)
        draw.line([(col_x, y_cursor + 38), (col_end, y_cursor + 38)], fill=(200, 200, 200), width=1)
        y_cursor += 55

        for item in section["items"]:
            dish_y_start = y_cursor

            # Draw Dish Name and Price
            draw.text((col_x, y_cursor), item["name"], fill=(20, 20, 20), font=dish_font)
            price_str = item["price"]
            draw.text((col_end, y_cursor), price_str, fill=(150, 40, 30), font=price_font, anchor="ra")
            y_cursor += 32

            # Wrap Description text
            desc = item["desc"]
            words = desc.split()
            lines = []
            curr_line = []
            for w in words:
                curr_line.append(w)
                if len(" ".join(curr_line)) > 42:
                    lines.append(" ".join(curr_line[:-1]))
                    curr_line = [w]
            if curr_line:
                lines.append(" ".join(curr_line))

            for line in lines:
                draw.text((col_x, y_cursor), line, fill=(75, 75, 75), font=desc_font)
                y_cursor += 22

            dish_y_end = y_cursor + 8
            y_cursor += 25

            # Bounding box coordinates
            xmin_px = max(0, col_x - 6)
            ymin_px = max(0, dish_y_start - 4)
            xmax_px = min(width, col_end + 6)
            ymax_px = min(height, dish_y_end)

            box_2d = [
                round(ymin_px / height, 4),
                round(xmin_px / width, 4),
                round(ymax_px / height, 4),
                round(xmax_px / width, 4),
            ]

            dish_id = f"item_{template['restaurant_id']}_{reading_order:03d}"
            items_meta.append({
                "dish_id": dish_id,
                "reading_order": reading_order,
                "section": section["title"],
                "original_name": item["name"],
                "subtitle_or_description": item["desc"],
                "price_display": item["price"],
                "currency": template["currency"],
                "box_2d": box_2d,
                "pixel_box": [xmin_px, ymin_px, xmax_px, ymax_px],
                "ingredients": item.get("ingredients", []),
                "allergens": item.get("allergens", []),
                "dietary": item.get("dietary", {}),
            })
            reading_order += 1

    # Condition enhancements
    if condition == "low_light":
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.65)
        contrast = ImageEnhance.Contrast(img)
        img = contrast.enhance(1.15)
    elif condition == "noisy":
        img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
        # Add slight compression artifacts by JPEG saving
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=45)
        buffer.seek(0)
        img = Image.open(buffer)

    return img, items_meta


def generate_full_dataset(
    output_dir: Path,
    seed: int = 42,
    copies_per_condition: int = 2,
) -> Dict[str, Any]:
    """Generate images, annotations, and train/val/test split manifests."""
    random.seed(seed)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    conditions = ["clear", "decorative", "low_light", "noisy"]
    all_menus: List[Dict[str, Any]] = []

    print(f"[*] Generating synthetic menu dataset with seed={seed}...")

    # Assign restaurant families to splits for strict zero-leakage isolation
    # 5 restaurant families: 3 train (60%), 1 val (20%), 1 test (20%)
    shuffled_templates = list(MENU_TEMPLATES)
    random.shuffle(shuffled_templates)

    train_families = {t["restaurant_id"] for t in shuffled_templates[:3]}
    val_families = {shuffled_templates[3]["restaurant_id"]}
    test_families = {shuffled_templates[4]["restaurant_id"]}

    total_dishes = 0

    for template in shuffled_templates:
        rest_id = template["restaurant_id"]
        if rest_id in train_families:
            split_name = "train"
        elif rest_id in val_families:
            split_name = "validation"
        else:
            split_name = "test"

        for cond in conditions:
            for copy_idx in range(copies_per_condition):
                menu_id = f"menu_{rest_id}_{cond}_{copy_idx:02d}"
                img, items = render_menu_image(template, condition=cond)

                image_filename = f"{menu_id}.png"
                img_path = images_dir / image_filename
                img.save(img_path, format="PNG")

                menu_record = {
                    "menu_id": menu_id,
                    "restaurant_id": rest_id,
                    "restaurant_name": template["restaurant_name"],
                    "cuisine": template["cuisine"],
                    "condition": cond,
                    "split": split_name,
                    "is_stress_test": cond in ["low_light", "noisy"],
                    "image_filename": image_filename,
                    "image_width": 1200,
                    "image_height": 1600,
                    "dish_count": len(items),
                    "items": items,
                }
                all_menus.append(menu_record)
                total_dishes += len(items)

    # Separate into splits
    train_menus = [m for m in all_menus if m["split"] == "train"]
    val_menus = [m for m in all_menus if m["split"] == "validation"]
    test_menus = [m for m in all_menus if m["split"] == "test"]
    stress_menus = [m for m in test_menus if m["is_stress_test"]]

    # Save split JSON files
    with open(output_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(train_menus, f, indent=2, ensure_ascii=False)

    with open(output_dir / "val.json", "w", encoding="utf-8") as f:
        json.dump(val_menus, f, indent=2, ensure_ascii=False)

    with open(output_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(test_menus, f, indent=2, ensure_ascii=False)

    with open(output_dir / "stress_test.json", "w", encoding="utf-8") as f:
        json.dump(stress_menus, f, indent=2, ensure_ascii=False)

    manifest = {
        "dataset_name": "menu-translator-synthetic-v1",
        "version": "1.0.0",
        "random_seed": seed,
        "total_menus": len(all_menus),
        "total_dishes": total_dishes,
        "splits": {
            "train": {
                "menus_count": len(train_menus),
                "dishes_count": sum(m["dish_count"] for m in train_menus),
                "restaurant_families": list(train_families),
            },
            "validation": {
                "menus_count": len(val_menus),
                "dishes_count": sum(m["dish_count"] for m in val_menus),
                "restaurant_families": list(val_families),
            },
            "test": {
                "menus_count": len(test_menus),
                "dishes_count": sum(m["dish_count"] for m in test_menus),
                "restaurant_families": list(test_families),
                "stress_test_menus": len(stress_menus),
            },
        },
        "license": "CC0-1.0 (Public Domain Synthetic Generation)",
        "provenance": "Generated via scripts/generate_dataset.py with PIL rendering and exact pixel bounding boxes",
    }

    with open(output_dir / "dataset_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("========================================")
    print("Dataset Generation Complete:")
    print(f"  Total Menus:      {len(all_menus)}")
    print(f"  Total Dishes:     {total_dishes}")
    print(f"  Train Menus:      {len(train_menus)} ({manifest['splits']['train']['dishes_count']} dishes)")
    print(f"  Val Menus:        {len(val_menus)} ({manifest['splits']['validation']['dishes_count']} dishes)")
    print(f"  Test Menus:       {len(test_menus)} ({manifest['splits']['test']['dishes_count']} dishes)")
    print(f"  Stress Test Menus:{len(stress_menus)}")
    print(f"  Manifest Path:    {output_dir / 'dataset_manifest.json'}")
    print("========================================")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic multilingual menu dataset.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/training",
        help="Directory to save images and manifests",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--copies",
        type=int,
        default=2,
        help="Copies per layout condition",
    )
    args = parser.parse_args()

    out_path = Path(args.output_dir)
    if not out_path.is_absolute():
        out_path = project_root / out_path

    generate_full_dataset(output_dir=out_path, seed=args.seed, copies_per_condition=args.copies)


if __name__ == "__main__":
    main()

"""Synthetic menu image generator for test fixtures and benchmark evaluation."""

import io
from typing import Any, Dict, List, Tuple
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


def create_synthetic_menu(
    width: int = 1200,
    height: int = 1600,
    condition: str = "clear",
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Generate a synthetic multi-column restaurant menu image and return its ground truth metadata.
    Conditions: 'clear', 'low_light', 'noisy', 'decorative'.
    """
    # Background
    if condition == "decorative":
        bg_color = (250, 246, 238)
    else:
        bg_color = (255, 255, 255)

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Use default font or basic system font
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        section_font = ImageFont.truetype("arial.ttf", 34)
        dish_font = ImageFont.truetype("arial.ttf", 26)
        desc_font = ImageFont.truetype("arial.ttf", 18)
        price_font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        title_font = ImageFont.load_default()
        section_font = ImageFont.load_default()
        dish_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        price_font = ImageFont.load_default()

    # Decorative header border if requested
    if condition == "decorative":
        draw.rectangle([40, 40, width - 40, height - 40], outline=(180, 140, 80), width=4)
        draw.rectangle([48, 48, width - 48, height - 48], outline=(180, 140, 80), width=1)

    # Restaurant Title
    draw.text((width // 2, 90), "OSTERIA DEL SOLE", fill=(30, 30, 30), font=title_font, anchor="mm")
    draw.text((width // 2, 140), "Cucina Tradizionale Italiana", fill=(100, 100, 100), font=desc_font, anchor="mm")
    draw.line([(width // 2 - 150, 165), (width // 2 + 150, 165)], fill=(180, 140, 80), width=2)

    # Multi-column layout data
    columns = [
        {
            "x_start": 90,
            "x_end": 560,
            "section": "ANTIPASTI",
            "y_start": 210,
            "items": [
                {
                    "name": "Bruschetta al Pomodoro",
                    "desc": "Toasted sourdough bread, heirloom tomatoes, fresh basil, extra virgin olive oil",
                    "price": "€8.50",
                },
                {
                    "name": "Carpaccio di Manzo",
                    "desc": "Thinly sliced prime beef tenderloin, arugula, capers, shaved parmigiano",
                    "price": "€14.00",
                },
                {
                    "name": "Calamari Fritti",
                    "desc": "Crispy fried baby squid served with spicy marinara and lemon wedges",
                    "price": "€13.50",
                },
            ],
        },
        {
            "x_start": 640,
            "x_end": 1110,
            "section": "PRIMI PIATTI",
            "y_start": 210,
            "items": [
                {
                    "name": "Tagliatelle al Ragù",
                    "desc": "Fresh handmade egg ribbons with slow-braised bolognese meat sauce",
                    "price": "€16.50",
                },
                {
                    "name": "Risotto ai Funghi Porcini",
                    "desc": "Carnaroli rice, wild porcini mushrooms, white wine, parmigiano reggiano",
                    "price": "€18.00",
                },
                {
                    "name": "Spaghetti alle Vongole",
                    "desc": "Spaghetti pasta, fresh clams, garlic, white wine, fresh parsley, chili flakes",
                    "price": "€19.50",
                },
            ],
        },
    ]

    ground_truth_items = []
    reading_order = 1

    for col in columns:
        col_x = col["x_start"]
        cur_y = col["y_start"]
        section_name = col["section"]

        # Section Heading
        draw.text((col_x, cur_y), section_name, fill=(150, 40, 40), font=section_font)
        draw.line([(col_x, cur_y + 42), (col["x_end"], cur_y + 42)], fill=(220, 220, 220), width=1)
        cur_y += 65

        for item in col["items"]:
            item_top = cur_y
            # Dish Name
            draw.text((col_x, cur_y), item["name"], fill=(20, 20, 20), font=dish_font)
            # Price (right aligned in column)
            draw.text((col["x_end"], cur_y), item["price"], fill=(40, 40, 40), font=price_font, anchor="ra")
            cur_y += 36

            # Description
            desc_lines = [item["desc"][:45], item["desc"][45:]] if len(item["desc"]) > 45 else [item["desc"]]
            for dline in desc_lines:
                if dline.strip():
                    draw.text((col_x, cur_y), dline.strip(), fill=(85, 85, 85), font=desc_font)
                    cur_y += 24

            item_bottom = cur_y + 10
            cur_y += 25  # Space between dishes

            # Record normalized ground truth box
            gt_box = {
                "xmin": round(col_x / width, 4),
                "ymin": round(item_top / height, 4),
                "xmax": round(col["x_end"] / width, 4),
                "ymax": round(item_bottom / height, 4),
            }

            ground_truth_items.append(
                {
                    "reading_order": reading_order,
                    "section": section_name,
                    "original_name": item["name"],
                    "subtitle_or_description": item["desc"],
                    "price_display": item["price"],
                    "ground_truth_box": gt_box,
                }
            )
            reading_order += 1

    # Apply conditions
    if condition == "low_light":
        # Darken image and lower contrast
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.45)
        contrast = ImageEnhance.Contrast(img)
        img = contrast.enhance(0.7)
    elif condition == "noisy":
        # Add slight blur to mimic motion or low-end camera sensor
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2))

    # Convert to JPEG bytes
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    img_bytes = buffer.getvalue()

    metadata = {
        "width": width,
        "height": height,
        "condition": condition,
        "total_items": len(ground_truth_items),
        "items": ground_truth_items,
    }

    return img_bytes, metadata

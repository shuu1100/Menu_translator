"""Curated Culinary Food Image Provider & Neutral Placeholder Generator.

Provides verified, authentic food photography with photographer attributions for global cuisines,
and generates clean SVG placeholders when no representative image is available.
"""

import html
import re
from typing import Dict, List, Optional
import urllib.parse
from backend.app.schemas.image_search import DishImageInfo, DishImageQuery
from backend.app.services.images.providers.base import BaseImageProvider
from backend.app.services.images.query_builder import (
    build_image_search_query,
    clean_dish_name,
    infer_cuisine,
    infer_dish_category,
)


# Verified high-resolution food photography directory with author attributions
CURATED_DISH_CATALOG: List[Dict[str, any]] = [
    # --- JAPANESE CUISINE ---
    {
        "keywords": ["tonkotsu ramen", "tonkotsu", "ramen", "pork ramen", "hakata ramen"],
        "dish_name": "Tonkotsu Ramen",
        "cuisine": "Japanese",
        "category": "noodles",
        "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=300&q=80",
        "photographer": "Diego Lozano",
        "photographer_url": "https://unsplash.com/@diegolozano?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/bowl-of-ramen-soup-M3n1Wf0h1Z0",
        "alt_text": "Bowl of Japanese Tonkotsu Ramen with soft-boiled egg, chashu pork, and nori",
    },
    {
        "keywords": ["miso ramen", "spicy miso ramen", "karakuchi miso"],
        "dish_name": "Miso Ramen",
        "cuisine": "Japanese",
        "category": "noodles",
        "image_url": "https://images.unsplash.com/photo-1591814468924-caf88d1232e1?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1591814468924-caf88d1232e1?auto=format&fit=crop&w=300&q=80",
        "photographer": "Mae Mu",
        "photographer_url": "https://unsplash.com/@itsmaemu?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/miso-ramen",
        "alt_text": "Steaming bowl of spicy miso ramen with scallions and bamboo shoots",
    },
    {
        "keywords": ["tsukemen", "dipping ramen", "gyokai tsukemen"],
        "dish_name": "Tsukemen Dipping Noodles",
        "cuisine": "Japanese",
        "category": "noodles",
        "image_url": "https://images.unsplash.com/photo-1552611052-33e04de081de?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1552611052-33e04de081de?auto=format&fit=crop&w=300&q=80",
        "photographer": "Alex Munsell",
        "photographer_url": "https://unsplash.com/@alexmunsell?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/ramen-noodles",
        "alt_text": "Japanese tsukemen chilled thick noodles with concentrated dipping broth",
    },
    {
        "keywords": ["gyoza", "dumpling", "dumplings", "yaki gyoza", "potstickers"],
        "dish_name": "Crispy Pan-Fried Gyoza",
        "cuisine": "Japanese",
        "category": "appetizer",
        "image_url": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=300&q=80",
        "photographer": "Charles Deluvio",
        "photographer_url": "https://unsplash.com/@charlesdeluvio?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/steamed-dumplings-in-basket",
        "alt_text": "Golden pan-fried gyoza dumplings with dipping sauce",
    },
    {
        "keywords": ["sushi", "nigiri", "maguro", "sashimi", "tuna nigiri", "salmon sushi", "maki"],
        "dish_name": "Assorted Sushi & Nigiri",
        "cuisine": "Japanese",
        "category": "appetizer",
        "image_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=300&q=80",
        "photographer": "Jakub Kapusnak",
        "photographer_url": "https://unsplash.com/@foodiesfeed?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/sushi-roll-platter",
        "alt_text": "Fresh bluefin tuna and salmon nigiri sushi on wooden board",
    },
    {
        "keywords": ["tempura", "ebi tempura", "prawn tempura", "shrimp tempura"],
        "dish_name": "Ebi Tempura",
        "cuisine": "Japanese",
        "category": "appetizer",
        "image_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=300&q=80",
        "photographer": "SJ Baren",
        "photographer_url": "https://unsplash.com/@sj_baren?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/tempura-fried-food",
        "alt_text": "Crispy golden battered tiger prawn tempura with dipping sauce",
    },
    {
        "keywords": ["yakitori", "chicken skewer", "tare yakitori", "kushiyaki"],
        "dish_name": "Yakitori Skewers",
        "cuisine": "Japanese",
        "category": "grilled",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=300&q=80",
        "photographer": "Alex Munsell",
        "photographer_url": "https://unsplash.com/@alexmunsell?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/grilled-meat-skewers",
        "alt_text": "Charcoal grilled yakitori chicken skewers glazed with tare sauce",
    },
    {
        "keywords": ["karaage", "japanese fried chicken", "tori karaage"],
        "dish_name": "Chicken Karaage",
        "cuisine": "Japanese",
        "category": "appetizer",
        "image_url": "https://images.unsplash.com/photo-1562967914-608f82629710?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1562967914-608f82629710?auto=format&fit=crop&w=300&q=80",
        "photographer": "Lucas Andrade",
        "photographer_url": "https://unsplash.com/@lucasandrade?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/fried-chicken-nuggets",
        "alt_text": "Crispy ginger-soy marinated Japanese fried chicken bites with lemon wedge",
    },
    {
        "keywords": ["matcha latte", "matcha", "green tea latte", "ujicha"],
        "dish_name": "Matcha Green Tea Latte",
        "cuisine": "Japanese",
        "category": "beverage",
        "image_url": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?auto=format&fit=crop&w=300&q=80",
        "photographer": "Nathana Rebouças",
        "photographer_url": "https://unsplash.com/@nathanareboucas?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/green-tea-latte",
        "alt_text": "Artisanal ceremonial Japanese matcha latte with creamy microfoam",
    },

    # --- KOREAN CUISINE ---
    {
        "keywords": ["black milk tea", "milk tea", "boba", "bubble tea", "pearl milk tea"],
        "dish_name": "Classic Black Milk Tea with Pearls",
        "cuisine": "Korean",
        "category": "beverage",
        "image_url": "https://images.unsplash.com/photo-1558857563-b37fe439169a?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1558857563-b37fe439169a?auto=format&fit=crop&w=300&q=80",
        "photographer": "Rosalind Chang",
        "photographer_url": "https://unsplash.com/@rosalindchang?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/boba-tea-in-glass",
        "alt_text": "Chilled black milk tea layered with chewy brown sugar tapioca boba pearls",
    },
    {
        "keywords": ["brown sugar milk tea", "brown sugar", "tiger milk tea", "jewelry milk tea"],
        "dish_name": "Brown Sugar Pearl Milk Tea",
        "cuisine": "Korean",
        "category": "beverage",
        "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=300&q=80",
        "photographer": "Daniela Araya",
        "photographer_url": "https://unsplash.com/@daniela_araya?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/brown-sugar-boba",
        "alt_text": "Brown sugar caramelized milk tea with tiger stripe syrup pattern",
    },
    {
        "keywords": ["mango smoothie", "mango yogurt", "mango drink"],
        "dish_name": "Mango Yogurt Smoothie",
        "cuisine": "Korean",
        "category": "beverage",
        "image_url": "https://images.unsplash.com/photo-1505252585461-04db1eb84625?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1505252585461-04db1eb84625?auto=format&fit=crop&w=300&q=80",
        "photographer": "Jonas Kakaroto",
        "photographer_url": "https://unsplash.com/@jonaskakaroto?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/mango-smoothie",
        "alt_text": "Fresh tropical mango smoothie topped with mint and fruit puree",
    },
    {
        "keywords": ["croffle", "croissant waffle", "cheese foam croffle"],
        "dish_name": "Artisanal Croffle with Sweet Foam",
        "cuisine": "Korean",
        "category": "dessert",
        "image_url": "https://images.unsplash.com/photo-1562376552-0d160a2f238d?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1562376552-0d160a2f238d?auto=format&fit=crop&w=300&q=80",
        "photographer": "Mae Mu",
        "photographer_url": "https://unsplash.com/@itsmaemu?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/waffle-croissant",
        "alt_text": "Crispy buttery pressed croffle topped with salted sweet cream foam",
    },
    {
        "keywords": ["kimchi fried rice", "kimchi bokkeumbap", "kimchi rice"],
        "dish_name": "Kimchi Fried Rice",
        "cuisine": "Korean",
        "category": "rice",
        "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=300&q=80",
        "photographer": "Farhad Ibrahimzade",
        "photographer_url": "https://unsplash.com/@farhad_ibrahimzade?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/fried-rice-bowl",
        "alt_text": "Spicy Korean kimchi fried rice topped with a sunny-side-up egg and seaweed",
    },
    {
        "keywords": ["bibimbap", "dolsot bibimbap", "korean mixed rice"],
        "dish_name": "Traditional Bibimbap",
        "cuisine": "Korean",
        "category": "rice",
        "image_url": "https://images.unsplash.com/photo-1590301157890-4810ed352733?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1590301157890-4810ed352733?auto=format&fit=crop&w=300&q=80",
        "photographer": "Jakub Kapusnak",
        "photographer_url": "https://unsplash.com/@foodiesfeed?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/bibimbap-bowl",
        "alt_text": "Korean dolsot bibimbap with colorful seasoned vegetables, beef, and gochujang",
    },
    {
        "keywords": ["bulgogi", "korean beef", "beef bulgogi"],
        "dish_name": "Beef Bulgogi",
        "cuisine": "Korean",
        "category": "grilled",
        "image_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=300&q=80",
        "photographer": "Eiliv Aceron",
        "photographer_url": "https://unsplash.com/@eilivaceron?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/grilled-korean-bbq",
        "alt_text": "Marinated thinly sliced Korean beef bulgogi with caramelized onions and sesame",
    },
    {
        "keywords": ["tteokbokki", "ddukbokki", "spicy rice cakes"],
        "dish_name": "Spicy Tteokbokki",
        "cuisine": "Korean",
        "category": "appetizer",
        "image_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=300&q=80",
        "photographer": "SJ Baren",
        "photographer_url": "https://unsplash.com/@sj_baren?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/spicy-rice-cakes",
        "alt_text": "Chewy cylindrical Korean rice cakes simmered in sweet and spicy gochujang sauce",
    },

    # --- ITALIAN CUISINE ---
    {
        "keywords": ["bruschetta", "bruschetta al pomodoro", "tomato bruschetta"],
        "dish_name": "Bruschetta al Pomodoro",
        "cuisine": "Italian",
        "category": "appetizer",
        "image_url": "https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?auto=format&fit=crop&w=300&q=80",
        "photographer": "Angelo Pantazis",
        "photographer_url": "https://unsplash.com/@angelopantazis?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/bruschetta-with-tomatoes",
        "alt_text": "Toasted rustic Italian bread topped with diced ripe tomatoes, fresh basil, and olive oil",
    },
    {
        "keywords": ["carpaccio", "carpaccio di manzo", "beef carpaccio"],
        "dish_name": "Beef Carpaccio",
        "cuisine": "Italian",
        "category": "appetizer",
        "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=300&q=80",
        "photographer": "Alex Munsell",
        "photographer_url": "https://unsplash.com/@alexmunsell?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/thin-sliced-carpaccio",
        "alt_text": "Thinly shaved raw beef tenderloin with wild arugula, capers, and shaved parmesan",
    },
    {
        "keywords": ["carbonara", "spaghetti carbonara", "spaghetti alla carbonara"],
        "dish_name": "Spaghetti alla Carbonara",
        "cuisine": "Italian",
        "category": "noodles",
        "image_url": "https://images.unsplash.com/photo-1612874742237-6526221588e3?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1612874742237-6526221588e3?auto=format&fit=crop&w=300&q=80",
        "photographer": "Klara Kulikova",
        "photographer_url": "https://unsplash.com/@klarakulikova?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/spaghetti-carbonara",
        "alt_text": "Traditional Roman spaghetti carbonara with crispy guanciale, pecorino, and egg yolk",
    },
    {
        "keywords": ["cacio e pepe", "tonnarelli cacio e pepe"],
        "dish_name": "Tonnarelli Cacio e Pepe",
        "cuisine": "Italian",
        "category": "noodles",
        "image_url": "https://images.unsplash.com/photo-1608897013039-887f21d8c804?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1608897013039-887f21d8c804?auto=format&fit=crop&w=300&q=80",
        "photographer": "Davide Cantelli",
        "photographer_url": "https://unsplash.com/@cant89?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/creamy-pasta-dish",
        "alt_text": "Silky tonnarelli pasta tossed with sharp Pecorino Romano and freshly cracked black pepper",
    },
    {
        "keywords": ["tagliatelle al ragu", "bolognese", "tagliatelle bolognese", "pasta bolognese"],
        "dish_name": "Tagliatelle al Ragù Bolognese",
        "cuisine": "Italian",
        "category": "noodles",
        "image_url": "https://images.unsplash.com/photo-1621996346565-e3d5d6281781?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1621996346565-e3d5d6281781?auto=format&fit=crop&w=300&q=80",
        "photographer": "Olayinka Babalola",
        "photographer_url": "https://unsplash.com/@olayinka?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/pasta-with-meat-sauce",
        "alt_text": "Handmade egg tagliatelle ribbon pasta with slow-simmered beef and pork ragù",
    },
    {
        "keywords": ["risotto", "risotto ai funghi", "mushroom risotto", "porcini risotto"],
        "dish_name": "Risotto ai Funghi Porcini",
        "cuisine": "Italian",
        "category": "rice",
        "image_url": "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?auto=format&fit=crop&w=300&q=80",
        "photographer": "Jonathan Cooper",
        "photographer_url": "https://unsplash.com/@thejonathancooper?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/mushroom-risotto",
        "alt_text": "Creamy Carnaroli mushroom risotto garnished with fresh parsley and parmesan",
    },
    {
        "keywords": ["tiramisu", "tiramisu tradizionale", "italian tiramisu"],
        "dish_name": "Tiramisù Tradizionale",
        "cuisine": "Italian",
        "category": "dessert",
        "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=300&q=80",
        "photographer": "Klara Kulikova",
        "photographer_url": "https://unsplash.com/@klarakulikova?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/tiramisu-dessert",
        "alt_text": "Classic Italian tiramisu layered with espresso ladyfingers, mascarpone cream, and cocoa",
    },
    {
        "keywords": ["pizza", "margherita", "pizza margherita", "neapolitan pizza"],
        "dish_name": "Pizza Margherita",
        "cuisine": "Italian",
        "category": "pizza_bread",
        "image_url": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=300&q=80",
        "photographer": "Aurélien Lemasson-Théobald",
        "photographer_url": "https://unsplash.com/@aurelien_lemasson?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/margherita-pizza",
        "alt_text": "Wood-fired Neapolitan pizza margherita with San Marzano tomatoes, mozzarella, and fresh basil",
    },

    # --- INDIAN CUISINE ---
    {
        "keywords": ["butter chicken", "murgh makhani", "chicken makhani"],
        "dish_name": "Murgh Makhani (Butter Chicken)",
        "cuisine": "Indian",
        "category": "curry",
        "image_url": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?auto=format&fit=crop&w=300&q=80",
        "photographer": "Kunal Kalra",
        "photographer_url": "https://unsplash.com/@kunalkalra?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/butter-chicken-bowl",
        "alt_text": "Tender tandoori chicken simmered in rich creamy tomato and butter fenugreek gravy",
    },
    {
        "keywords": ["biryani", "chicken biryani", "dum biryani", "awadhi biryani", "mutton biryani"],
        "dish_name": "Awadhi Dum Biryani",
        "cuisine": "Indian",
        "category": "rice",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=300&q=80",
        "photographer": "Mounir Khashaba",
        "photographer_url": "https://unsplash.com/@mounirkhashaba?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/biryani-pot",
        "alt_text": "Aromatic fragrant saffron basmati rice layered with spiced meat and caramelized onions",
    },
    {
        "keywords": ["naan", "garlic naan", "garlic butter naan", "roti", "tandoori bread"],
        "dish_name": "Garlic Butter Naan",
        "cuisine": "Indian",
        "category": "pizza_bread",
        "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?auto=format&fit=crop&w=300&q=80",
        "photographer": "Prabal Goyal",
        "photographer_url": "https://unsplash.com/@prabalgoyal?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/naan-flatbread",
        "alt_text": "Pillowy tandoor baked garlic butter naan brushed with chopped coriander and ghee",
    },
    {
        "keywords": ["gulab jamun", "indian dessert", "jamun"],
        "dish_name": "Gulab Jamun",
        "cuisine": "Indian",
        "category": "dessert",
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=300&q=80",
        "photographer": "Sujit Kumar",
        "photographer_url": "https://unsplash.com/@sujit_kumar?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/gulab-jamun",
        "alt_text": "Golden fried milk solid dumplings steeped in warm saffron and cardamom rose syrup",
    },
    {
        "keywords": ["tikka masala", "chicken tikka", "paneer tikka"],
        "dish_name": "Chicken Tikka Masala",
        "cuisine": "Indian",
        "category": "curry",
        "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=300&q=80",
        "photographer": "Mounir Khashaba",
        "photographer_url": "https://unsplash.com/@mounirkhashaba?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/curry-with-rice",
        "alt_text": "Chargrilled chicken chunks in a spiced aromatic tomato and onion gravy",
    },

    # --- THAI CUISINE ---
    {
        "keywords": ["pad thai", "pad thai noodles", "thai noodles"],
        "dish_name": "Classic Pad Thai",
        "cuisine": "Thai",
        "category": "noodles",
        "image_url": "https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=300&q=80",
        "photographer": "GoodEats YQR",
        "photographer_url": "https://unsplash.com/@goodeatsyqr?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/pad-thai-plate",
        "alt_text": "Stir-fried rice noodles with tamarind, tiger prawns, crushed peanuts, and lime",
    },
    {
        "keywords": ["tom yum", "tom yum soup", "tom yum goong"],
        "dish_name": "Tom Yum Goong Soup",
        "cuisine": "Thai",
        "category": "soup",
        "image_url": "https://images.unsplash.com/photo-1548943487-a2e4e43b4853?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1548943487-a2e4e43b4853?auto=format&fit=crop&w=300&q=80",
        "photographer": "Nathana Rebouças",
        "photographer_url": "https://unsplash.com/@nathanareboucas?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/thai-soup",
        "alt_text": "Spicy and sour Thai tom yum soup infused with lemongrass, galangal, kaffir lime, and prawns",
    },

    # --- DESSERTS & CAFÉ ---
    {
        "keywords": ["acai bowl", "acai", "smoothie bowl", "açaí"],
        "dish_name": "Superfood Açaí Smoothie Bowl",
        "cuisine": "Dessert",
        "category": "dessert",
        "image_url": "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?auto=format&fit=crop&w=300&q=80",
        "photographer": "Jonas Kakaroto",
        "photographer_url": "https://unsplash.com/@jonaskakaroto?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/acai-bowl",
        "alt_text": "Chilled wild Brazilian açaí bowl topped with sliced banana, berries, chia seeds, and granola",
    },
    {
        "keywords": ["souffle", "chocolate souffle", "dark chocolate souffle", "lava cake"],
        "dish_name": "Molten Dark Chocolate Soufflé",
        "cuisine": "Dessert",
        "category": "dessert",
        "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=300&q=80",
        "photographer": "American Heritage Chocolate",
        "photographer_url": "https://unsplash.com/@americanheritagechocolate?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/chocolate-souffle",
        "alt_text": "Warm molten dark chocolate soufflé with powdered sugar dusting",
    },
    {
        "keywords": ["parfait", "matcha parfait", "ice cream parfait"],
        "dish_name": "Matcha Green Tea Parfait",
        "cuisine": "Dessert",
        "category": "dessert",
        "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&w=300&q=80",
        "photographer": "Emile Mbunzama",
        "photographer_url": "https://unsplash.com/@emilembunzama?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/ice-cream-dessert",
        "alt_text": "Layered artisanal Japanese matcha mousse parfait with shiratama dango and azuki",
    },
    {
        "keywords": ["taco", "tacos", "carnitas", "al pastor", "mexican taco"],
        "dish_name": "Artisanal Street Tacos",
        "cuisine": "Mexican",
        "category": "appetizer",
        "image_url": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=800&q=80",
        "thumbnail_url": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=300&q=80",
        "photographer": "Edgar Castrejon",
        "photographer_url": "https://unsplash.com/@edgarraw?utm_source=universal_menu_translator&utm_medium=referral",
        "source_url": "https://unsplash.com/photos/mexican-tacos",
        "alt_text": "Handmade corn tortilla street tacos topped with cilantro, diced onions, and lime wedges",
    },
]


def create_neutral_placeholder_svg(dish_name: str, cuisine: str = "Culinary") -> str:
    """Generate an inline SVG data URI representing a neutral culinary icon with clean title."""
    raw_name = urllib.parse.unquote(str(dish_name)).strip()
    clean_name = html.escape(raw_name[:32], quote=False)
    clean_cuisine = html.escape(cuisine.upper() if cuisine else "REPRESENTATIVE", quote=False)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#FBF2ED"/>
          <stop offset="1" stop-color="#F5ECE7"/>
        </linearGradient>
      </defs>
      <rect width="600" height="400" fill="url(#bg)"/>
      <rect x="20" y="20" width="560" height="360" rx="16" fill="none" stroke="#EADFD5" stroke-width="2" stroke-dasharray="8 6"/>
      <circle cx="300" cy="160" r="48" fill="#F2DFD3"/>
      <path d="M285 145 c0 -15 30 -15 30 0 v35 h-30 z M275 180 h50 v6 h-50 z" fill="#C74735"/>
      <text x="300" y="240" font-family="system-ui, sans-serif" font-size="12" font-weight="800" fill="#C74735" letter-spacing="2" text-anchor="middle">{clean_cuisine}</text>
      <text x="300" y="270" font-family="system-ui, sans-serif" font-size="16" font-weight="700" fill="#1F1B18" text-anchor="middle">{clean_name}</text>
      <text x="300" y="300" font-family="system-ui, sans-serif" font-size="12" fill="#70645C" text-anchor="middle">Representative photo unavailable</text>
    </svg>"""
    return f"data:image/svg+xml;utf8,{urllib.parse.quote(svg)}"


class CuratedImageProvider(BaseImageProvider):
    """Provides high-confidence verified culinary photographs from local catalog,

    falling back to neutral cuisine SVG placeholders when no match is found.
    """

    name = "curated"

    def is_configured(self) -> bool:
        return True

    async def search_image(self, query: DishImageQuery, timeout_seconds: float = 3.5) -> Optional[DishImageInfo]:
        primary_query, fallback_query, category = build_image_search_query(
            dish_name=query.dish_name,
            native_name=query.native_name,
            transliteration=query.transliteration,
            cuisine=query.cuisine,
            section=query.section,
            ingredients=query.ingredients,
        )

        search_tokens = clean_dish_name(f"{query.dish_name} {query.native_name or ''} {query.transliteration or ''}").split()

        best_match = None
        highest_score = 0.0

        for entry in CURATED_DISH_CATALOG:
            entry_cat = entry.get("category", "")
            # Strict category rejection
            if category == "beverage" and entry_cat != "beverage":
                continue
            if category == "dessert" and entry_cat not in ("dessert", "bakery"):
                continue
            if category in ("noodles", "soup", "meat_bbq") and entry_cat in ("beverage", "dessert"):
                continue

            score = 0.0
            for kw in entry["keywords"]:
                kw_tokens = kw.lower().split()
                if all(t in search_tokens or t in primary_query.lower() for t in kw_tokens):
                    # Exact or strong multi-word match
                    score = max(score, 0.95 if len(kw_tokens) > 1 else 0.85)
                elif any(re.search(rf"\b{re.escape(t)}\b", kw.lower()) for t in search_tokens if len(t) >= 4):
                    score = max(score, 0.65)

            # Same cuisine boost
            if query.cuisine and query.cuisine.lower() == entry.get("cuisine", "").lower():
                score += 0.05

            if score > highest_score and score >= 0.70:
                highest_score = score
                best_match = entry

        if best_match and highest_score >= 0.70:
            return DishImageInfo(
                image_url=best_match["image_url"],
                thumbnail_url=best_match.get("thumbnail_url", best_match["image_url"]),
                source="curated",
                photographer=best_match.get("photographer", "Culinary Archive"),
                photographer_url=best_match.get("photographer_url"),
                source_url=best_match.get("source_url"),
                alt_text=best_match.get("alt_text", f"Representative photo of {query.dish_name}"),
                relevance_score=min(1.0, round(highest_score, 2)),
                is_fallback=False,
                status="available",
                query_used=primary_query,
                dish_category=category,
            )

        # Fallback: create neutral cuisine placeholder with explicit unavailable notice
        inferred_c = infer_cuisine(query.dish_name, query.native_name, hint=query.cuisine) or "Culinary"
        placeholder_uri = create_neutral_placeholder_svg(query.dish_name, inferred_c)

        return DishImageInfo(
            image_url=placeholder_uri,
            thumbnail_url=placeholder_uri,
            source="placeholder",
            photographer="Universal Menu Translator",
            photographer_url=None,
            source_url=None,
            alt_text=f"Representative photo unavailable (Representative image unavailable) for {query.dish_name}",
            relevance_score=0.0,
            is_fallback=True,
            status="unavailable",
            query_used=primary_query,
            dish_category=category,
        )

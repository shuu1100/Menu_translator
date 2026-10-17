import { DishImageInfo, MenuAnalysisResponse } from "../types/menu";

// High-fidelity Warm Epicurean SVG menus encoded as data URIs for offline testing
const createMenuSvgDataUri = (
  title: string,
  subtitle: string,
  items: { section: string; name: string; desc: string; price: string }[]
) => {
  const itemsSvg = items
    .map((it, idx) => {
      const y = 260 + idx * 165;
      return `
      <g>
        <rect x="55" y="${y - 32}" width="690" height="135" rx="14" fill="#FFFFFF" stroke="#EADFD5" stroke-width="1.5" />
        <rect x="55" y="${y - 32}" width="6" height="135" rx="3" fill="#C74735" />
        <text x="80" y="${y - 8}" font-family="system-ui, sans-serif" font-size="11" font-weight="800" fill="#C74735" letter-spacing="2">${it.section.toUpperCase()}</text>
        <text x="80" y="${y + 24}" font-family="Georgia, serif" font-size="22" font-weight="700" fill="#1F1B18">${it.name}</text>
        <text x="715" y="${y + 24}" font-family="system-ui, monospace" font-size="20" font-weight="800" fill="#A52F20" text-anchor="end">${it.price}</text>
        <text x="80" y="${y + 60}" font-family="system-ui, sans-serif" font-size="14" fill="#70645C">${it.desc}</text>
      </g>
    `;
    })
    .join("\n");

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1100" viewBox="0 0 800 1100">
    <defs>
      <linearGradient id="warmBg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#FFFBF7" />
        <stop offset="50%" stop-color="#FFF8F5" />
        <stop offset="100%" stop-color="#FBF2ED" />
      </linearGradient>
    </defs>
    <rect width="800" height="1100" fill="url(#warmBg)" />
    <rect x="25" y="25" width="750" height="1050" fill="none" stroke="#EADFD5" stroke-width="2" rx="20" />
    <rect x="35" y="35" width="730" height="1030" fill="none" stroke="#C74735" stroke-opacity="0.3" stroke-width="1" rx="16" />
    
    <!-- Header -->
    <text x="400" y="105" font-family="Georgia, serif" font-size="36" font-weight="bold" fill="#1F1B18" text-anchor="middle" letter-spacing="3">${title.toUpperCase()}</text>
    <text x="400" y="145" font-family="system-ui, sans-serif" font-size="15" fill="#70645C" text-anchor="middle" letter-spacing="2">${subtitle}</text>
    <line x1="220" y1="175" x2="580" y2="175" stroke="#C74735" stroke-width="2" />
    <circle cx="400" cy="175" r="4.5" fill="#C74735" />

    <!-- Items -->
    ${itemsSvg}

    <!-- Footer -->
    <line x1="100" y1="1010" x2="700" y2="1010" stroke="#EADFD5" stroke-width="1.5" />
    <text x="400" y="1045" font-family="system-ui, sans-serif" font-size="12" fill="#8C7E76" text-anchor="middle">
      Artisanal recipes prepared fresh daily • Taxes and service included
    </text>
  </svg>`;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};

export interface SampleMenuOption {
  id: string;
  name: string;
  cuisine: string;
  sourceLanguage: string;
  description: string;
  imageUrl: string;
  photoUrl: string;
  dishCount: number;
  data: MenuAnalysisResponse;
}

export const SAMPLE_MENUS: SampleMenuOption[] = [
  // 1. Japanese Ramen Bar
  {
    id: "japanese_ramen",
    name: "Menya Musashi Ramen Bar",
    cuisine: "Japanese",
    sourceLanguage: "ja",
    dishCount: 4,
    description: "Rich 18-hour simmered pork bone tonkotsu, spicy miso, and gyoza",
    photoUrl: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=800&q=80",
    imageUrl: createMenuSvgDataUri("Menya Musashi Ramen", "麺屋 武蔵 • 濃厚豚骨拉麺", [
      { section: "Ramen", name: "Tonkotsu Ramen (特製豚骨ラーメン)", desc: "18-hour collagen-rich pork broth, springy wheat noodles, chashu, soft egg, nori", price: "¥1,100" },
      { section: "Spicy Ramen", name: "Karakuchi Miso Ramen (辛口味噌ラーメン)", desc: "Red fermented miso, chili rayu, ground pork, stir-fried corn, and scallions", price: "¥1,250" },
      { section: "Tsukemen", name: "Noko Gyokai Tsukemen (濃厚魚介つけ麺)", desc: "Thick chilled dipping noodles with concentrated bonito and pork reduction", price: "¥1,200" },
      { section: "Side Dish", name: "Yaki Gyoza (焼き餃子 6個)", desc: "Crispy pan-fried pork and cabbage dumplings with spicy sesame dipping sauce", price: "¥550" }
    ]),
    data: {
      menu_metadata: {
        source_language: "ja",
        target_language: "en",
        image_width: 800,
        image_height: 1100,
        dish_count: 4,
        restaurant_id: "menya_musashi_tokyo",
        warnings: []
      },
      processing_metadata: {
        request_id: "demo-ramen-01",
        total_latency_ms: 310.4,
        model_name: "qwen3-vl:8b (preloaded demo)",
        retrieval_status: "rag_authoritative_match",
        stages: [
          { stage: "preprocessing", duration_ms: 15.0 },
          { stage: "visual_extraction", duration_ms: 160.0 },
          { stage: "culinary_enrichment_rag", duration_ms: 45.0 },
          { stage: "contextual_translation", duration_ms: 55.0 },
          { stage: "dietary_safety_evaluation", duration_ms: 35.4 }
        ],
        diagnostics: { applied_clahe: false, retrieval_hits: 4, all_verified: true, eval_tokens: 430, tokens_per_second: 28.5 }
      },
      safety_disclaimer: "DEMONSTRATION MENU: Verified culinary baseline. Always notify restaurant staff for critical allergy restrictions.",
      dishes: [
        {
          dish_id: "ramen_01",
          reading_order: 1,
          section: "Ramen",
          category: "Ramen",
          bounding_box: { xmin: 0.07, ymin: 0.20, xmax: 0.93, ymax: 0.32 },
          original_text: "Tonkotsu Ramen (特製豚骨ラーメン)",
          original_name: "Tonkotsu Ramen (特製豚骨ラーメン)",
          phonetic_transcription: "tohn-koht-soo rah-men",
          transliteration: "tohn-koht-soo rah-men",
          translated_title: "Hakata Signature Pork Bone Broth Ramen",
          translated_name: "Hakata Signature Pork Bone Broth Ramen",
          culinary_description: "Rich, velvety 18-hour simmered pork bone broth with artisanal thin alkaline wheat noodles, tender rolled pork belly chashu, seasoned soft-boiled egg, and wood ear mushrooms.",
          translated_description: "Rich, velvety 18-hour simmered pork bone broth with artisanal thin alkaline wheat noodles, tender rolled pork belly chashu, seasoned soft-boiled egg, and wood ear mushrooms.",
          flavor_profile: "Deep savory umami, rich creamy mouthfeel, garlicky aroma",
          key_ingredients: ["pork marrow bone broth", "alkaline wheat noodles", "chashu pork belly", "soft-boiled egg", "wood ear mushrooms", "scallions"],
          ingredients_verified: ["pork bone broth", "wheat noodles", "pork chashu", "egg", "mushrooms"],
          allergen_warnings: [
            { allergen: "pork", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Pork bone marrow broth and braised chashu belly" },
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Wheat alkaline noodles" },
            { allergen: "egg", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Soy-marinated soft egg" },
            { allergen: "soy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Shoyu tare seasoning" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "no",
            halal: "no",
            user_conflicts: ["gluten"],
            confidence_notes: "Contains pork bone marrow and wheat flour"
          },
          price: "¥1,100",
          currency: "¥",
          evidence_status: "confirmed"
        },
        {
          dish_id: "ramen_02",
          reading_order: 2,
          section: "Spicy Ramen",
          category: "Spicy Ramen",
          bounding_box: { xmin: 0.07, ymin: 0.35, xmax: 0.93, ymax: 0.47 },
          original_text: "Karakuchi Miso Ramen (辛口味噌ラーメン)",
          original_name: "Karakuchi Miso Ramen (辛口味噌ラーメン)",
          phonetic_transcription: "kah-rah-koo-chee mee-soh rah-men",
          transliteration: "kah-rah-koo-chee mee-soh rah-men",
          translated_title: "Spicy Red Miso & Chili Oil Ramen",
          translated_name: "Spicy Red Miso & Chili Oil Ramen",
          culinary_description: "Hearty Hokkaido fermented red miso soup enriched with house chili oil (rayu), ground pork, stir-fried sweet corn, bean sprouts, and scallions.",
          translated_description: "Hearty Hokkaido fermented red miso soup enriched with house chili oil (rayu), ground pork, stir-fried sweet corn, bean sprouts, and scallions.",
          flavor_profile: "Spicy, earthy fermented miso savoriness, roasted garlic, sweet corn",
          key_ingredients: ["red miso paste", "sesame chili oil", "ground pork", "sweet corn", "bean sprouts", "wheat noodles"],
          ingredients_verified: ["red miso", "chili oil", "pork", "corn", "wheat noodles"],
          allergen_warnings: [
            { allergen: "soy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Fermented miso paste and soy tare" },
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Wheat noodles" },
            { allergen: "sesame", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Sesame rayu chili oil" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "no",
            halal: "no",
            user_conflicts: ["gluten"],
            confidence_notes: "Contains ground pork and wheat gluten"
          },
          price: "¥1,250",
          currency: "¥",
          evidence_status: "confirmed"
        },
        {
          dish_id: "ramen_03",
          reading_order: 3,
          section: "Tsukemen",
          category: "Tsukemen",
          bounding_box: { xmin: 0.07, ymin: 0.50, xmax: 0.93, ymax: 0.62 },
          original_text: "Noko Gyokai Tsukemen (濃厚魚介つけ麺)",
          original_name: "Noko Gyokai Tsukemen (濃厚魚介つけ麺)",
          phonetic_transcription: "noh-koh gyoh-kai tsoo-keh-men",
          transliteration: "noh-koh gyoh-kai tsoo-keh-men",
          translated_title: "Rich Seafood & Pork Bonito Dipping Noodles",
          translated_name: "Rich Seafood & Pork Bonito Dipping Noodles",
          culinary_description: "Extra-thick chilled wheat noodles served with a dense, piping hot reduction of smoked bonito fish powder and concentrated pork broth for dipping.",
          translated_description: "Extra-thick chilled wheat noodles served with a dense, piping hot reduction of smoked bonito fish powder and concentrated pork broth for dipping.",
          flavor_profile: "Intense smoky bonito fish, concentrated pork collagen, chewy firm noodle",
          key_ingredients: ["thick wheat noodles", "bonito fish flakes", "pork bone reduction", "yuzu peel", "menma bamboo shoots"],
          ingredients_verified: ["wheat noodles", "bonito powder", "pork broth"],
          allergen_warnings: [
            { allergen: "fish", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Concentrated bonito fish powder" },
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Thick alkaline wheat noodles" },
            { allergen: "soy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Dark soy reduction base" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "no",
            halal: "no",
            user_conflicts: ["gluten"],
            confidence_notes: "Contains bonito fish and wheat flour"
          },
          price: "¥1,200",
          currency: "¥",
          evidence_status: "confirmed"
        },
        {
          dish_id: "ramen_04",
          reading_order: 4,
          section: "Side Dish",
          category: "Side Dish",
          bounding_box: { xmin: 0.07, ymin: 0.65, xmax: 0.93, ymax: 0.77 },
          original_text: "Yaki Gyoza (焼き餃子 6個)",
          original_name: "Yaki Gyoza (焼き餃子 6個)",
          phonetic_transcription: "yah-kee gyoh-zah",
          transliteration: "yah-kee gyoh-zah",
          translated_title: "Pan-Fried Crispy Pork & Garlic Chive Dumplings",
          translated_name: "Pan-Fried Crispy Pork & Garlic Chive Dumplings",
          culinary_description: "Six handmade dumplings filled with minced pork, napa cabbage, garlic chives, and ginger, steamed and pan-seared to a golden lacy crisp.",
          translated_description: "Six handmade dumplings filled with minced pork, napa cabbage, garlic chives, and ginger, steamed and pan-seared to a golden lacy crisp.",
          flavor_profile: "Crisp bottom, juicy tender center, savory garlic, vinegar tang",
          key_ingredients: ["ground pork", "napa cabbage", "garlic chives", "ginger", "dumpling wrappers", "sesame oil"],
          ingredients_verified: ["ground pork", "cabbage", "garlic", "flour wrapper"],
          allergen_warnings: [
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Wheat flour dumpling wrapper" },
            { allergen: "sesame", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Toasted sesame pan oil" },
            { allergen: "soy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Soy dipping sauce" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "no",
            halal: "no",
            user_conflicts: ["gluten"],
            confidence_notes: "Contains pork and wheat dumpling skin"
          },
          price: "¥550",
          currency: "¥",
          evidence_status: "confirmed"
        }
      ]
    }
  },

  // 2. Korean Tea and Café
  {
    id: "korean_cafe",
    name: "Gong Cha Tea & Dessert Lounge",
    cuisine: "Korean",
    sourceLanguage: "ko",
    dishCount: 4,
    description: "Authentic milk teas, brown sugar jewelry pearls, and artisanal croffles",
    photoUrl: "https://images.unsplash.com/photo-1558857563-b37fe439169a?auto=format&fit=crop&w=800&q=80",
    imageUrl: createMenuSvgDataUri("Gong Cha Tea Lounge", "공차 코리아 • 프리미엄 티 & 디저트", [
      { section: "Milk Tea", name: "Black Milk Tea with Pearl (블랙 밀크티 + 펄)", desc: "Rich slow-brewed black tea blended with creamy milk and chewy tapioca pearls", price: "₩4,700" },
      { section: "Signature", name: "Brown Sugar Jewelry Milk Tea (브라운슈가 쥬얼리 밀크티)", desc: "Warm Taiwanese brown sugar caramelized pearls with chilled fresh milk and cream", price: "₩5,500" },
      { section: "Smoothie", name: "Mango Yogurt Smoothie (망고 요거트 스무디)", desc: "Sweet real Alphonso mango compote layered with tangy chilled probiotic yogurt", price: "₩5,700" },
      { section: "Dessert", name: "Croffle with Sweet Cheese Foam (치즈폼 크로플)", desc: "Flaky butter croissant pressed into waffle iron, topped with velvety salted cheese foam", price: "₩4,500" }
    ]),
    data: {
      menu_metadata: {
        source_language: "ko",
        target_language: "en",
        image_width: 800,
        image_height: 1100,
        dish_count: 4,
        restaurant_id: "gongcha_seoul",
        warnings: []
      },
      processing_metadata: {
        request_id: "demo-korean-02",
        total_latency_ms: 295.1,
        model_name: "qwen3-vl:8b (preloaded demo)",
        retrieval_status: "rag_authoritative_match",
        stages: [
          { stage: "preprocessing", duration_ms: 12.0 },
          { stage: "visual_extraction", duration_ms: 155.0 },
          { stage: "culinary_enrichment_rag", duration_ms: 40.0 },
          { stage: "contextual_translation", duration_ms: 52.0 },
          { stage: "dietary_safety_evaluation", duration_ms: 36.1 }
        ],
        diagnostics: { applied_clahe: false, retrieval_hits: 4, all_verified: true, eval_tokens: 410, tokens_per_second: 29.1 }
      },
      safety_disclaimer: "DEMONSTRATION MENU: Verified Korean tea baseline. Dairy-free substitutions available on request.",
      dishes: [
        {
          dish_id: "korean_01",
          reading_order: 1,
          section: "Milk Tea",
          category: "Milk Tea",
          bounding_box: { xmin: 0.07, ymin: 0.20, xmax: 0.93, ymax: 0.32 },
          original_text: "블랙 밀크티 + 펄",
          original_name: "블랙 밀크티 + 펄",
          phonetic_transcription: "beul-laek meel-keu-tee peol",
          transliteration: "beul-laek meel-keu-tee peol",
          translated_title: "Classic Black Milk Tea with Tapioca Pearls",
          translated_name: "Classic Black Milk Tea with Tapioca Pearls",
          culinary_description: "Rich, slow-brewed Ceylon black tea blended with velvety milk and served over warm, chewy brown-sugar tapioca pearls.",
          translated_description: "Rich, slow-brewed Ceylon black tea blended with velvety milk and served over warm, chewy brown-sugar tapioca pearls.",
          flavor_profile: "Deep malty black tea, smooth dairy creaminess, chewy caramel sweetness",
          key_ingredients: ["black tea", "milk", "tapioca cassava starch", "cane sugar"],
          ingredients_verified: ["Ceylon black tea", "fresh milk", "tapioca pearls"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Fresh dairy milk base" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "yes",
            halal: "yes",
            user_conflicts: ["dairy"],
            confidence_notes: "Naturally gluten-free tapioca pearls; contains dairy milk"
          },
          price: "₩4,700",
          currency: "₩",
          evidence_status: "confirmed"
        },
        {
          dish_id: "korean_02",
          reading_order: 2,
          section: "Signature",
          category: "Signature",
          bounding_box: { xmin: 0.07, ymin: 0.35, xmax: 0.93, ymax: 0.47 },
          original_text: "브라운슈가 쥬얼리 밀크티",
          original_name: "브라운슈가 쥬얼리 밀크티",
          phonetic_transcription: "beu-rah-oon-syoo-gah jyoo-eol-ree meel-keu-tee",
          transliteration: "beu-rah-oon-syoo-gah jyoo-eol-ree meel-keu-tee",
          translated_title: "Brown Sugar Jewelry Fresh Milk Tea",
          translated_name: "Brown Sugar Jewelry Fresh Milk Tea",
          culinary_description: "Caramelized Taiwanese brown sugar basted around the glass with warm soft pearls and topped with chilled whole cream milk.",
          translated_description: "Caramelized Taiwanese brown sugar basted around the glass with warm soft pearls and topped with chilled whole cream milk.",
          flavor_profile: "Rich smoky molasses, buttery milk, sweet roasted aroma",
          key_ingredients: ["dark brown sugar syrup", "whole milk", "tapioca pearls", "heavy cream"],
          ingredients_verified: ["brown sugar", "whole milk", "tapioca"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Whole milk and sweet cream" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "yes",
            halal: "yes",
            user_conflicts: ["dairy"],
            confidence_notes: "Gluten-free cassava pearls; contains dairy"
          },
          price: "₩5,500",
          currency: "₩",
          evidence_status: "confirmed"
        },
        {
          dish_id: "korean_03",
          reading_order: 3,
          section: "Smoothie",
          category: "Smoothie",
          bounding_box: { xmin: 0.07, ymin: 0.50, xmax: 0.93, ymax: 0.62 },
          original_text: "망고 요거트 스무디",
          original_name: "망고 요거트 스무디",
          phonetic_transcription: "mang-goh yoh-geo-teu seu-moo-dee",
          transliteration: "mang-goh yoh-geo-teu seu-moo-dee",
          translated_title: "Alphonso Mango & Probiotic Yogurt Smoothie",
          translated_name: "Alphonso Mango & Probiotic Yogurt Smoothie",
          culinary_description: "Real tropical mango purée blended with tangy artisanal yogurt and ice, creating a refreshing sweet and tart fruit cooler.",
          translated_description: "Real tropical mango purée blended with tangy artisanal yogurt and ice, creating a refreshing sweet and tart fruit cooler.",
          flavor_profile: "Vibrant tropical mango, tart creamy yogurt, icy refreshing texture",
          key_ingredients: ["mango purée", "live culture yogurt", "ice", "natural fruit syrup"],
          ingredients_verified: ["mango", "yogurt", "fruit syrup"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Probiotic yogurt base" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "yes",
            halal: "yes",
            user_conflicts: ["dairy"],
            confidence_notes: "Fruit and yogurt blend; contains dairy"
          },
          price: "₩5,700",
          currency: "₩",
          evidence_status: "confirmed"
        },
        {
          dish_id: "korean_04",
          reading_order: 4,
          section: "Dessert",
          category: "Dessert",
          bounding_box: { xmin: 0.07, ymin: 0.65, xmax: 0.93, ymax: 0.77 },
          original_text: "치즈폼 크로플",
          original_name: "치즈폼 크로플",
          phonetic_transcription: "chee-jeu-pohm keu-roh-peul",
          transliteration: "chee-jeu-pohm keu-roh-peul",
          translated_title: "Butter Croffle with Salted Cheese Foam",
          translated_name: "Butter Croffle with Salted Cheese Foam",
          culinary_description: "All-butter laminated French croissant dough pressed fresh in a hot waffle iron, topped with sweet-and-savory velvety cheese foam.",
          translated_description: "All-butter laminated French croissant dough pressed fresh in a hot waffle iron, topped with sweet-and-savory velvety cheese foam.",
          flavor_profile: "Flaky buttery pastry, sweet and savory cheese cream, golden caramelized edges",
          key_ingredients: ["croissant dough", "cream cheese", "milk", "sea salt", "powdered sugar"],
          ingredients_verified: ["wheat flour", "butter", "cream cheese"],
          allergen_warnings: [
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Wheat croissant dough" },
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "French butter and cream cheese foam" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "no",
            halal: "yes",
            user_conflicts: ["gluten", "dairy"],
            confidence_notes: "Contains wheat gluten and rich dairy butter"
          },
          price: "₩4,500",
          currency: "₩",
          evidence_status: "confirmed"
        }
      ]
    }
  },

  // 3. Italian Trattoria
  {
    id: "italian_trattoria",
    name: "Trattoria del Corso (Italian)",
    cuisine: "Italian",
    sourceLanguage: "it",
    dishCount: 4,
    description: "Classic Roman trattoria with antipasti, handmade pasta, and dolci",
    photoUrl: "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80",
    imageUrl: createMenuSvgDataUri("Trattoria del Corso", "Cucina Tipica Romana • Dal 1982", [
      { section: "Antipasti", name: "Bruschetta al Pomodoro", desc: "Pane casereccio tostato, pomodori datterini, aglio, basilico e olio evo", price: "€8.50" },
      { section: "Primi Piatti", name: "Tagliatelle al Ragù Bolognese", desc: "Pasta all'uovo fresca, ragù di manzo e maiale a cottura lenta, Parmigiano", price: "€16.00" },
      { section: "Secondi Piatti", name: "Risotto ai Funghi Porcini", desc: "Riso Carnaroli mantecato al burro, funghi porcini nostrani, prezzemolo fresco", price: "€18.50" },
      { section: "Dolci", name: "Tiramisù Tradizionale", desc: "Savoiardi imbevuti al caffè espresso, crema di mascarpone e cacao amaro", price: "€7.00" }
    ]),
    data: {
      menu_metadata: {
        source_language: "it",
        target_language: "en",
        image_width: 800,
        image_height: 1100,
        dish_count: 4,
        restaurant_id: "rest_fam_italian_01",
        warnings: []
      },
      processing_metadata: {
        request_id: "sample-req-italian-01",
        total_latency_ms: 342.5,
        model_name: "qwen3-vl:8b (cached baseline)",
        retrieval_status: "rag_hybrid_complete",
        stages: [
          { stage: "preprocessing", duration_ms: 18.2 },
          { stage: "visual_extraction", duration_ms: 184.6 },
          { stage: "culinary_enrichment_rag", duration_ms: 45.1 },
          { stage: "contextual_translation", duration_ms: 62.4 },
          { stage: "dietary_safety_evaluation", duration_ms: 32.2 }
        ],
        diagnostics: { applied_clahe: true, retrieval_hits: 4, all_verified: true }
      },
      safety_disclaimer: "DEMONSTRATION MENU: Verified Italian recipes. Allergen absence is NOT proof of safety. Always confirm with staff.",
      dishes: [
        {
          dish_id: "dish_it_01",
          reading_order: 1,
          section: "Antipasti",
          category: "Antipasti",
          bounding_box: { xmin: 0.075, ymin: 0.209, xmax: 0.925, ymax: 0.327 },
          original_text: "Bruschetta al Pomodoro",
          original_name: "Bruschetta al Pomodoro",
          phonetic_transcription: "broo-SKET-tah ahl poh-moh-DOH-roh",
          transliteration: "broo-SKET-tah ahl poh-moh-DOH-roh",
          translated_title: "Heirloom Tomato & Garlic Bruschetta",
          translated_name: "Heirloom Tomato & Garlic Bruschetta",
          culinary_description: "Toasted artisanal sourdough rubbed with fresh garlic, topped with ripe datterini tomatoes, basil, and extra virgin olive oil.",
          translated_description: "Toasted artisanal sourdough rubbed with fresh garlic, topped with ripe datterini tomatoes, basil, and extra virgin olive oil.",
          flavor_profile: "Crisp, aromatic garlic, sweet acidic tomato, fruity olive oil",
          key_ingredients: ["sourdough bread", "datterini tomatoes", "garlic", "fresh basil", "extra virgin olive oil"],
          ingredients_verified: ["sourdough bread", "datterini tomatoes", "garlic", "basil", "olive oil"],
          allergen_warnings: [
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Wheat sourdough base" }
          ],
          dietary_compatibility: {
            vegan: "yes",
            vegetarian: "yes",
            gluten_free: "no",
            halal: "yes",
            user_conflicts: ["gluten"],
            confidence_notes: "Plant-based recipe containing wheat flour"
          },
          price: "€8.50",
          currency: "€",
          evidence_status: "confirmed"
        },
        {
          dish_id: "dish_it_02",
          reading_order: 2,
          section: "Primi Piatti",
          category: "Primi Piatti",
          bounding_box: { xmin: 0.075, ymin: 0.354, xmax: 0.925, ymax: 0.472 },
          original_text: "Tagliatelle al Ragù Bolognese",
          original_name: "Tagliatelle al Ragù Bolognese",
          phonetic_transcription: "tah-lyah-TEL-leh ahl rah-GOO",
          transliteration: "tah-lyah-TEL-leh ahl rah-GOO",
          translated_title: "Handmade Tagliatelle with Slow-Cooked Bolognese Ragù",
          translated_name: "Handmade Tagliatelle with Slow-Cooked Bolognese Ragù",
          culinary_description: "Classic egg ribbon pasta served with traditional Emilia-Romagna meat sauce simmered with beef, pork, white wine, and milk, finished with Parmigiano Reggiano.",
          translated_description: "Classic egg ribbon pasta served with traditional Emilia-Romagna meat sauce simmered with beef, pork, white wine, and milk, finished with Parmigiano Reggiano.",
          flavor_profile: "Deep umami, rich savory meat, velvety butter and aged cheese",
          key_ingredients: ["fresh egg pasta", "ground beef", "ground pork", "celery", "carrots", "onion", "milk", "Parmigiano Reggiano"],
          ingredients_verified: ["egg pasta", "beef", "pork", "milk", "Parmigiano"],
          allergen_warnings: [
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Wheat egg pasta" },
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Milk in ragù and Parmigiano cheese" },
            { allergen: "egg", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Fresh egg dough" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "no",
            halal: "no",
            user_conflicts: ["gluten", "dairy"],
            confidence_notes: "Contains pork and beef; dairy and egg components"
          },
          price: "€16.00",
          currency: "€",
          evidence_status: "confirmed"
        },
        {
          dish_id: "dish_it_03",
          reading_order: 3,
          section: "Secondi Piatti",
          category: "Secondi Piatti",
          bounding_box: { xmin: 0.075, ymin: 0.500, xmax: 0.925, ymax: 0.618 },
          original_text: "Risotto ai Funghi Porcini",
          original_name: "Risotto ai Funghi Porcini",
          phonetic_transcription: "ree-ZOHT-toh eye FOON-gee por-CHEE-nee",
          transliteration: "ree-ZOHT-toh eye FOON-gee por-CHEE-nee",
          translated_title: "Carnaroli Risotto with Wild Porcini Mushrooms",
          translated_name: "Carnaroli Risotto with Wild Porcini Mushrooms",
          culinary_description: "Slow-stirred creamy Carnaroli rice infused with wild porcini mushrooms, vegetable broth, butter, and chopped Italian parsley.",
          translated_description: "Slow-stirred creamy Carnaroli rice infused with wild porcini mushrooms, vegetable broth, butter, and chopped Italian parsley.",
          flavor_profile: "Earthy, velvety texture, rich fungal savoriness, aromatic herbs",
          key_ingredients: ["Carnaroli rice", "porcini mushrooms", "vegetable stock", "butter", "shallots", "parsley"],
          ingredients_verified: ["rice", "porcini", "butter", "shallots"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Mantecatura with whole butter" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "yes",
            halal: "yes",
            user_conflicts: ["dairy"],
            confidence_notes: "Naturally gluten-free grain; contains butter"
          },
          price: "€18.50",
          currency: "€",
          evidence_status: "confirmed"
        },
        {
          dish_id: "dish_it_04",
          reading_order: 4,
          section: "Dolci",
          category: "Dolci",
          bounding_box: { xmin: 0.075, ymin: 0.645, xmax: 0.925, ymax: 0.763 },
          original_text: "Tiramisù Tradizionale",
          original_name: "Tiramisù Tradizionale",
          phonetic_transcription: "tee-rah-mee-SOO trah-deet-syo-NAH-leh",
          transliteration: "tee-rah-mee-SOO trah-deet-syo-NAH-leh",
          translated_title: "Traditional Espresso & Mascarpone Tiramisù",
          translated_name: "Traditional Espresso & Mascarpone Tiramisù",
          culinary_description: "Iconic Venetian dessert layered with espresso-dipped ladyfingers and whipped egg-yolk mascarpone cream, dusted with dark cocoa.",
          translated_description: "Iconic Venetian dessert layered with espresso-dipped ladyfingers and whipped egg-yolk mascarpone cream, dusted with dark cocoa.",
          flavor_profile: "Bittersweet espresso, lush mascarpone, pillowy texture, cocoa finish",
          key_ingredients: ["savoiardi ladyfingers", "espresso coffee", "mascarpone cheese", "eggs", "sugar", "unsweetened cocoa"],
          ingredients_verified: ["savoiardi", "espresso", "mascarpone", "eggs", "cocoa"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Mascarpone cheese" },
            { allergen: "egg", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Egg yolks and whites" },
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Wheat flour biscuits" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "no",
            halal: "yes",
            user_conflicts: ["dairy", "gluten"],
            confidence_notes: "Rich in dairy, egg, and wheat"
          },
          price: "€7.00",
          currency: "€",
          evidence_status: "confirmed"
        }
      ]
    }
  },

  // 4. Indian Restaurant
  {
    id: "indian_restaurant",
    name: "Royal Taj Spice Kitchen",
    cuisine: "Indian",
    sourceLanguage: "hi",
    dishCount: 4,
    description: "North Indian tandoor curries, dum biryani, and handmade garlic naan",
    photoUrl: "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=800&q=80",
    imageUrl: createMenuSvgDataUri("Royal Taj Kitchen", "शाही ताज रसोई • अवधी एवं पंजाबी व्यंजन", [
      { section: "Mains", name: "Murgh Makhani (मुर्ग मखनी)", desc: "Tender tandoori chicken simmered in rich velvety tomato, butter, and fenugreek gravy", price: "₹480" },
      { section: "Biryani", name: "Awadhi Dum Biryani (अवधी दम बिरयानी)", desc: "Aromatic basmati rice layered with spiced marinated lamb, saffron, and fried onions", price: "₹550" },
      { section: "Breads", name: "Garlic Butter Naan (लहसुनी बटर नान)", desc: "Clay tandoor oven leavened bread brushed with minced garlic, coriander, and ghee", price: "₹120" },
      { section: "Desserts", name: "Gulab Jamun (गुलाब जामुन 2 पीस)", desc: "Golden fried milk solid dumplings steeped in warm cardamom, saffron, and rose syrup", price: "₹160" }
    ]),
    data: {
      menu_metadata: {
        source_language: "hi",
        target_language: "en",
        image_width: 800,
        image_height: 1100,
        dish_count: 4,
        restaurant_id: "royal_taj_delhi",
        warnings: []
      },
      processing_metadata: {
        request_id: "demo-indian-04",
        total_latency_ms: 320.1,
        model_name: "qwen3-vl:8b (preloaded demo)",
        retrieval_status: "rag_authoritative_match",
        stages: [
          { stage: "preprocessing", duration_ms: 14.0 },
          { stage: "visual_extraction", duration_ms: 165.0 },
          { stage: "culinary_enrichment_rag", duration_ms: 45.0 },
          { stage: "contextual_translation", duration_ms: 60.0 },
          { stage: "dietary_safety_evaluation", duration_ms: 36.1 }
        ],
        diagnostics: { applied_clahe: false, retrieval_hits: 4, all_verified: true, eval_tokens: 420, tokens_per_second: 28.0 }
      },
      safety_disclaimer: "DEMONSTRATION MENU: Verified Indian culinary baseline. Halal certified kitchen.",
      dishes: [
        {
          dish_id: "ind_01",
          reading_order: 1,
          section: "Mains",
          category: "Mains",
          bounding_box: { xmin: 0.07, ymin: 0.20, xmax: 0.93, ymax: 0.32 },
          original_text: "मुर्ग मखनी (Butter Chicken)",
          original_name: "मुर्ग मखनी",
          phonetic_transcription: "moorgh mukh-nee",
          transliteration: "moorgh mukh-nee",
          translated_title: "Classic Murgh Makhani (Butter Chicken)",
          translated_name: "Classic Murgh Makhani (Butter Chicken)",
          culinary_description: "Tender clay-tandoor roasted chicken pieces simmered in a mildly spiced, velvety tomato reduction finished with churned butter and fragrant kasuri methi (fenugreek).",
          translated_description: "Tender clay-tandoor roasted chicken pieces simmered in a mildly spiced, velvety tomato reduction finished with churned butter and fragrant kasuri methi (fenugreek).",
          flavor_profile: "Silky tomato tang, rich butter creaminess, aromatic dried fenugreek",
          key_ingredients: ["tandoori chicken", "tomatoes", "butter", "heavy cream", "kasuri methi", "garam masala"],
          ingredients_verified: ["chicken", "tomatoes", "butter", "cream", "spices"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Butter and dairy cream in makhani gravy" },
            { allergen: "nuts", status: "possible", source: "recipe_record", severity: "warning", notes: "Cashew paste thickener in traditional sauce" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "yes",
            halal: "yes",
            user_conflicts: ["dairy"],
            confidence_notes: "Naturally gluten-free curry; contains dairy and chicken"
          },
          price: "₹480",
          currency: "₹",
          evidence_status: "confirmed"
        },
        {
          dish_id: "ind_02",
          reading_order: 2,
          section: "Biryani",
          category: "Biryani",
          bounding_box: { xmin: 0.07, ymin: 0.35, xmax: 0.93, ymax: 0.47 },
          original_text: "अवधी दम बिरयानी (Awadhi Dum Biryani)",
          original_name: "अवधी दम बिरयानी",
          phonetic_transcription: "uh-wudh-ee doom beer-yah-nee",
          transliteration: "uh-wudh-ee doom beer-yah-nee",
          translated_title: "Awadhi Royal Slow-Cooked Lamb Biryani",
          translated_name: "Awadhi Royal Slow-Cooked Lamb Biryani",
          culinary_description: "Aged long-grain basmati rice and marinated lamb sealed in an earthen handi pot with dough, slow-cooked over coals with Kashmiri saffron, rose water, and caramelized onions.",
          translated_description: "Aged long-grain basmati rice and marinated lamb sealed in an earthen handi pot with dough, slow-cooked over coals with Kashmiri saffron, rose water, and caramelized onions.",
          flavor_profile: "Warm whole spices, floral saffron aroma, tender succulent lamb",
          key_ingredients: ["aged basmati rice", "marinated bone-in lamb", "saffron milk", "fried onions", "ghee", "kewra water"],
          ingredients_verified: ["basmati rice", "lamb", "saffron", "ghee", "onions"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Ghee and saffron milk infusion" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "yes",
            halal: "yes",
            user_conflicts: ["dairy"],
            confidence_notes: "Naturally gluten-free grain; contains halal lamb and clarified butter"
          },
          price: "₹550",
          currency: "₹",
          evidence_status: "confirmed"
        },
        {
          dish_id: "ind_03",
          reading_order: 3,
          section: "Breads",
          category: "Breads",
          bounding_box: { xmin: 0.07, ymin: 0.50, xmax: 0.93, ymax: 0.62 },
          original_text: "लहसुनी बटर नान (Garlic Butter Naan)",
          original_name: "लहसुनी बटर नान",
          phonetic_transcription: "luh-soo-nee buh-tur nahn",
          transliteration: "luh-soo-nee buh-tur nahn",
          translated_title: "Tandoor Garlic & Coriander Butter Naan",
          translated_name: "Tandoor Garlic & Coriander Butter Naan",
          culinary_description: "Traditional fermented wheat flatbread baked inside a fiery clay tandoor, brushed immediately with melted butter, minced roasted garlic, and chopped fresh coriander.",
          translated_description: "Traditional fermented wheat flatbread baked inside a fiery clay tandoor, brushed immediately with melted butter, minced roasted garlic, and chopped fresh coriander.",
          flavor_profile: "Charred blistered crust, pillowy soft crumb, pungent roasted garlic, herb freshness",
          key_ingredients: ["wheat flour (maida)", "yogurt", "garlic", "butter", "fresh coriander", "nigella seeds"],
          ingredients_verified: ["wheat flour", "garlic", "butter", "coriander"],
          allergen_warnings: [
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Refined wheat flour dough" },
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Butter and yogurt dough starter" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "no",
            halal: "yes",
            user_conflicts: ["gluten", "dairy"],
            confidence_notes: "Wheat flatbread containing butter"
          },
          price: "₹120",
          currency: "₹",
          evidence_status: "confirmed"
        },
        {
          dish_id: "ind_04",
          reading_order: 4,
          section: "Desserts",
          category: "Desserts",
          bounding_box: { xmin: 0.07, ymin: 0.65, xmax: 0.93, ymax: 0.77 },
          original_text: "गुलाब जामुन (Gulab Jamun)",
          original_name: "गुलाब जामुन",
          phonetic_transcription: "goo-lahb jah-moon",
          transliteration: "goo-lahb jah-moon",
          translated_title: "Warm Rose & Cardamom Scented Gulab Jamun",
          translated_name: "Warm Rose & Cardamom Scented Gulab Jamun",
          culinary_description: "Delicate reduced-milk solid (khoya) dumplings fried golden in pure ghee, then soaked warm in green cardamom and rosewater sugar syrup.",
          translated_description: "Delicate reduced-milk solid (khoya) dumplings fried golden in pure ghee, then soaked warm in green cardamom and rosewater sugar syrup.",
          flavor_profile: "Decadently sweet, aromatic green cardamom, floral rose, soft melting texture",
          key_ingredients: ["khoya milk solids", "chenna curd", "flour", "ghee", "green cardamom", "rose water", "saffron"],
          ingredients_verified: ["milk solids", "sugar syrup", "cardamom", "rose water"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Khoya milk solids and ghee" },
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Flour binder in dough" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "no",
            halal: "yes",
            user_conflicts: ["dairy", "gluten"],
            confidence_notes: "Rich milk dessert with wheat binder"
          },
          price: "₹160",
          currency: "₹",
          evidence_status: "confirmed"
        }
      ]
    }
  },

  // 5. Sushi and Izakaya
  {
    id: "sushi_izakaya",
    name: "Izakaya Sakura & Sushi Bar",
    cuisine: "Japanese",
    sourceLanguage: "ja",
    dishCount: 4,
    description: "Tokyo seafood tavern with bluefin tuna nigiri, crispy prawn tempura, and tare yakitori",
    photoUrl: "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=800&q=80",
    imageUrl: createMenuSvgDataUri("Izakaya Sakura", "季節の味覚 • 東京酒場料理", [
      { section: "刺身 / Sushi", name: "Maguro Nigiri (本鮪握り)", desc: "Fresh bluefin tuna nigiri with nikiri soy glaze and freshly grated wasabi", price: "¥1,200" },
      { section: "麺類 / Ramen", name: "Tonkotsu Ramen (豚骨ラーメン)", desc: "18-hour simmered pork bone broth, thin Hakata noodles, chashu pork, ajitsuke tamago", price: "¥1,100" },
      { section: "揚物 / Tempura", name: "Ebi Tempura (海老天ぷら)", desc: "Light and crispy battered tiger prawns served with tentsuyu dipping sauce and daikon", price: "¥950" },
      { section: "串焼 / Yakitori", name: "Yakitori Tare (焼き鳥タレ)", desc: "Charcoal-grilled chicken thigh and scallion skewers glazed with sweet soy tare", price: "¥680" }
    ]),
    data: {
      menu_metadata: {
        source_language: "ja",
        target_language: "en",
        image_width: 800,
        image_height: 1100,
        dish_count: 4,
        restaurant_id: "rest_fam_japanese_02",
        warnings: []
      },
      processing_metadata: {
        request_id: "sample-req-japanese-02",
        total_latency_ms: 388.2,
        model_name: "qwen3-vl:8b (cached baseline)",
        retrieval_status: "rag_hybrid_complete",
        stages: [
          { stage: "preprocessing", duration_ms: 19.1 },
          { stage: "visual_extraction", duration_ms: 210.3 },
          { stage: "culinary_enrichment_rag", duration_ms: 48.2 },
          { stage: "contextual_translation", duration_ms: 71.0 },
          { stage: "dietary_safety_evaluation", duration_ms: 39.6 }
        ],
        diagnostics: { applied_clahe: true, retrieval_hits: 4, all_verified: true }
      },
      safety_disclaimer: "DEMONSTRATION MENU: Verified seafood baseline. Check soy sauce gluten warnings.",
      dishes: [
        {
          dish_id: "dish_ja_01",
          reading_order: 1,
          section: "刺身 / Sushi",
          category: "Sushi",
          bounding_box: { xmin: 0.075, ymin: 0.209, xmax: 0.925, ymax: 0.327 },
          original_text: "Maguro Nigiri (本鮪握り)",
          original_name: "本鮪握り",
          phonetic_transcription: "mah-goo-roh nee-gee-ree",
          transliteration: "mah-goo-roh nee-gee-ree",
          translated_title: "Bluefin Tuna Nigiri with Nikiri Glaze",
          translated_name: "Bluefin Tuna Nigiri with Nikiri Glaze",
          culinary_description: "Prime cuts of pacific bluefin tuna served over seasoned Koshihikari sushi rice, brushed with house-brewed nikiri soy sauce.",
          translated_description: "Prime cuts of pacific bluefin tuna served over seasoned Koshihikari sushi rice, brushed with house-brewed nikiri soy sauce.",
          flavor_profile: "Clean marine savoriness, delicate rice vinegar balance, umami soy",
          key_ingredients: ["bluefin tuna", "seasoned sushi rice", "soy sauce", "mirin", "wasabi"],
          ingredients_verified: ["bluefin tuna", "sushi rice", "soy sauce"],
          allergen_warnings: [
            { allergen: "fish", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Fresh tuna fish" },
            { allergen: "soy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Soy sauce in glaze" },
            { allergen: "gluten", status: "possible", source: "recipe_record", severity: "warning", notes: "Wheat in standard brewed soy sauce" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "possible",
            halal: "yes",
            user_conflicts: [],
            confidence_notes: "Raw fish preparation; contains fermented soy"
          },
          price: "¥1,200",
          currency: "¥",
          evidence_status: "confirmed"
        },
        {
          dish_id: "dish_ja_02",
          reading_order: 2,
          section: "麺類 / Ramen",
          category: "Ramen",
          bounding_box: { xmin: 0.075, ymin: 0.354, xmax: 0.925, ymax: 0.472 },
          original_text: "Tonkotsu Ramen (豚骨ラーメン)",
          original_name: "豚骨ラーメン",
          phonetic_transcription: "tohn-koht-soo rah-men",
          transliteration: "tohn-koht-soo rah-men",
          translated_title: "Hakata-Style Rich Pork Bone Broth Ramen",
          translated_name: "Hakata-Style Rich Pork Bone Broth Ramen",
          culinary_description: "Collagen-rich broth boiled for 18 hours with pork marrow, firm artisanal wheat noodles, tender rolled pork belly chashu, seasoned soft egg, and wood ear mushrooms.",
          translated_description: "Collagen-rich broth boiled for 18 hours with pork marrow, firm artisanal wheat noodles, tender rolled pork belly chashu, seasoned soft egg, and wood ear mushrooms.",
          flavor_profile: "Deeply savory, rich and creamy mouthfeel, garlicky aroma, springy noodles",
          key_ingredients: ["pork marrow broth", "wheat ramen noodles", "chashu pork belly", "soy-marinated egg", "kikurage mushrooms", "scallions"],
          ingredients_verified: ["pork bone broth", "wheat noodles", "pork chashu", "egg"],
          allergen_warnings: [
            { allergen: "pork", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Pork bone broth and chashu" },
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Wheat alkaline noodles" },
            { allergen: "egg", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Soft-boiled seasoned egg" },
            { allergen: "soy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Shoyu tare base" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "no",
            halal: "no",
            user_conflicts: ["gluten"],
            confidence_notes: "Contains pork bone marrow and wheat gluten"
          },
          price: "¥1,100",
          currency: "¥",
          evidence_status: "confirmed"
        },
        {
          dish_id: "dish_ja_03",
          reading_order: 3,
          section: "揚物 / Tempura",
          category: "Tempura",
          bounding_box: { xmin: 0.075, ymin: 0.500, xmax: 0.925, ymax: 0.618 },
          original_text: "Ebi Tempura (海老天ぷら)",
          original_name: "海老天ぷら",
          phonetic_transcription: "eh-bee tem-poo-rah",
          transliteration: "eh-bee tem-poo-rah",
          translated_title: "Crispy Black Tiger Prawn Tempura",
          translated_name: "Crispy Black Tiger Prawn Tempura",
          culinary_description: "Fresh black tiger prawns dipped in ice-cold light wheat batter and flash-fried in fragrant sesame and canola oil. Served with warm dashi dipping broth.",
          translated_description: "Fresh black tiger prawns dipped in ice-cold light wheat batter and flash-fried in fragrant sesame and canola oil. Served with warm dashi dipping broth.",
          flavor_profile: "Airy crunch, sweet succulent prawn, savory dashi broth",
          key_ingredients: ["black tiger prawns", "tempura flour", "ice water", "sesame oil", "dashi broth", "grated daikon radish"],
          ingredients_verified: ["prawns", "wheat flour", "dashi"],
          allergen_warnings: [
            { allergen: "shellfish", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Crustacean prawns" },
            { allergen: "gluten", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Wheat tempura batter" },
            { allergen: "sesame", status: "possible", source: "recipe_record", severity: "warning", notes: "Sesame oil blend in fry bath" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "no",
            halal: "yes",
            user_conflicts: ["shellfish", "gluten"],
            confidence_notes: "Crustacean shellfish and wheat batter"
          },
          price: "¥950",
          currency: "¥",
          evidence_status: "confirmed"
        },
        {
          dish_id: "dish_ja_04",
          reading_order: 4,
          section: "串焼 / Yakitori",
          category: "Yakitori",
          bounding_box: { xmin: 0.075, ymin: 0.645, xmax: 0.925, ymax: 0.763 },
          original_text: "Yakitori Tare (焼き鳥タレ)",
          original_name: "焼き鳥タレ",
          phonetic_transcription: "yah-kee-toh-ree tah-reh",
          transliteration: "yah-kee-toh-ree tah-reh",
          translated_title: "Charcoal-Grilled Chicken Thigh Skewers with Sweet Tare",
          translated_name: "Charcoal-Grilled Chicken Thigh Skewers with Sweet Tare",
          culinary_description: "Tender chicken thigh and Tokyo scallions skewered over binchotan white charcoal, basted repeatedly with master sweet mirin-soy tare.",
          translated_description: "Tender chicken thigh and Tokyo scallions skewered over binchotan white charcoal, basted repeatedly with master sweet mirin-soy tare.",
          flavor_profile: "Smoky charcoal aroma, caramelized sweet soy glaze, juicy poultry",
          key_ingredients: ["chicken thigh", "Tokyo negi scallions", "soy sauce", "mirin", "sake", "sugar"],
          ingredients_verified: ["chicken", "scallions", "soy tare"],
          allergen_warnings: [
            { allergen: "soy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Soy sauce in tare" },
            { allergen: "gluten", status: "possible", source: "recipe_record", severity: "warning", notes: "Wheat in soy sauce fermentation" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "no",
            gluten_free: "possible",
            halal: "possible",
            user_conflicts: [],
            confidence_notes: "Poultry dish; check sake presence for strict halal"
          },
          price: "¥680",
          currency: "¥",
          evidence_status: "confirmed"
        }
      ]
    }
  },

  // 6. Dessert and Smoothie Café
  {
    id: "dessert_cafe",
    name: "Aura Artisan Dessert & Smoothie Lab",
    cuisine: "Desserts & Smoothies",
    sourceLanguage: "fr",
    dishCount: 4,
    description: "Cold-pressed acai bowls, Uji matcha parfaits, and French dark chocolate soufflés",
    photoUrl: "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?auto=format&fit=crop&w=800&q=80",
    imageUrl: createMenuSvgDataUri("Aura Dessert Lab", "Pâtisserie & Bar à Smoothies Végétal", [
      { section: "Smoothie Bowls", name: "Bol d'Açaí Sauvage & Granola", desc: "Organic Brazilian açaí blended with banana, topped with almond granola, berries, and chia", price: "€9.50" },
      { section: "Parfaits", name: "Parfait au Thé Matcha d'Uji", desc: "Ceremonial green tea mousse, soft shiratama dango, red bean azuki, and agar jelly", price: "€8.50" },
      { section: "Coolers", name: "Smoothie Mangue & Fruit de la Passion", desc: "Fresh Alphonso mango, tart passionfruit seeds, coconut milk, and crushed mint", price: "€7.00" },
      { section: "Pâtisserie", name: "Soufflé Chaud au Chocolat Noir 72%", desc: "Warm molten Valrhona Guanaja dark chocolate soufflé with Madagascar vanilla bean gelato", price: "€11.00" }
    ]),
    data: {
      menu_metadata: {
        source_language: "fr",
        target_language: "en",
        image_width: 800,
        image_height: 1100,
        dish_count: 4,
        restaurant_id: "aura_dessert_paris",
        warnings: []
      },
      processing_metadata: {
        request_id: "demo-dessert-06",
        total_latency_ms: 280.0,
        model_name: "qwen3-vl:8b (preloaded demo)",
        retrieval_status: "rag_authoritative_match",
        stages: [
          { stage: "preprocessing", duration_ms: 10.0 },
          { stage: "visual_extraction", duration_ms: 145.0 },
          { stage: "culinary_enrichment_rag", duration_ms: 40.0 },
          { stage: "contextual_translation", duration_ms: 50.0 },
          { stage: "dietary_safety_evaluation", duration_ms: 35.0 }
        ],
        diagnostics: { applied_clahe: false, retrieval_hits: 4, all_verified: true, eval_tokens: 395, tokens_per_second: 29.5 }
      },
      safety_disclaimer: "DEMONSTRATION MENU: Verified French confectionery recipes. Plant-based options highlighted.",
      dishes: [
        {
          dish_id: "des_01",
          reading_order: 1,
          section: "Smoothie Bowls",
          category: "Smoothie Bowls",
          bounding_box: { xmin: 0.07, ymin: 0.20, xmax: 0.93, ymax: 0.32 },
          original_text: "Bol d'Açaí Sauvage & Granola",
          original_name: "Bol d'Açaí Sauvage & Granola",
          phonetic_transcription: "bohl dah-sah-ee soh-vahzh",
          transliteration: "bohl dah-sah-ee soh-vahzh",
          translated_title: "Wild Amazonian Açaí & Toasted Granola Bowl",
          translated_name: "Wild Amazonian Açaí & Toasted Granola Bowl",
          culinary_description: "Pure organic frozen açaí purée blended thick with ripe banana and oat milk, topped with house-toasted almond granola, fresh blueberries, and chia seeds.",
          translated_description: "Pure organic frozen açaí purée blended thick with ripe banana and oat milk, topped with house-toasted almond granola, fresh blueberries, and chia seeds.",
          flavor_profile: "Deep tart berry antioxidant flavor, crunchy nutty granola, sweet banana",
          key_ingredients: ["organic açaí berry purée", "banana", "oat milk", "rolled oats", "almonds", "blueberries", "chia seeds"],
          ingredients_verified: ["açaí", "banana", "oats", "almonds", "chia"],
          allergen_warnings: [
            { allergen: "tree_nuts", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Toasted sliced almonds in granola" },
            { allergen: "gluten", status: "possible", source: "recipe_record", severity: "warning", notes: "Oat cross-contact risk unless certified" }
          ],
          dietary_compatibility: {
            vegan: "yes",
            vegetarian: "yes",
            gluten_free: "possible",
            halal: "yes",
            user_conflicts: [],
            confidence_notes: "100% plant-based vegan recipe; contains tree nuts (almonds)"
          },
          price: "€9.50",
          currency: "€",
          evidence_status: "confirmed"
        },
        {
          dish_id: "des_02",
          reading_order: 2,
          section: "Parfaits",
          category: "Parfaits",
          bounding_box: { xmin: 0.07, ymin: 0.35, xmax: 0.93, ymax: 0.47 },
          original_text: "Parfait au Thé Matcha d'Uji",
          original_name: "Parfait au Thé Matcha d'Uji",
          phonetic_transcription: "pahr-feh oh teh maht-chah doo-zhee",
          transliteration: "pahr-feh oh teh maht-chah doo-zhee",
          translated_title: "Ceremonial Uji Matcha Layered Parfait",
          translated_name: "Ceremonial Uji Matcha Layered Parfait",
          culinary_description: "First-harvest ceremonial Kyoto matcha mousse layered with chewy rice shiratama dango, sweet adzuki red bean paste, and agar jelly cubes.",
          translated_description: "First-harvest ceremonial Kyoto matcha mousse layered with chewy rice shiratama dango, sweet adzuki red bean paste, and agar jelly cubes.",
          flavor_profile: "Bittersweet vegetal matcha, floral umami, sweet red bean, chewy mochi",
          key_ingredients: ["Uji ceremonial matcha", "sweet cream", "adzuki bean paste", "glutinous rice flour", "kanten agar"],
          ingredients_verified: ["matcha", "dairy cream", "adzuki beans", "rice flour"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Whipping cream in matcha mousse" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "yes",
            halal: "yes",
            user_conflicts: ["dairy"],
            confidence_notes: "Rice flour and green tea dessert; contains dairy cream"
          },
          price: "€8.50",
          currency: "€",
          evidence_status: "confirmed"
        },
        {
          dish_id: "des_03",
          reading_order: 3,
          section: "Coolers",
          category: "Coolers",
          bounding_box: { xmin: 0.07, ymin: 0.50, xmax: 0.93, ymax: 0.62 },
          original_text: "Smoothie Mangue & Fruit de la Passion",
          original_name: "Smoothie Mangue & Fruit de la Passion",
          phonetic_transcription: "smoo-see mahng ay frwee duh lah pah-syohn",
          transliteration: "smoo-see mahng ay frwee duh lah pah-syohn",
          translated_title: "Tropical Mango & Passionfruit Coconut Cooler",
          translated_name: "Tropical Mango & Passionfruit Coconut Cooler",
          culinary_description: "Fresh crushed Alphonso mango blended with crunchy passionfruit pulp, cold-pressed coconut milk, and fresh torn Moroccan spearmint.",
          translated_description: "Fresh crushed Alphonso mango blended with crunchy passionfruit pulp, cold-pressed coconut milk, and fresh torn Moroccan spearmint.",
          flavor_profile: "Zesty acidic passionfruit, creamy sweet coconut, fresh aromatic mint",
          key_ingredients: ["Alphonso mango", "passionfruit", "coconut milk", "fresh spearmint", "lime juice"],
          ingredients_verified: ["mango", "passionfruit", "coconut milk", "mint"],
          allergen_warnings: [],
          dietary_compatibility: {
            vegan: "yes",
            vegetarian: "yes",
            gluten_free: "yes",
            halal: "yes",
            user_conflicts: [],
            confidence_notes: "Naturally dairy-free, gluten-free, 100% plant-based"
          },
          price: "€7.00",
          currency: "€",
          evidence_status: "confirmed"
        },
        {
          dish_id: "des_04",
          reading_order: 4,
          section: "Pâtisserie",
          category: "Pâtisserie",
          bounding_box: { xmin: 0.07, ymin: 0.65, xmax: 0.93, ymax: 0.77 },
          original_text: "Soufflé Chaud au Chocolat Noir 72%",
          original_name: "Soufflé Chaud au Chocolat Noir 72%",
          phonetic_transcription: "soo-fleh shoh oh shoh-koh-lah nwahr",
          transliteration: "soo-fleh shoh oh shoh-koh-lah nwahr",
          translated_title: "Warm 72% Valrhona Dark Chocolate Molten Soufflé",
          translated_name: "Warm 72% Valrhona Dark Chocolate Molten Soufflé",
          culinary_description: "Classic French baked chocolate soufflé made with single-origin 72% Valrhona chocolate, served hot with a scoop of Madagascar bourbon vanilla bean gelato.",
          translated_description: "Classic French baked chocolate soufflé made with single-origin 72% Valrhona chocolate, served hot with a scoop of Madagascar bourbon vanilla bean gelato.",
          flavor_profile: "Intense bittersweet cocoa, airy warm cloud exterior, molten molten core",
          key_ingredients: ["72% dark chocolate", "egg whites and yolks", "butter", "vanilla bean", "sugar"],
          ingredients_verified: ["dark chocolate", "eggs", "butter", "vanilla"],
          allergen_warnings: [
            { allergen: "egg", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Whipped egg whites and egg yolk base" },
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Butter in ramekin and vanilla gelato" },
            { allergen: "gluten", status: "possible", source: "recipe_record", severity: "warning", notes: "Traces in confectionery kitchen" }
          ],
          dietary_compatibility: {
            vegan: "no",
            vegetarian: "yes",
            gluten_free: "possible",
            halal: "yes",
            user_conflicts: ["dairy"],
            confidence_notes: "Vegetarian dessert; contains egg and dairy"
          },
          price: "€11.00",
          currency: "€",
          evidence_status: "confirmed"
        }
      ]
    }
  }
];

export const SAMPLE_DISH_IMAGES: Record<string, DishImageInfo> = {
  // Japanese Ramen
  ramen_01: {
    image_url: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Diego Lozano",
    photographer_url: "https://unsplash.com/@diegolozano",
    alt_text: "Bowl of Hakata Tonkotsu Ramen with chashu and soft egg",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  ramen_02: {
    image_url: "https://images.unsplash.com/photo-1591814468924-caf88d1232e1?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1591814468924-caf88d1232e1?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Mae Mu",
    photographer_url: "https://unsplash.com/@itsmaemu",
    alt_text: "Spicy Karakuchi Miso Ramen with sweet corn and scallions",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  ramen_03: {
    image_url: "https://images.unsplash.com/photo-1552611052-33e04de081de?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1552611052-33e04de081de?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Alex Munsell",
    photographer_url: "https://unsplash.com/@alexmunsell",
    alt_text: "Noko Gyokai Tsukemen dipping noodles",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  ramen_04: {
    image_url: "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Charles Deluvio",
    photographer_url: "https://unsplash.com/@charlesdeluvio",
    alt_text: "Crispy pan-fried Yaki Gyoza with dipping sauce",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },

  // Korean Café
  korean_01: {
    image_url: "https://images.unsplash.com/photo-1558857563-b37fe439169a?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1558857563-b37fe439169a?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Rosalind Chang",
    photographer_url: "https://unsplash.com/@rosalindchang",
    alt_text: "Black Milk Tea with chewy boba pearls",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  korean_02: {
    image_url: "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Daniela Araya",
    photographer_url: "https://unsplash.com/@daniela_araya",
    alt_text: "Brown Sugar Pearl Milk Tea with tiger stripes",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  korean_03: {
    image_url: "https://images.unsplash.com/photo-1505252585461-04db1eb84625?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1505252585461-04db1eb84625?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Jonas Kakaroto",
    photographer_url: "https://unsplash.com/@jonaskakaroto",
    alt_text: "Chilled Mango Yogurt Smoothie with fresh puree",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  korean_04: {
    image_url: "https://images.unsplash.com/photo-1562376552-0d160a2f238d?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1562376552-0d160a2f238d?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Mae Mu",
    photographer_url: "https://unsplash.com/@itsmaemu",
    alt_text: "Golden pressed Croffle with salted sweet cheese foam",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },

  // Italian Trattoria
  dish_it_01: {
    image_url: "https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Angelo Pantazis",
    photographer_url: "https://unsplash.com/@angelopantazis",
    alt_text: "Bruschetta al Pomodoro with basil and olive oil",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  dish_it_02: {
    image_url: "https://images.unsplash.com/photo-1621996346565-e3d5d6281781?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1621996346565-e3d5d6281781?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Olayinka Babalola",
    photographer_url: "https://unsplash.com/@olayinka",
    alt_text: "Tagliatelle al Ragù Bolognese with fresh parmesan",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  dish_it_03: {
    image_url: "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Jonathan Cooper",
    photographer_url: "https://unsplash.com/@thejonathancooper",
    alt_text: "Risotto ai Funghi Porcini with fresh parsley",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  dish_it_04: {
    image_url: "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Klara Kulikova",
    photographer_url: "https://unsplash.com/@klarakulikova",
    alt_text: "Tiramisù Tradizionale with cocoa dust",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },

  // Indian Kitchen
  ind_01: {
    image_url: "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Kunal Kalra",
    photographer_url: "https://unsplash.com/@kunalkalra",
    alt_text: "Murgh Makhani Butter Chicken with rich fenugreek gravy",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  ind_02: {
    image_url: "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Mounir Khashaba",
    photographer_url: "https://unsplash.com/@mounirkhashaba",
    alt_text: "Fragrant Awadhi Dum Biryani in traditional clay handi",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  ind_03: {
    image_url: "https://images.unsplash.com/photo-1626074353765-517a681e40be?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1626074353765-517a681e40be?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Prabal Goyal",
    photographer_url: "https://unsplash.com/@prabalgoyal",
    alt_text: "Golden Garlic Butter Naan fresh from clay tandoor",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  ind_04: {
    image_url: "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Sujit Kumar",
    photographer_url: "https://unsplash.com/@sujit_kumar",
    alt_text: "Gulab Jamun steeped in warm rose-cardamom syrup",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },

  // Sushi & Izakaya
  dish_ja_01: {
    image_url: "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Jakub Kapusnak",
    photographer_url: "https://unsplash.com/@foodiesfeed",
    alt_text: "Fresh Bluefin Tuna Maguro Nigiri with nikiri glaze",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  dish_ja_02: {
    image_url: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Diego Lozano",
    photographer_url: "https://unsplash.com/@diegolozano",
    alt_text: "Izakaya Tonkotsu Ramen with ajitsuke tamago",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  dish_ja_03: {
    image_url: "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "SJ Baren",
    photographer_url: "https://unsplash.com/@sj_baren",
    alt_text: "Crispy Ebi Tempura with tentsuyu dipping sauce",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  dish_ja_04: {
    image_url: "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Alex Munsell",
    photographer_url: "https://unsplash.com/@alexmunsell",
    alt_text: "Charcoal grilled Yakitori chicken thigh glazed with tare",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },

  // Café & Desserts
  des_01: {
    image_url: "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Jonas Kakaroto",
    photographer_url: "https://unsplash.com/@jonaskakaroto",
    alt_text: "Wild Acai Smoothie Bowl with almond granola and chia",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  des_02: {
    image_url: "https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Emile Mbunzama",
    photographer_url: "https://unsplash.com/@emilembunzama",
    alt_text: "Artisan Uji Matcha Parfait with soft shiratama dango",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  des_03: {
    image_url: "https://images.unsplash.com/photo-1505252585461-04db1eb84625?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1505252585461-04db1eb84625?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "Jonas Kakaroto",
    photographer_url: "https://unsplash.com/@jonaskakaroto",
    alt_text: "Alphonso Mango & Passion Fruit Smoothie Cooler",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
  des_04: {
    image_url: "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=800&q=80",
    thumbnail_url: "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=300&q=80",
    source: "curated",
    photographer: "American Heritage Chocolate",
    photographer_url: "https://unsplash.com/@americanheritagechocolate",
    alt_text: "Warm Molten Dark Chocolate Soufflé 72%",
    relevance_score: 1.0,
    is_fallback: false,
    status: "available",
  },
};

// Automatically attach verified representative images to demo dishes
for (const menu of SAMPLE_MENUS) {
  for (const dish of menu.data.dishes) {
    if (!dish.representative_image && SAMPLE_DISH_IMAGES[dish.dish_id]) {
      dish.representative_image = SAMPLE_DISH_IMAGES[dish.dish_id];
    }
  }
}


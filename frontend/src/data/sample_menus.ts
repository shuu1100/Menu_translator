import { MenuAnalysisResponse } from "../types/menu";

// High-fidelity SVG menus encoded as data URIs for immediate offline testing
const createMenuSvgDataUri = (title: string, subtitle: string, items: { section: string; name: string; desc: string; price: string }[]) => {
  const itemsSvg = items.map((it, idx) => {
    const y = 260 + idx * 160;
    return `
      <g>
        <rect x="60" y="${y - 30}" width="680" height="130" rx="10" fill="#1e293b" fill-opacity="0.6" stroke="#334155" stroke-dasharray="2 2" />
        <text x="80" y="${y - 8}" font-family="sans-serif" font-size="13" font-weight="bold" fill="#38bdf8" letter-spacing="2">${it.section.toUpperCase()}</text>
        <text x="80" y="${y + 24}" font-family="serif" font-size="24" font-weight="bold" fill="#f8fafc">${it.name}</text>
        <text x="720" y="${y + 24}" font-family="sans-serif" font-size="22" font-weight="bold" fill="#fbbf24" text-anchor="end">${it.price}</text>
        <text x="80" y="${y + 60}" font-family="sans-serif" font-size="15" fill="#94a3b8">${it.desc}</text>
      </g>
    `;
  }).join("\n");

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1100" viewBox="0 0 800 1100">
    <defs>
      <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#090d16" />
        <stop offset="50%" stop-color="#0f172a" />
        <stop offset="100%" stop-color="#020617" />
      </linearGradient>
    </defs>
    <rect width="800" height="1100" fill="url(#bg)" />
    <rect x="25" y="25" width="750" height="1050" fill="none" stroke="#475569" stroke-width="2" rx="16" />
    <rect x="35" y="35" width="730" height="1030" fill="none" stroke="#334155" stroke-width="1" rx="12" />
    
    <!-- Header -->
    <text x="400" y="110" font-family="serif" font-size="40" font-weight="bold" fill="#ffffff" text-anchor="middle" letter-spacing="4">${title.toUpperCase()}</text>
    <text x="400" y="150" font-family="sans-serif" font-size="16" fill="#94a3b8" text-anchor="middle" letter-spacing="3">${subtitle}</text>
    <line x1="200" y1="180" x2="600" y2="180" stroke="#f59e0b" stroke-width="2" />
    <circle cx="400" cy="180" r="5" fill="#f59e0b" />

    <!-- Items -->
    ${itemsSvg}

    <!-- Footer -->
    <line x1="100" y1="1010" x2="700" y2="1010" stroke="#334155" stroke-width="1" />
    <text x="400" y="1045" font-family="sans-serif" font-size="12" fill="#64748b" text-anchor="middle">
      Tutti i prezzi sono espressi in Euro • Coperto e servizio inclusi
    </text>
  </svg>`;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};

export interface SampleMenuOption {
  id: string;
  name: string;
  cuisine: string;
  description: string;
  imageUrl: string;
  data: MenuAnalysisResponse;
}

export const SAMPLE_MENUS: SampleMenuOption[] = [
  {
    id: "italian_trattoria",
    name: "Trattoria del Corso (Italian)",
    cuisine: "Italian",
    description: "Classic Roman trattoria with antipasti, handmade pasta, and dolci",
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
      safety_disclaimer: "CRITICAL SAFETY NOTICE: Allergen absence is NOT proof of safety. Always confirm with staff for life-threatening allergies.",
      dishes: [
        {
          dish_id: "dish_it_01",
          reading_order: 1,
          section: "Antipasti",
          bounding_box: { xmin: 0.075, ymin: 0.209, xmax: 0.925, ymax: 0.327 },
          original_text: "Bruschetta al Pomodoro",
          phonetic_transcription: "broo-SKET-tah ahl poh-moh-DOH-roh",
          translated_title: "Heirloom Tomato & Garlic Bruschetta",
          culinary_description: "Toasted artisanal sourdough rubbed with fresh garlic, topped with ripe datterini tomatoes, basil, and extra virgin olive oil.",
          flavor_profile: "Crisp, aromatic garlic, sweet acidic tomato, fruity olive oil",
          key_ingredients: ["sourdough bread", "datterini tomatoes", "garlic", "fresh basil", "extra virgin olive oil"],
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
          bounding_box: { xmin: 0.075, ymin: 0.354, xmax: 0.925, ymax: 0.472 },
          original_text: "Tagliatelle al Ragù Bolognese",
          phonetic_transcription: "tah-lyah-TEL-leh ahl rah-GOO",
          translated_title: "Handmade Tagliatelle with Slow-Cooked Bolognese Ragù",
          culinary_description: "Classic egg ribbon pasta served with traditional Emilia-Romagna meat sauce simmered with beef, pork, white wine, and milk, finished with Parmigiano Reggiano.",
          flavor_profile: "Deep umami, rich savory meat, velvety butter and aged cheese",
          key_ingredients: ["fresh egg pasta", "ground beef", "ground pork", "celery", "carrots", "onion", "milk", "Parmigiano Reggiano"],
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
          bounding_box: { xmin: 0.075, ymin: 0.500, xmax: 0.925, ymax: 0.618 },
          original_text: "Risotto ai Funghi Porcini",
          phonetic_transcription: "ree-ZOHT-toh eye FOON-gee por-CHEE-nee",
          translated_title: "Carnaroli Risotto with Wild Porcini Mushrooms",
          culinary_description: "Slow-stirred creamy Carnaroli rice infused with wild porcini mushrooms, vegetable broth, butter, and chopped Italian parsley.",
          flavor_profile: "Earthy, velvety texture, rich fungal savoriness, aromatic herbs",
          key_ingredients: ["Carnaroli rice", "porcini mushrooms", "vegetable stock", "butter", "shallots", "parsley"],
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
          bounding_box: { xmin: 0.075, ymin: 0.645, xmax: 0.925, ymax: 0.763 },
          original_text: "Tiramisù Tradizionale",
          phonetic_transcription: "tee-rah-mee-SOO trah-deet-syo-NAH-leh",
          translated_title: "Traditional Espresso & Mascarpone Tiramisù",
          culinary_description: "Iconic Venetian dessert layered with espresso-dipped ladyfingers and whipped egg-yolk mascarpone cream, dusted with dark cocoa.",
          flavor_profile: "Bittersweet espresso, lush mascarpone, pillowy texture, cocoa finish",
          key_ingredients: ["savoiardi ladyfingers", "espresso coffee", "mascarpone cheese", "eggs", "sugar", "unsweetened cocoa"],
          allergen_warnings: [
            { allergen: "dairy", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Mascarpone cheese" },
            { allergen: "egg", status: "confirmed", source: "recipe_record", severity: "critical", notes: "Raw or pasteurized egg yolks and whites" },
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
  {
    id: "japanese_izakaya",
    name: "Izakaya Sakura (Japanese)",
    cuisine: "Japanese",
    description: "Authentic Tokyo pub menu with ramen, tempura, and yakitori skewers",
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
      safety_disclaimer: "CRITICAL SAFETY NOTICE: Allergen absence is NOT proof of safety. Always confirm with staff for life-threatening allergies.",
      dishes: [
        {
          dish_id: "dish_ja_01",
          reading_order: 1,
          section: "刺身 / Sushi",
          bounding_box: { xmin: 0.075, ymin: 0.209, xmax: 0.925, ymax: 0.327 },
          original_text: "Maguro Nigiri (本鮪握り)",
          phonetic_transcription: "mah-goo-roh nee-gee-ree",
          translated_title: "Bluefin Tuna Nigiri with Nikiri Glaze",
          culinary_description: "Prime cuts of pacific bluefin tuna served over seasoned Koshihikari sushi rice, brushed with house-brewed nikiri soy sauce.",
          flavor_profile: "Clean marine savoriness, delicate rice vinegar balance, umami soy",
          key_ingredients: ["bluefin tuna", "seasoned sushi rice", "soy sauce", "mirin", "wasabi"],
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
          bounding_box: { xmin: 0.075, ymin: 0.354, xmax: 0.925, ymax: 0.472 },
          original_text: "Tonkotsu Ramen (豚骨ラーメン)",
          phonetic_transcription: "tohn-koht-soo rah-men",
          translated_title: "Hakata-Style Rich Pork Bone Broth Ramen",
          culinary_description: "Collagen-rich broth boiled for 18 hours with pork marrow, firm artisanal wheat noodles, tender rolled pork belly chashu, seasoned soft egg, and wood ear mushrooms.",
          flavor_profile: "Deeply savory, rich and creamy mouthfeel, garlicky aroma, springy noodles",
          key_ingredients: ["pork marrow broth", "wheat ramen noodles", "chashu pork belly", "soy-marinated egg", "kikurage mushrooms", "scallions"],
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
          bounding_box: { xmin: 0.075, ymin: 0.500, xmax: 0.925, ymax: 0.618 },
          original_text: "Ebi Tempura (海老天ぷら)",
          phonetic_transcription: "eh-bee tem-poo-rah",
          translated_title: "Crispy Black Tiger Prawn Tempura",
          culinary_description: "Fresh black tiger prawns dipped in ice-cold light wheat batter and flash-fried in fragrant sesame and canola oil. Served with warm dashi dipping broth.",
          flavor_profile: "Airy crunch, sweet succulent prawn, savory dashi broth",
          key_ingredients: ["black tiger prawns", "tempura flour", "ice water", "sesame oil", "dashi broth", "grated daikon radish"],
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
          bounding_box: { xmin: 0.075, ymin: 0.645, xmax: 0.925, ymax: 0.763 },
          original_text: "Yakitori Tare (焼き鳥タレ)",
          phonetic_transcription: "yah-kee-toh-ree tah-reh",
          translated_title: "Charcoal-Grilled Chicken Thigh Skewers with Sweet Tare",
          culinary_description: "Tender chicken thigh and Tokyo scallions skewered over binchotan white charcoal, basted repeatedly with master sweet mirin-soy tare.",
          flavor_profile: "Smoky charcoal aroma, caramelized sweet soy glaze, juicy poultry",
          key_ingredients: ["chicken thigh", "Tokyo negi scallions", "soy sauce", "mirin", "sake", "sugar"],
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
  }
];

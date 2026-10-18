/**
 * TypeScript types for Menu Translator matching backend Pydantic contracts.
 */

export type SupportedLanguage =
  | "en"
  | "es"
  | "fr"
  | "de"
  | "ja"
  | "zh"
  | "ar"
  | "it"
  | "pt"
  | "ko"
  | "hi"
  | "ru"
  | "zh-CN";

export type EvidenceStatus =
  | "confirmed"
  | "possible"
  | "unverified"
  | "not_listed"
  | "unknown";

export type DietaryFlagStatus = "yes" | "no" | "possible" | "unknown";

export interface BoundingBox {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
  pixel_x?: number;
  pixel_y?: number;
  pixel_width?: number;
  pixel_height?: number;
}

export interface DietaryCompatibility {
  vegan: DietaryFlagStatus;
  vegetarian: DietaryFlagStatus;
  gluten_free: DietaryFlagStatus;
  halal: DietaryFlagStatus;
  user_conflicts: string[];
  confidence_notes?: string;
}

export interface AllergenWarning {
  allergen: string;
  status: EvidenceStatus;
  source: string;
  notes?: string;
  icon?: string;
  severity: "critical" | "warning" | "advisory" | string;
}

export interface AnalyzedDish {
  dish_id: string;
  id?: string | null;
  reading_order: number;
  section?: string | null;
  category?: string | null;
  section_original?: string | null;
  section_translated?: string | null;
  bounding_box: BoundingBox;
  original_text: string;
  original_name?: string | null;
  original_description?: string | null;
  phonetic_transcription?: string | null;
  transliteration?: string | null;
  translated_title: string;
  translated_name?: string | null;
  culinary_description?: string | null;
  translated_description?: string | null;
  generated_description?: string | null;
  tags?: string[];
  flavor_profile?: string | null;
  price?: string | null;
  price_text_original?: string | null;
  price_value?: number | null;
  currency?: string | null;
  price_currency?: string | null;
  key_ingredients: string[];
  ingredients_original?: string[];
  ingredients_translated?: string[];
  ingredients_verified?: string[];
  ingredient_evidence_status?: EvidenceStatus;
  allergen_warnings: AllergenWarning[];
  allergens?: AllergenWarning[];
  nutrition?: Record<string, unknown> | null;
  dietary_compatibility: DietaryCompatibility;
  dietary_evidence?: Record<string, string>;
  confidence?: number | null;
  source_evidence?: string | null;
  evidence_status: EvidenceStatus;
  representative_image?: DishImageInfo | null;
}

export interface DishImageInfo {
  image_url: string;
  thumbnail_url?: string | null;
  source: string;
  photographer?: string | null;
  photographer_url?: string | null;
  source_url?: string | null;
  alt_text: string;
  relevance_score: number;
  is_fallback: boolean;
  status: "available" | "unavailable" | "error" | "loading";
  query_used?: string | null;
  dish_category?: string | null;
  photo_id?: string | null;
}

export interface StageTiming {
  stage: string;
  duration_ms: number;
  request_id?: string | null;
}

export interface ExtractionWarning {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface MenuMetadata {
  source_language?: string | null;
  target_language: SupportedLanguage;
  image_width: number;
  image_height: number;
  dish_count: number;
  restaurant_id?: string | null;
  warnings?: ExtractionWarning[];
}

export interface ProcessingMetadata {
  request_id: string;
  total_latency_ms: number;
  model_name: string;
  retrieval_status: string;
  stages: StageTiming[];
  diagnostics?: Record<string, unknown>;
}

export interface MenuAnalysisResponse {
  menu_metadata: MenuMetadata;
  dishes: AnalyzedDish[];
  processing_metadata: ProcessingMetadata;
  safety_disclaimer: string;
}

export interface DietaryFilterState {
  restrictions: string[]; // e.g., ["gluten", "dairy", "vegan", "vegetarian", "peanuts", "shellfish"]
}

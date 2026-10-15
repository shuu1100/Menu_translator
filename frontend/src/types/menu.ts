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
  | "ko";

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
  reading_order: number;
  section?: string | null;
  bounding_box: BoundingBox;
  original_text: string;
  phonetic_transcription?: string | null;
  translated_title: string;
  culinary_description?: string | null;
  flavor_profile?: string | null;
  key_ingredients: string[];
  allergen_warnings: AllergenWarning[];
  dietary_compatibility: DietaryCompatibility;
  price?: string | null;
  currency?: string | null;
  evidence_status: EvidenceStatus;
}

export interface StageTiming {
  stage: string;
  duration_ms: number;
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

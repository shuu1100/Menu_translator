# Dataset Card & Culinary Data License Inventory

## Overview
This document inventories the public and synthetic culinary datasets evaluated for the Menu Translator project, detailing licensing, provenance, fields, linguistic coverage, and safety boundaries.

---

## 1. Public Source Inventory

| Dataset Name | Source / Repository | Primary License | Modality & Coverage | Project Suitability & Safety Boundaries |
| :--- | :--- | :--- | :--- | :--- |
| **`worldcuisines/food-kb`** | Hugging Face (`worldcuisines/food-kb`) | CC BY-SA 4.0 | Textual knowledge graph of dishes, culinary regions, and ingredients across 20+ languages. | **Suitable for culinary RAG reference**. Contains regional food taxonomy, but ingredients are crowdsourced and must not be treated as certified allergen guarantees. |
| **`latimal/foodeval`** | Hugging Face (`latimal/foodeval`) | MIT | Visual restaurant menu images, layout annotations, dish bounding boxes. | **Suitable for layout extraction evaluation**. Provides real-world menu structures, multi-column designs, and price association pairs. |
| **`PaulineSanchez/Dataset_food_translation_fr_en`** | Hugging Face (`PaulineSanchez/...`) | Open Data Commons (ODC-By) | Parallel bilingual French-English menu dish titles and descriptions. | **Suitable for translation validation**. Grounded pairs for culinary terminology and French gastronomic loanword preservation. |
| **`ethz/food101`** | ETH Zurich / Vision Lab | Open Access (Research) | 101,000 plated food photographs across 101 dish categories. | **Category classification only**. Contains no printed menu OCR, no ingredient recipes, and **NO ALLERGEN LABELS**. Strictly prohibited from inferring allergen truth. |

---

## 2. Safety Boundaries & Non-Negotiable Rules

> [!CAUTION]
> **FOOD IMAGE CLASSIFICATION IS NOT AN ALLERGEN AUTHORITY**  
> Visual classification datasets (such as Food-101) depict cooked meals, not ingredient formulations. A photograph of soup or a baked pastry cannot reveal whether wheat flour, hidden peanut oil, or dairy butter was used in preparation. Allergen presence must only be confirmed through verified recipe formulations or explicit restaurant disclosures.

1. **Absence is not proof of safety**: If a dataset does not list an allergen for a dish, it is flagged as `not_listed` or `unknown`, never `allergen-free`.
2. **Human Review for Ground Truth**: Factual recipe entries and allergen profiles in test sets must be human-reviewed; synthetic or model-generated labels are considered weak supervision.
3. **No Private Leakage**: Private restaurant recipes (such as proprietary house broths) must never be redistributed in public training corpora.

---

## 3. Synthetic Multilingual Menu Dataset (`mt-synth-v1`)

To evaluate visual layout extraction, OCR precision, and price association across diverse typographic conditions without copyright infringement, Menu Translator generates a synthetic ground-truth corpus.

### Specification & Schema
- **Image Dimensions**: $1200 \times 1600$ px (high-resolution render)
- **Typographic Variations**: Single-column, dual-column, and decorative framed layouts.
- **Lighting & Quality Conditions**:
  - `clear`: High contrast, white background.
  - `decorative`: Vintage paper texture, ornamental borders.
  - `low_light`: Simulates ambient restaurant candle/dim lighting.
  - `noisy`: Simulates high-ISO camera sensor noise and compression artifacts.
- **Linguistic Coverage**: Italian, Japanese (Kanji/Katakana), Mexican Spanish, Levantine Arabic, French, and English.
- **Annotated Ground Truth Fields**:
  - `dish_id`: Unique identifier.
  - `original_name`: Verbatim printed dish name.
  - `box_2d`: Normalized bounding box $[ymin, xmin, ymax, xmax]$ in range $[0.0, 1.0]$.
  - `pixel_box`: Pixel bounding box $[xmin, ymin, xmax, ymax]$.
  - `reading_order`: 1-indexed document reading sequence.
  - `price_display` & `currency`: Extracted price and currency symbol.
  - `translated_title`: Contextual human-reviewed translation.
  - `ingredients`: Explicitly listed ingredients.
  - `allergen_evidence`: Structured allergen disclosures (`contains`, `may_contain`, `unknown`).
  - `provenance`: Originating menu generator configuration.

---

## 4. Train / Validation / Test Splitting Strategy

- **Split Ratio**: 70% Train, 15% Validation, 15% Test.
- **Isolation by Restaurant & Menu Family**:
  - Entire menus and restaurant families are assigned to exactly one split.
  - No random crop splitting to prevent visual and content leakage between training and testing sets.
- **Frozen Test Set**:
  - The 15% test set is permanently frozen and version-pinned in `data/training/dataset_manifest.json`.
  - Hyperparameter tuning and prompt engineering must never touch the test split.
- **Stress-Test Subset**:
  - Dedicated stress tests for low-light degradation, high noise, rare unicode scripts, and dishes with undisclosed secret sauces.

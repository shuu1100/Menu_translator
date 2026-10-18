# Phase 6 Prompt --- Dataset Engineering, Evaluation, and Optional QLoRA Fine-Tuning

Build the data and evaluation pipeline first. Fine-tuning is optional
and must only proceed after a baseline is measured. Do not fine-tune
merely to make the project appear more advanced.

## Dataset sources to investigate

The design document names: - `worldcuisines/food-kb` for multilingual
culinary knowledge records - `latimal/foodeval` for restaurant menu
structures - `PaulineSanchez/Dataset_food_translation_fr_en` for
French-English culinary translation pairs - `ethz/food101` for
dish-image classification (useful for visual category context, not menu
OCR ground truth) Verify each dataset's current availability, license,
fields, language coverage, and redistribution terms before using it.
These datasets do not automatically provide aligned menu-image bounding
boxes, reliable ingredient recipes, or allergen labels. Never infer
allergen truth from a food image classification dataset.

## Data plan

1.  Build a dataset card and source/license inventory.
2.  Curate menu photos or permitted public samples with ground-truth
    transcription and bounding boxes.
3.  Create approximately 3,000 synthetic image-text examples as a target
    only if time/resources permit. Synthetic images should include
    varied columns, fonts, prices, lighting, scripts, and menu
    decorations. Clearly label synthetic data.
4.  Ground-truth fields: source text, dish bounding box, reading order,
    price association, target-language translation, contextual
    description, ingredients, allergen evidence/status, and provenance.
5.  Human-review culturally specific translations and any
    recipe/allergen labels. Synthetic model-generated labels are weak
    supervision, not truth.
6.  Deduplicate by image, near-duplicate crop, menu source, and
    normalized text before splitting.

## Train/validation/test split

-   Split by source menu/restaurant and image family, not random crops,
    to prevent leakage.
-   Initial target: 70% train, 15% validation, 15% test, adjusted for
    dataset size and language coverage.
-   Keep the test set frozen and never use it to tune prompts or
    hyperparameters.
-   Add a small stress-test suite for low light, skew, small text,
    multiple columns, rare scripts, and unknown dishes.
-   Fix random seeds and write a manifest with source IDs, split,
    license, and label version.

## Baseline metrics

Visual extraction: CER, WER, dish-title exact match, price association
accuracy, reading-order accuracy, bounding-box IoU, JSON-validity rate,
latency, peak memory. Translation: human adequacy/context rating,
terminology consistency, factuality, native-name preservation,
target-language quality. RAG: Recall@k, MRR/nDCG if labels exist,
exact/alias match accuracy, cross-restaurant leakage rate. Safety:
allergen evidence precision/recall on verified records, unknown
handling, false-safe rate (must be tracked prominently). System:
end-to-end success rate, p50/p95 latency, CPU/RAM/VRAM use, offline
behavior.

## Optional QLoRA

Only after baseline: - Candidate: Qwen2.5-VL-3B/7B or a compatible
Qwen3-VL variant with documented vision fine-tuning support. Confirm
exact Unsloth support, model license, GPU memory, and recipe before
training. - Framework: Unsloth + Transformers + PEFT + TRL +
bitsandbytes, using QLoRA 4-bit NF4 where supported. - Format:
ChatML-style instruction samples with image input and target structured
JSON; follow the exact model's required multimodal chat template. -
Start conservatively: LoRA rank 16, alpha 16, dropout 0, learning rate
around 1e-4 to 2e-4 for a short pilot, warmup about 5%, cosine schedule,
AdamW 8-bit if compatible, micro-batch 1--2, gradient accumulation to
reach a manageable effective batch. Treat these as starting values, not
guaranteed optimal settings. - Train only on training split; evaluate
each checkpoint on validation; choose checkpoint by predeclared metrics;
run frozen test only once for final comparison. - Save adapter,
tokenizer/processor config, dataset manifest, hyperparameters, code
revision, metrics, and license notes. - Compare base vs adapter with
paired test examples. Roll back if extraction, multilingual quality, or
safety worsens. - Do not claim training has happened if no GPU run and
saved artifacts exist.

## Acceptance criteria

-   Reproducible data preparation and split scripts.
-   Dataset license and provenance documented.
-   Baseline report exists before fine-tuning.
-   No leakage between train/validation/test.
-   Fine-tuning is optional and guarded by resource checks.
-   Model card states limitations, languages evaluated, and safety
    boundaries. Stop after Phase 6.

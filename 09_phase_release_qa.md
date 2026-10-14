# Phase 9 Prompt --- Final QA, Demo, Documentation, and Hacktoberfest Release

Prepare a reliable open-source submission. Do not add major features
during this phase unless they fix a blocker.

## QA matrix

Test: - Clear menu, low-light image, perspective tilt, multiple columns,
small font, non-Latin scripts, RTL Arabic, and decorative backgrounds. -
Dish with verified allergen, dish with uncertain sauce, unknown dish, no
database match, conflicting records, and user restrictions. - Model
unavailable, database unavailable, sqlite-vec unavailable, invalid
image, oversized upload, timeout, malformed JSON, and frontend network
loss. - Mobile layout, desktop layout, keyboard operation, screen-reader
status, zoom/resize coordinate alignment, and PWA installability. -
Restaurant data isolation and private recipe logging/storage checks.

## Release deliverables

-   README with screenshots/GIF placeholders, features, architecture,
    setup, local model setup, database setup, tests, known limitations,
    and contribution guide.
-   Architecture diagram in Mermaid or a static diagram source file.
-   `.env.example`; Docker Compose only if the team can support it
    without hiding model/runtime constraints.
-   API contract and sample request/response.
-   Dataset card, source licenses, training/evaluation methodology,
    model card, and reproducibility notes if fine-tuning occurred.
-   Clear distinction between synthetic demo data and verified culinary
    facts.
-   GitHub issue templates or contribution instructions if time permits.
-   `LICENSE` chosen deliberately after checking model and dataset
    licenses; code license does not override model/dataset terms.
-   Demo script: capture image → extract menu → retrieve culinary
    context → display translation → show uncertainty/allergen warning →
    demonstrate offline shell.

## Final report

Include: - Features actually implemented - Selected model and why, with
benchmark results - Dataset provenance and whether fine-tuning was
actually performed - Metrics for OCR/layout, translation, retrieval,
safety, latency, and resource use - Known failures and mitigations -
Installation/test commands - Privacy and safety limitations

## Acceptance criteria

-   Fresh clone can follow README and run the demo.
-   Automated tests pass, or known failures are listed precisely.
-   No secrets, private recipes, user photos, or model weights
    accidentally committed.
-   The release does not claim guaranteed allergy safety or universal
    offline AI.
-   Git status is reviewed and no unrelated user changes are discarded.

# Model Selection Quick Reference

## Recommended starting point

Try `qwen3-vl:8b` in Ollama first if your installed Ollama version
supports it and your machine has enough memory. It is a newer
vision-language family with explicit visual grounding and document/image
understanding. Benchmark it against the design document's `qwen2.5vl:7b`
and the smaller `qwen2.5vl:3b` or `qwen3-vl:4b` fallback. Official
Ollama catalog and model pages should be checked for current tags and
runtime requirements.

## Practical choices

-   **Quality-first local GPU:** Qwen3-VL 8B candidate; compare with
    Qwen2.5-VL 7B.
-   **Lower-memory machine:** Qwen3-VL 4B or Qwen2.5-VL 3B; measure
    image resolution and long-menu performance.
-   **CPU-only:** a small quantized model may run but could be slow;
    consider using the computer's GPU or a temporary evaluation machine
    before committing to CPU inference.
-   **Fine-tuning:** start with prompt engineering, JSON schema
    validation, and RAG. Only use Unsloth QLoRA after collecting a clean
    labeled dataset and establishing a baseline. Confirm that the exact
    VLM/version and image processor are supported by the chosen training
    library.
-   **Embeddings:** choose a multilingual embedding model and align the
    vector dimension with sqlite-vec schema. Do not use the VLM itself
    as a default embedding model without benchmarking.

## Ollama setup examples

Check the official Ollama model library for current tags:

``` bash
ollama pull qwen3-vl:8b
ollama run qwen3-vl:8b
```

Fallback example:

``` bash
ollama pull qwen2.5vl:3b
ollama run qwen2.5vl:3b
```

These commands are examples; tags and minimum Ollama versions can
change. Test image input using the exact installed model before
integrating it.

## Benchmark before choosing

Use the same fixed set of at least 100 representative menu images if
possible, including multi-column and multilingual examples. Compare: 1.
Dish-title CER/WER and exact match 2. Price association accuracy 3.
Bounding-box IoU and reading order 4. JSON-validity rate 5. Translation
quality reviewed by bilingual humans 6. RAG retrieval quality 7.
False-safe allergen rate and unknown handling 8. p50/p95 latency and
peak RAM/VRAM 9. Model size, license, and ease of local deployment

Pick the model with the best task-specific balance, not simply the
highest general benchmark score.

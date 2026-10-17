"""Ollama Vision Provider implementation for Qwen3-VL / Qwen2.5-VL extraction."""

import base64
import logging
import time
import uuid
from typing import Any, Dict, Optional
import httpx

from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import (
    ModelInferenceError,
    ModelServiceUnavailableError,
)
from backend.app.schemas.extraction import (
    ExtractionWarning,
    MenuExtractionResult,
)
from backend.app.services.image_processor import ImageProcessor
from backend.app.services.vision.json_parser import ModelJsonParser
from backend.app.services.vision.prompts import (
    MENU_EXTRACTION_SYSTEM_PROMPT,
    MENU_EXTRACTION_USER_PROMPT,
    REPAIR_JSON_PROMPT,
)
from backend.app.services.vision.provider import MenuVisionProvider

logger = logging.getLogger("menu_translator.ollama_provider")


class OllamaVisionProvider(MenuVisionProvider):
    """Integrates with locally running Ollama VLM instance."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.model_name = self.settings.vision_model
        self.timeout = float(self.settings.inference_timeout_seconds)

    async def check_health(self) -> bool:
        """Verify Ollama is reachable and model is available."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    return any(
                        m == self.model_name or m.startswith(f"{self.model_name}:")
                        for m in models
                    )
        except Exception:
            return False
        return False

    async def extract_menu(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        metadata: Optional[Dict[str, Any]] = None,
        apply_clahe: bool = False,
        rotation: int = 0,
        preprocessed: Optional[Any] = None,
    ) -> MenuExtractionResult:
        """
        Validate, preprocess, invoke Ollama VLM with image, and defensively parse response.
        """
        start_time = time.perf_counter()
        menu_id = (metadata or {}).get("menu_id") or str(uuid.uuid4())

        # 1. Image Validation & Preprocessing (reuse if orchestrator pre-computed)
        if preprocessed is None:
            pil_image = ImageProcessor.validate_and_decode(
                image_bytes=image_bytes,
                max_size_mb=self.settings.max_upload_size_mb,
                rotation=rotation,
            )
            preprocessed = ImageProcessor.preprocess_for_vlm(
                image=pil_image,
                max_dimension=self.settings.image_max_dimension,
                apply_clahe=apply_clahe,
            )

        # 2. Encode to base64 for API transport (never logged)
        b64_image = base64.b64encode(preprocessed.image_bytes).decode("utf-8")

        # 3. Call Ollama Chat API with keep_alive, assistant prefill, and bounded context
        chat_url = f"{self.base_url}/api/chat"
        user_prompt = f"{MENU_EXTRACTION_SYSTEM_PROMPT}\n\n{MENU_EXTRACTION_USER_PROMPT}"
        prefill = '{\n  "source_language": "'
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt,
                    "images": [b64_image],
                },
                {
                    "role": "assistant",
                    "content": prefill,
                },
            ],
            "keep_alive": "30m",
            "options": {
                "temperature": 0.1,  # Low temperature for deterministic factual extraction
                "top_p": 0.9,
                "repeat_penalty": 1.15,
                "num_ctx": 3584,     # Sized for 100% GPU residency on 8GB VRAM (image tokens ~1200 + generation ~1000)
                "num_predict": 1000, # Bounded for fast, reliable extraction (<30s)
            },
            "stream": False,
        }

        raw_content = ""
        telemetry: Dict[str, Any] = {}
        t_inf_start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Sending extraction request to Ollama [{self.model_name}]...")
                response = await client.post(chat_url, json=payload)
                t_inf_end = time.perf_counter()

                if response.status_code != 200:
                    raise ModelInferenceError(
                        message=f"Ollama returned HTTP error {response.status_code}",
                        details={"status_code": response.status_code, "body": response.text[:200]},
                    )

                data = response.json()
                raw_content = data.get("message", {}).get("content", "")
                thinking = data.get("message", {}).get("thinking", "")
                if prefill and raw_content and not raw_content.lstrip().startswith("{"):
                    raw_content = prefill + raw_content

                if not raw_content or not raw_content.strip() or ("{" not in raw_content and "[" not in raw_content):
                    if thinking and ("{" in thinking or "items" in thinking):
                        cleaned_from_think = ModelJsonParser.clean_raw_output(thinking)
                        if "{" in cleaned_from_think or "[" in cleaned_from_think:
                            raw_content = cleaned_from_think
                        else:
                            raw_content = thinking
                    elif not raw_content:
                        raw_content = thinking or ""

                done_reason = data.get("done_reason", "unknown")
                eval_count = data.get("eval_count", 0)
                prompt_eval_count = data.get("prompt_eval_count", 0)
                load_duration_ns = data.get("load_duration", 0)
                eval_duration_ns = data.get("eval_duration", 0)
                prompt_eval_duration_ns = data.get("prompt_eval_duration", 0)
                inf_wall_ms = round((t_inf_end - t_inf_start) * 1000, 2)

                tok_s = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns > 0 else 0.0
                telemetry = {
                    "load_duration_ms": round(load_duration_ns / 1e6, 2),
                    "eval_duration_ms": round(eval_duration_ns / 1e6, 2),
                    "prompt_eval_duration_ms": round(prompt_eval_duration_ns / 1e6, 2),
                    "inference_wall_ms": inf_wall_ms,
                    "eval_tokens": eval_count,
                    "prompt_tokens": prompt_eval_count,
                    "tokens_per_second": round(tok_s, 2),
                    "done_reason": done_reason,
                    "model_residency": "warm_resident" if (load_duration_ns / 1e6) < 100 else "cold_loaded",
                }

                logger.info(
                    f"Ollama response received: content_len={len(raw_content)}, done_reason={done_reason}, "
                    f"eval_tokens={eval_count}, speed={tok_s:.1f} tok/s, inf_wall_ms={inf_wall_ms}"
                )
                if done_reason == "length":
                    logger.warning(f"VLM reached generation limit ({eval_count} tokens). Response may be truncated.")

        except httpx.ConnectError:
            raise ModelServiceUnavailableError(
                message=f"Could not connect to Ollama at {self.base_url}. Ensure 'ollama serve' is active."
            )
        except httpx.TimeoutException:
            raise ModelInferenceError(
                message=f"Model inference timed out after {self.timeout}s"
            )
        except Exception as e:
            if isinstance(e, (ModelInferenceError, ModelServiceUnavailableError)):
                raise
            raise ModelInferenceError(f"Unexpected inference communication error: {str(e)}")

        # 4. Parse JSON defensively, with 1 retry repair if invalid
        warnings: list[ExtractionWarning] = []
        if preprocessed.applied_clahe:
            warnings.append(
                ExtractionWarning(
                    code="CLAHE_ENHANCEMENT_APPLIED",
                    message="CLAHE adaptive histogram equalization applied to enhance text contrast",
                )
            )

        t_parse_start = time.perf_counter()
        try:
            source_lang, items, parse_warnings = ModelJsonParser.parse_and_validate(
                raw_output=raw_content,
                orig_width=preprocessed.original_width,
                orig_height=preprocessed.original_height,
            )
            warnings.extend(parse_warnings)
        except ModelInferenceError as initial_err:
            error_code = (initial_err.details or {}).get("code", "PARSE_ERROR")
            error_msg = f"{initial_err.message} ({error_code})"
            # Only attempt text-only repair if raw_content actually contains JSON markers
            if raw_content and ("{" in raw_content or "[" in raw_content) and len(raw_content.strip()) > 20:
                logger.warning(f"Extraction JSON invalid: {error_msg}. Triggering bounded repair prompt retry.")
                try:
                    repaired_content = await self._attempt_repair(raw_content, error_details=error_msg)
                    source_lang, items, parse_warnings = ModelJsonParser.parse_and_validate(
                        raw_output=repaired_content,
                        orig_width=preprocessed.original_width,
                        orig_height=preprocessed.original_height,
                    )
                    warnings.append(
                        ExtractionWarning(
                            code="REPAIR_RETRY_SUCCEEDED",
                            message="Recovered valid extraction JSON through secondary repair prompt",
                        )
                    )
                    warnings.extend(parse_warnings)
                except Exception as repair_err:
                    logger.warning(f"Repair retry failed: {repair_err}. Raising original error.")
                    raise initial_err
            else:
                logger.warning("Extraction returned empty or non-JSON output; skipping text repair to avoid hallucinated items.")
                raise initial_err

        t_parse_end = time.perf_counter()
        parsing_duration_ms = round((t_parse_end - t_parse_start) * 1000, 2)
        telemetry["parsing_duration_ms"] = parsing_duration_ms

        total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(f"Extraction successful: {len(items)} items extracted from '{source_lang}' menu in {total_latency_ms}ms")

        return MenuExtractionResult(
            menu_id=menu_id,
            source_language=source_lang,
            original_width=preprocessed.original_width,
            original_height=preprocessed.original_height,
            items=items,
            warnings=warnings,
            processing_time_ms=total_latency_ms,
            model_name=self.model_name,
            metadata=telemetry,
        )

    async def _attempt_repair(self, invalid_output: str, error_details: str = "Syntax or formatting error") -> str:
        """Attempt a single bounded repair round without images to fix malformed JSON syntax."""
        repair_url = f"{self.base_url}/api/chat"
        # Truncate invalid output to keep repair fast
        sample = invalid_output[:2000]
        prompt = (
            REPAIR_JSON_PROMPT
            .replace("{error_details}", error_details)
            .replace("{invalid_output}", sample)
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "keep_alive": "30m",
            "options": {
                "temperature": 0.0,
                "num_ctx": 4096,
                "num_predict": 1024,
            },
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(repair_url, json=payload)
                if res.status_code == 200:
                    repair_data = res.json()
                    repaired = repair_data.get("message", {}).get("content", "")
                    if not repaired or not repaired.strip():
                        thinking = repair_data.get("message", {}).get("thinking", "")
                        if "{" in thinking and ("items" in thinking or "source_language" in thinking):
                            repaired = thinking
                    return repaired or invalid_output
        except Exception as e:
            logger.error(f"Repair retry failed: {str(e)}")

        # If repair fails, return original to let parser raise diagnostic error
        return invalid_output

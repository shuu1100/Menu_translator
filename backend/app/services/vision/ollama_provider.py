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
    ) -> MenuExtractionResult:
        """
        Validate, preprocess, invoke Ollama VLM with image, and defensively parse response.
        """
        start_time = time.perf_counter()
        menu_id = (metadata or {}).get("menu_id") or str(uuid.uuid4())

        # 1. Image Validation & Preprocessing
        pil_image = ImageProcessor.validate_and_decode(
            image_bytes=image_bytes,
            max_size_mb=self.settings.max_upload_size_mb,
        )

        preprocessed = ImageProcessor.preprocess_for_vlm(
            image=pil_image,
            max_dimension=self.settings.image_max_dimension,
            apply_clahe=apply_clahe,
        )

        # 2. Encode to base64 for API transport (never logged)
        b64_image = base64.b64encode(preprocessed.image_bytes).decode("utf-8")

        # 3. Call Ollama Chat API
        chat_url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": MENU_EXTRACTION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": MENU_EXTRACTION_USER_PROMPT,
                    "images": [b64_image],
                },
            ],
            "options": {
                "temperature": 0.1,  # Low temperature for deterministic factual extraction
                "top_p": 0.9,
            },
            "stream": False,
        }

        raw_content = ""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Sending extraction request to Ollama [{self.model_name}]...")
                response = await client.post(chat_url, json=payload)

                if response.status_code != 200:
                    raise ModelInferenceError(
                        message=f"Ollama returned HTTP error {response.status_code}",
                        details={"status_code": response.status_code, "body": response.text[:200]},
                    )

                data = response.json()
                raw_content = data.get("message", {}).get("content", "")

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

        try:
            source_lang, items, parse_warnings = ModelJsonParser.parse_and_validate(
                raw_output=raw_content,
                orig_width=preprocessed.original_width,
                orig_height=preprocessed.original_height,
            )
            warnings.extend(parse_warnings)
        except ModelInferenceError as initial_err:
            logger.warning(f"Extraction JSON invalid. Triggering repair prompt retry: {initial_err.message}")
            repaired_content = await self._attempt_repair(raw_content)
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

        total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return MenuExtractionResult(
            menu_id=menu_id,
            source_language=source_lang,
            original_width=preprocessed.original_width,
            original_height=preprocessed.original_height,
            items=items,
            warnings=warnings,
            processing_time_ms=total_latency_ms,
            model_name=self.model_name,
        )

    async def _attempt_repair(self, invalid_output: str) -> str:
        """Attempt a single repair round without images to fix malformed JSON syntax."""
        repair_url = f"{self.base_url}/api/chat"
        # Truncate invalid output if unreasonably huge
        sample = invalid_output[:2500]
        prompt = REPAIR_JSON_PROMPT.replace("{invalid_output}", sample)

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.0},
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(repair_url, json=payload)
                if res.status_code == 200:
                    return res.json().get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Repair retry failed: {str(e)}")

        # If repair fails, return original to let parser raise diagnostic error
        return invalid_output

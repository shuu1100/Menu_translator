"""Menu analysis and ingestion API endpoints."""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import (
    AppException,
    InvalidImageError,
    ModelInferenceError,
    ModelServiceUnavailableError,
)
from backend.app.schemas.menu_analysis import (
    MenuAnalysisResponse,
    SupportedLanguage,
)
from backend.app.services.pipeline_orchestrator import MenuPipelineOrchestrator
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.app.services.vision.provider import MenuVisionProvider

router = APIRouter(prefix="/menus", tags=["Menus"])


def get_vision_provider(settings: Settings = Depends(get_settings)) -> MenuVisionProvider:
    return OllamaVisionProvider(settings=settings)


def get_pipeline_orchestrator(
    provider: MenuVisionProvider = Depends(get_vision_provider),
    settings: Settings = Depends(get_settings),
) -> MenuPipelineOrchestrator:
    return MenuPipelineOrchestrator(vision_provider=provider, settings=settings)


@router.post(
    "/analyze",
    response_model=MenuAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze restaurant menu photo",
    description=(
        "Full pipeline endpoint: Ingests menu photo, performs local visual extraction, "
        "enriches dish records, cross-checks dietary preferences, and returns structured dish data with bounding boxes."
    ),
    responses={
        400: {"description": "Invalid image payload or unsupported format"},
        413: {"description": "Payload exceeds maximum allowed size"},
        422: {"description": "Validation error in request parameters"},
        503: {"description": "Local AI model engine is unavailable"},
        504: {"description": "Model inference timed out"},
    },
)
async def analyze_menu(
    file: UploadFile = File(..., description="Menu photo (JPEG, PNG, WEBP)"),
    target_language: str = Form(
        default="en",
        description="Target language code (e.g. en, es, fr, de, ja, zh, ar, it)",
    ),
    user_dietary_restrictions: Optional[str] = Form(
        default=None,
        description="Optional comma-separated or JSON list of dietary restrictions (e.g. 'vegan, gluten-free')",
    ),
    restaurant_id: Optional[str] = Form(
        default=None,
        description="Optional restaurant ID for scoped knowledge retrieval",
    ),
    apply_clahe: bool = Form(
        default=False,
        description="Apply adaptive contrast equalization for dim restaurant lighting",
    ),
    orchestrator: MenuPipelineOrchestrator = Depends(get_pipeline_orchestrator),
    settings: Settings = Depends(get_settings),
) -> MenuAnalysisResponse:
    """Execute end-to-end menu analysis pipeline."""
    # 1. Validate Target Language Enum
    try:
        lang_enum = SupportedLanguage(target_language.lower().strip())
    except ValueError:
        valid_langs = [l.value for l in SupportedLanguage]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "UNSUPPORTED_LANGUAGE",
                "message": f"Unsupported target language '{target_language}'. Supported: {', '.join(valid_langs)}",
            },
        )

    # 2. Validate MIME type
    if not file.content_type or not any(file.content_type.startswith(m) for m in ["image/jpeg", "image/png", "image/webp"]):
        raise InvalidImageError(
            f"Unsupported file type '{file.content_type}'. Must be image/jpeg, image/png, or image/webp."
        )

    # 3. Read image bytes and enforce 413 Payload Too Large
    image_bytes = await file.read()
    if not image_bytes:
        raise InvalidImageError("Uploaded image payload is empty.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "PAYLOAD_TOO_LARGE",
                "message": f"File size exceeds maximum allowed upload of {settings.max_upload_size_mb}MB",
            },
        )

    # 4. Parse user dietary restrictions list
    restrictions_list: List[str] = []
    if user_dietary_restrictions:
        cleaned = user_dietary_restrictions.strip()
        if cleaned.startswith("[") and cleaned.endswith("]"):
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    restrictions_list = [str(x) for x in parsed]
            except Exception:
                restrictions_list = [r.strip() for r in cleaned.strip("[]").split(",") if r.strip()]
        else:
            restrictions_list = [r.strip() for r in cleaned.split(",") if r.strip()]

    # 5. Execute Pipeline with mapped exceptions
    try:
        response = await orchestrator.run_pipeline(
            image_bytes=image_bytes,
            mime_type=file.content_type,
            target_language=lang_enum,
            user_dietary_restrictions=restrictions_list,
            restaurant_id=restaurant_id,
            apply_clahe=apply_clahe,
        )
        return response
    except ModelServiceUnavailableError:
        raise
    except ModelInferenceError as err:
        if "timed out" in err.message.lower():
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={"code": "INFERENCE_TIMEOUT", "message": err.message},
            )
        raise
    except AppException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PIPELINE_ERROR", "message": f"Internal pipeline error: {str(e)}"},
        )

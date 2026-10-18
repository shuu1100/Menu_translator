import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import (
    AppException,
    InvalidImageError,
    ModelInferenceError,
    ModelServiceUnavailableError,
    ServerOverloadedError,
)
from backend.app.schemas.menu_analysis import (
    AnalyzedDish,
    MenuAnalysisResponse,
    RetranslateRequest,
    RetranslateResponse,
    SupportedLanguage,
)
from backend.app.services.pipeline_orchestrator import MenuPipelineOrchestrator
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.app.services.vision.provider import MenuVisionProvider

router = APIRouter(prefix="/menus", tags=["Menus"])

_pipeline_concurrency_lock = asyncio.Lock()
_pipeline_semaphore: Optional[asyncio.Semaphore] = None


async def get_pipeline_semaphore(settings: Settings) -> asyncio.Semaphore:
    """Return bounded concurrency semaphore singleton."""
    global _pipeline_semaphore
    if _pipeline_semaphore is None:
        async with _pipeline_concurrency_lock:
            if _pipeline_semaphore is None:
                _pipeline_semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
    return _pipeline_semaphore


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
    dietary_restrictions: Optional[str] = Form(
        default=None,
        description="Alias for user_dietary_restrictions",
    ),
    restaurant_id: Optional[str] = Form(
        default=None,
        description="Optional restaurant ID for scoped knowledge retrieval",
    ),
    apply_clahe: bool = Form(
        default=False,
        description="Apply adaptive contrast equalization for dim restaurant lighting",
    ),
    rotation: int = Form(
        default=0,
        description="Clockwise rotation in degrees (0, 90, 180, 270)",
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

    # 2. Read image bytes and enforce 413 Payload Too Large
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

    # 3. Validate image format (via MIME type, filename extension, or magic bytes)
    allowed_mimes = ["image/jpeg", "image/png", "image/webp", "image/mpo", "image/pjpeg", "image/jfif"]
    valid_exts = (".jpg", ".jpeg", ".png", ".webp", ".mpo", ".jfif")
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    has_valid_mime = any(content_type.startswith(m) for m in allowed_mimes)
    has_valid_ext = filename.endswith(valid_exts)
    has_valid_magic = (
        image_bytes.startswith(b"\xff\xd8\xff")  # JPEG
        or image_bytes.startswith(b"\x89PNG\r\n\x1a\n")  # PNG
        or (image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:16])  # WebP
    )

    if not (has_valid_mime or has_valid_ext or has_valid_magic):
        raise InvalidImageError(
            f"Unsupported file type '{content_type or filename or 'unknown'}'. Please upload a JPEG, PNG, or WebP photo."
        )

    canonical_mime = content_type if has_valid_mime else (
        "image/png" if image_bytes.startswith(b"\x89PNG") else
        "image/webp" if image_bytes.startswith(b"RIFF") else
        "image/jpeg"
    )

    # 4. Parse user dietary restrictions list
    raw_restrictions = user_dietary_restrictions or dietary_restrictions
    restrictions_list: List[str] = []
    if raw_restrictions:
        cleaned = raw_restrictions.strip()
        if cleaned.startswith("[") and cleaned.endswith("]"):
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    restrictions_list = [str(x) for x in parsed]
            except Exception:
                restrictions_list = [r.strip() for r in cleaned.strip("[]").split(",") if r.strip()]
        else:
            restrictions_list = [r.strip() for r in cleaned.split(",") if r.strip()]

    # 5. Acquire bounded concurrency semaphore to prevent overload
    sem = await get_pipeline_semaphore(settings)
    try:
        await asyncio.wait_for(sem.acquire(), timeout=5.0)
    except asyncio.TimeoutError:
        raise ServerOverloadedError(
            f"Server capacity reached ({settings.max_concurrent_requests} concurrent analysis jobs active). Please retry shortly."
        )

    # 6. Execute Pipeline with mapped exceptions and timeout
    try:
        response = await asyncio.wait_for(
            orchestrator.run_pipeline(
                image_bytes=image_bytes,
                mime_type=canonical_mime,
                target_language=lang_enum,
                user_dietary_restrictions=restrictions_list,
                restaurant_id=restaurant_id,
                apply_clahe=apply_clahe,
                rotation=rotation,
            ),
            timeout=float(settings.pipeline_timeout_seconds),
        )
        return response
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": "PIPELINE_TIMEOUT", "message": f"Pipeline execution exceeded {settings.pipeline_timeout_seconds}s limit."},
        )
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
    finally:
        sem.release()


@router.post(
    "/retranslate",
    response_model=RetranslateResponse,
    status_code=status.HTTP_200_OK,
    summary="Retranslate existing menu dishes to another language",
    description="Retranslates already-extracted dishes without re-uploading the image.",
)
async def retranslate_menu(
    payload: RetranslateRequest,
    orchestrator: MenuPipelineOrchestrator = Depends(get_pipeline_orchestrator),
) -> RetranslateResponse:
    """Retranslate dish items into a newly selected target language."""
    try:
        lang_enum = SupportedLanguage.from_code(payload.target_language)
    except ValueError:
        valid_langs = [l.value for l in SupportedLanguage]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "UNSUPPORTED_LANGUAGE",
                "message": f"Unsupported target language '{payload.target_language}'. Supported: {', '.join(valid_langs)}",
            },
        )

    # Always translate from original OCR / extracted dish text and description,
    # never from previously translated text to avoid compounding errors.
    batch_items = [
        {
            "original_name": dish.original_name or dish.original_text,
            "printed_desc": dish.original_description or "",
            "price": dish.price,
            "rag_record": None,
        }
        for dish in payload.dishes
    ]

    translations = await orchestrator.translator.translate_batch(
        items=batch_items,
        target_language=lang_enum,
    )

    updated_dishes: List[AnalyzedDish] = []
    for idx, dish in enumerate(payload.dishes):
        trans = translations[idx] if idx < len(translations) else None
        updated_dish = dish.model_copy()
        if trans:
            # Synchronize both title/name aliases
            updated_dish.translated_title = trans.translated_title
            updated_dish.translated_name = trans.translated_title

            if trans.phonetic_transcription:
                updated_dish.phonetic_transcription = trans.phonetic_transcription
                updated_dish.transliteration = trans.phonetic_transcription

            # Only provide a translated description if the dish had an authentic printed description
            if dish.original_description:
                desc = trans.culinary_description or dish.original_description
                updated_dish.culinary_description = desc
                updated_dish.translated_description = desc
            else:
                updated_dish.culinary_description = None
                updated_dish.translated_description = None

            if trans.flavor_profile:
                updated_dish.flavor_profile = trans.flavor_profile

        # Ensure original text remains completely untouched and image is preserved
        updated_dishes.append(updated_dish)

    return RetranslateResponse(
        dishes=updated_dishes,
        target_language=lang_enum.value,
    )

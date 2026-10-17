"""Menu extraction API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from backend.app.core.exceptions import InvalidImageError
from backend.app.schemas.extraction import MenuExtractionResult
from backend.app.services.vision.ollama_provider import OllamaVisionProvider
from backend.app.services.vision.provider import MenuVisionProvider

router = APIRouter(prefix="/extract", tags=["Extraction"])


def get_vision_provider() -> MenuVisionProvider:
    return OllamaVisionProvider()


@router.post(
    "",
    response_model=MenuExtractionResult,
    status_code=status.HTTP_200_OK,
    summary="Extract menu items and bounding boxes from an uploaded photo",
    description=(
        "Ingests a menu image, validates/preprocesses with OpenCV, invokes the local VLM (Qwen3-VL), "
        "and extracts structured dish blocks with normalized coordinates without generating allergen claims."
    ),
)
async def extract_menu_from_image(
    file: UploadFile = File(..., description="Menu photo (JPEG, PNG, WEBP)"),
    apply_clahe: bool = Form(
        default=False,
        description="Apply CLAHE adaptive contrast equalization (recommended for dim restaurant lighting)",
    ),
    provider: MenuVisionProvider = Depends(get_vision_provider),
) -> MenuExtractionResult:
    """Validate, preprocess, and extract menu text blocks."""
    allowed_mimes = ["image/jpeg", "image/png", "image/webp", "image/mpo", "image/pjpeg"]
    if not file.content_type or not any(file.content_type.startswith(p) for p in allowed_mimes):
        raise InvalidImageError(
            f"Unsupported file type '{file.content_type}'. Must be image/jpeg, image/png, image/webp, or image/mpo."
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise InvalidImageError("Uploaded file payload is empty.")

    result = await provider.extract_menu(
        image_bytes=image_bytes,
        mime_type=file.content_type,
        apply_clahe=apply_clahe,
    )
    return result

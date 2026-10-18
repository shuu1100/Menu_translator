"""UI Translation API Router for Universal Menu Translator.

Provides endpoints for on-demand UI text localization via DeepL.
Menu content translation remains strictly handled by the local vision/RAG pipeline.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.services.deepl_translator import get_deepl_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translate", tags=["UI Translation"])


class UiTranslationRequest(BaseModel):
    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of UI text strings to translate (max 50 strings)",
    )
    target_language: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Target ISO language code (e.g., es, fr, de, ja, ko, zh)",
    )
    source_language: Optional[str] = Field(
        default="en",
        description="Source ISO language code (default 'en')",
    )


class UiTranslationItem(BaseModel):
    original: str
    translated: str


class UiTranslationResponse(BaseModel):
    translations: List[UiTranslationItem]
    target_language: str
    provider: str


class TranslateStatusResponse(BaseModel):
    deepl_configured: bool
    deepl_endpoint: str
    supported_languages: List[str]


@router.get(
    "/status",
    response_model=TranslateStatusResponse,
    summary="Get UI Translation Service Status",
)
async def get_translation_status():
    """Return whether DeepL API is configured and which languages are supported."""
    service = get_deepl_service()
    return TranslateStatusResponse(
        deepl_configured=service.is_configured,
        deepl_endpoint=service.api_url,
        supported_languages=service.get_supported_target_languages(),
    )


@router.post(
    "/ui",
    response_model=UiTranslationResponse,
    summary="Translate Dynamic UI Strings",
)
async def translate_ui_strings(payload: UiTranslationRequest):
    """Translate a batch of UI text strings using DeepL.
    
    Strictly scoped to interface strings; menu dishes and OCR data are processed by local AI.
    """
    service = get_deepl_service()

    if not service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DeepL API is not configured on this server. Standard UI is available via local dictionaries.",
        )

    try:
        translated_texts = await service.translate_batch(
            texts=payload.texts,
            target_lang=payload.target_language,
            source_lang=payload.source_language,
        )

        items = [
            UiTranslationItem(original=orig, translated=trans)
            for orig, trans in zip(payload.texts, translated_texts)
        ]

        return UiTranslationResponse(
            translations=items,
            target_language=payload.target_language,
            provider="deepl",
        )

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except PermissionError as perm_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DeepL API authorization failed. Check configured DEEPL_API_KEY.",
        )
    except RuntimeError as run_err:
        err_msg = str(run_err)
        if "rate limit" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="DeepL API rate limit reached. Please retry later.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"DeepL translation error: {err_msg}",
        )

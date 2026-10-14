"""Config and reference metadata endpoints."""

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.schemas.menu_analysis import SupportedLanguage

router = APIRouter(prefix="/config", tags=["Configuration"])


class LanguageOption(BaseModel):
    code: str
    name: str


LANGUAGE_METADATA = [
    LanguageOption(code=SupportedLanguage.EN.value, name="English"),
    LanguageOption(code=SupportedLanguage.ES.value, name="Spanish (Español)"),
    LanguageOption(code=SupportedLanguage.FR.value, name="French (Français)"),
    LanguageOption(code=SupportedLanguage.DE.value, name="German (Deutsch)"),
    LanguageOption(code=SupportedLanguage.JA.value, name="Japanese (日本語)"),
    LanguageOption(code=SupportedLanguage.ZH.value, name="Chinese (中文)"),
    LanguageOption(code=SupportedLanguage.AR.value, name="Arabic (العربية)"),
    LanguageOption(code=SupportedLanguage.IT.value, name="Italian (Italiano)"),
    LanguageOption(code=SupportedLanguage.PT.value, name="Portuguese (Português)"),
    LanguageOption(code=SupportedLanguage.KO.value, name="Korean (한국어)"),
]


@router.get(
    "/languages",
    response_model=List[LanguageOption],
    summary="Get supported target languages",
    description="Returns the list of available target languages supported for menu translation.",
)
async def get_supported_languages() -> List[LanguageOption]:
    """Return supported target languages list."""
    return LANGUAGE_METADATA

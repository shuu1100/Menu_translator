"""DeepL Translation Service for UI Localization.

Provides secure server-side translation for website UI strings using DeepL's official API.
Preserves interpolation variables ({var}), applies caching, and guards credentials.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
import httpx

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)

# DeepL target language mapping (our ISO 639-1 code -> DeepL API uppercase code)
DEEPL_TARGET_LANGUAGE_MAP: Dict[str, str] = {
    "en": "EN-US",
    "es": "ES",
    "fr": "FR",
    "de": "DE",
    "it": "IT",
    "ja": "JA",
    "zh": "ZH",
    "ko": "KO",
    "pt": "PT-PT",
    "ru": "RU",
    "ar": "AR",
    # Add full variant mappings if passed
    "en-us": "EN-US",
    "en-gb": "EN-GB",
    "pt-br": "PT-BR",
    "zh-hans": "ZH",
}

# DeepL supported source languages
DEEPL_SOURCE_LANGUAGE_MAP: Dict[str, str] = {
    "en": "EN",
    "es": "ES",
    "fr": "FR",
    "de": "DE",
    "it": "IT",
    "ja": "JA",
    "zh": "ZH",
    "ko": "KO",
    "pt": "PT",
    "ru": "RU",
    "ar": "AR",
}

# Regex to match interpolation tokens like {count}, {language}, {rotation}
INTERPOLATION_PATTERN = re.compile(r"\{([a-zA-Z0-9_]+)\}")


class DeepLTranslationService:
    """Service for translating UI text strings using the official DeepL API."""

    def __init__(self):
        self.settings = get_settings()
        self._cache: Dict[Tuple[str, str], str] = {}  # (target_lang, original_text) -> translated_text

    @property
    def is_configured(self) -> bool:
        """Return True if a non-empty DeepL API key is present."""
        key = self.settings.deepl_api_key
        return bool(key and key.strip())

    @property
    def api_url(self) -> str:
        """Return the configured DeepL endpoint."""
        return self.settings.deepl_api_url.strip()

    def get_supported_target_languages(self) -> List[str]:
        """Return list of supported ISO codes."""
        return list(DEEPL_TARGET_LANGUAGE_MAP.keys())

    def _mask_key(self, key: Optional[str]) -> str:
        """Return masked key for safe diagnostic logging."""
        if not key or len(key) < 6:
            return "***"
        return f"{key[:2]}***{key[-4:]}"

    def _protect_placeholders(self, text: str) -> Tuple[str, List[str]]:
        """Wrap interpolation placeholders in XML tags to preserve them during translation."""
        placeholders: List[str] = []

        if not INTERPOLATION_PATTERN.search(text):
            return text, []

        def replacer(match: re.Match) -> str:
            token = match.group(0)
            placeholders.append(token)
            idx = len(placeholders) - 1
            return f'<ph id="{idx}"/>'

        # First escape XML ampersands to avoid DeepL XML parsing errors
        escaped_text = text.replace("&", "&amp;")
        protected = INTERPOLATION_PATTERN.sub(replacer, escaped_text)
        return protected, placeholders

    def _restore_placeholders(self, text: str, placeholders: List[str]) -> str:
        """Restore protected interpolation placeholders from XML tags."""
        restored = text
        for idx, token in enumerate(placeholders):
            tag = f'<ph id="{idx}"/>'
            # Also handle variations if DeepL modifies whitespace in tag
            tag_alt = f'<ph id="{idx}" />'
            tag_alt2 = f'<ph id="{idx}">'
            tag_alt3 = f'<ph id="{idx}"></ph>'
            restored = restored.replace(tag, token).replace(tag_alt, token).replace(tag_alt2, token).replace(tag_alt3, token)
        # Clean any remaining stray tags
        restored = re.sub(r'</?ph[^>]*>', '', restored)
        # Restore XML entities
        restored = restored.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        return restored

    async def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = "en",
    ) -> List[str]:
        """Translate a batch of UI text strings using DeepL with caching and placeholder preservation."""
        if not texts:
            return []

        # Validate target language
        target_normalized = target_lang.lower().strip()
        deepl_target = DEEPL_TARGET_LANGUAGE_MAP.get(target_normalized)
        if not deepl_target:
            raise ValueError(
                f"Target language '{target_lang}' is not supported by DeepL. "
                f"Supported target languages: {', '.join(sorted(set(DEEPL_TARGET_LANGUAGE_MAP.keys())))}."
            )

        # Source language
        deepl_source = None
        if source_lang:
            source_normalized = source_lang.lower().strip()
            deepl_source = DEEPL_SOURCE_LANGUAGE_MAP.get(source_normalized)

        # Check configuration
        if not self.is_configured:
            logger.warning(
                "DeepL API key is not configured (DEEPL_API_KEY). "
                "Returning original texts without translation."
            )
            return texts

        # Enforce batch and length limits
        if len(texts) > 50:
            raise ValueError("DeepL UI translation allows a maximum of 50 texts per batch.")

        for t in texts:
            if len(t) > 5000:
                raise ValueError("Individual text exceeds 5000 character limit.")

        # Check cache for any pre-translated items
        results: List[Optional[str]] = [None] * len(texts)
        texts_to_fetch: List[Tuple[int, str, List[str]]] = []

        for i, text in enumerate(texts):
            cached = self._cache.get((deepl_target, text))
            if cached is not None:
                results[i] = cached
            else:
                protected, placeholders = self._protect_placeholders(text)
                texts_to_fetch.append((i, protected, placeholders))

        if not texts_to_fetch:
            return [r for r in results if r is not None]

        # Prepare payload for DeepL API
        raw_texts_payload = [item[1] for item in texts_to_fetch]
        has_xml_tags = any(len(item[2]) > 0 for item in texts_to_fetch)

        payload = {
            "text": raw_texts_payload,
            "target_lang": deepl_target,
            "preserve_formatting": True,
        }
        if has_xml_tags:
            payload["tag_handling"] = "xml"
            payload["ignore_tags"] = ["ph"]
        if deepl_source:
            payload["source_lang"] = deepl_source

        headers = {
            "Authorization": f"DeepL-Auth-Key {self.settings.deepl_api_key.strip()}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.deepl_timeout_seconds) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                )

            if response.status_code == 403:
                masked = self._mask_key(self.settings.deepl_api_key)
                logger.error(f"DeepL authorization failed (403 Forbidden) with key {masked}.")
                raise PermissionError("DeepL API key is invalid or unauthorized.")
            elif response.status_code == 429:
                logger.warning("DeepL rate limit encountered (429 Too Many Requests).")
                raise RuntimeError("DeepL translation rate limit reached. Please retry shortly.")
            elif response.status_code == 456:
                logger.warning("DeepL character quota exceeded (456 Quota Exceeded).")
                raise RuntimeError("DeepL account quota exceeded.")
            elif response.status_code != 200:
                logger.error(f"DeepL API error HTTP {response.status_code}: {response.text}")
                raise RuntimeError(f"DeepL API returned HTTP error {response.status_code}.")

            data = response.json()
            translations = data.get("translations", [])

            if len(translations) != len(texts_to_fetch):
                logger.warning(
                    f"DeepL returned {len(translations)} translations for {len(texts_to_fetch)} inputs."
                )

            for idx, (original_pos, _, placeholders) in enumerate(texts_to_fetch):
                if idx < len(translations):
                    raw_translated = translations[idx].get("text", "")
                    final_translated = self._restore_placeholders(raw_translated, placeholders)
                    results[original_pos] = final_translated
                    # Cache the result
                    self._cache[(deepl_target, texts[original_pos])] = final_translated
                else:
                    results[original_pos] = texts[original_pos]

        except (httpx.RequestError, httpx.TimeoutException) as exc:
            logger.error(f"Network error communicating with DeepL endpoint ({self.api_url}): {exc}")
            raise RuntimeError(f"Failed to connect to DeepL API: {exc}")

        return [r if r is not None else texts[idx] for idx, r in enumerate(results)]


# Singleton instance
_deepl_service: Optional[DeepLTranslationService] = None


def get_deepl_service() -> DeepLTranslationService:
    """Return singleton instance of DeepLTranslationService."""
    global _deepl_service
    if _deepl_service is None:
        _deepl_service = DeepLTranslationService()
    return _deepl_service

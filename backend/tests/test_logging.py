"""Tests for structured logging and base64 redaction filter."""

import logging
from backend.app.core.logging import Base64RedactionFilter


def test_base64_image_redaction() -> None:
    filter_obj = Base64RedactionFilter()
    fake_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"Uploaded menu photo payload: {fake_base64}",
        args=(),
        exc_info=None,
    )
    filter_obj.filter(record)
    assert "data:image/png;base64,[REDACTED_BASE64_IMAGE_PAYLOAD]" in record.msg
    assert "iVBORw0KGgo" not in record.msg


def test_long_base64_blob_redaction() -> None:
    filter_obj = Base64RedactionFilter()
    long_blob = "A" * 120
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"Long payload block: {long_blob} padding text to exceed three hundred characters in length for test evaluation purposes and ensuring redaction triggers reliably across systems.",
        args=(),
        exc_info=None,
    )
    filter_obj.filter(record)
    assert "[REDACTED_BINARY_PAYLOAD]" in record.msg

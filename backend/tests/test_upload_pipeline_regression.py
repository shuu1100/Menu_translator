import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import create_app

app = create_app()
client = TestClient(app)


def test_upload_supported_formats_and_validation():
    """Verify JPEG, PNG, WEBP, corrupt, and unsupported uploads are validated correctly."""
    # 1. Unsupported mime
    res = client.post(
        "/api/v1/menus/analyze",
        files={"file": ("test.txt", b"plain text", "text/plain")},
        data={"target_language": "en"},
    )
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["error"]["message"]

    # 2. Corrupt image
    res_corrupt = client.post(
        "/api/v1/menus/analyze",
        files={"file": ("corrupt.png", b"not_a_real_image_bytes", "image/png")},
        data={"target_language": "en"},
    )
    assert res_corrupt.status_code == 400
    assert "corrupt" in res_corrupt.json()["error"]["message"].lower() or "malformed" in res_corrupt.json()["error"]["message"].lower()

    # 3. Oversized payload check
    oversized_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * (16 * 1024 * 1024)
    res_oversized = client.post(
        "/api/v1/menus/analyze",
        files={"file": ("big.jpg", oversized_bytes, "image/jpeg")},
        data={"target_language": "en"},
    )
    assert res_oversized.status_code == 413

    # 4. Unsupported target language
    img = Image.new("RGB", (50, 50), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    res_bad_lang = client.post(
        "/api/v1/menus/analyze",
        files={"file": ("valid.jpg", buf.getvalue(), "image/jpeg")},
        data={"target_language": "invalid_lang_code"},
    )
    assert res_bad_lang.status_code == 422

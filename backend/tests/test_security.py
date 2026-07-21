"""Tests for the two security fixes: JWT secret hardening and upload validation."""
import io

import pytest
from PIL import Image

from app.config import Settings
from app.utils.files import save_upload


class _FakeUpload:
    """Minimal stand-in for FastAPI's UploadFile (only what save_upload uses)."""

    def __init__(self, data: bytes, filename: str, content_type: str):
        self.file = io.BytesIO(data)
        self.filename = filename
        self.content_type = content_type


def _png_bytes(size=(4, 4)):
    buf = io.BytesIO()
    Image.new("RGB", size, (0, 128, 0)).save(buf, format="PNG")
    return buf.getvalue()


# ---- JWT secret hardening (config fails closed) ----

@pytest.mark.parametrize("bad", ["", "short", "change-this-secret-key-in-production", "placeholder-secret"])
def test_weak_secret_is_rejected(bad, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", bad)
    with pytest.raises(ValueError):
        Settings()


def test_strong_secret_is_accepted(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "a-perfectly-fine-random-secret-value-1234567890")
    assert Settings().jwt_secret_key.startswith("a-perfectly-fine")


# ---- Upload validation (stored-XSS defence) ----

def test_html_disguised_as_image_is_rejected():
    payload = b"<html><script>alert(document.cookie)</script></html>"
    upload = _FakeUpload(payload, filename="evil.html", content_type="image/jpeg")
    with pytest.raises(Exception) as exc:  # HTTPException
        save_upload(upload, "listings")
    assert getattr(exc.value, "status_code", None) == 400


def test_valid_image_stored_with_safe_extension():
    # Real PNG but a misleading .html filename — extension must come from the decoded format.
    upload = _FakeUpload(_png_bytes(), filename="photo.html", content_type="image/png")
    url = save_upload(upload, "listings")
    assert url.endswith(".png")
    assert ".html" not in url


def test_oversized_upload_is_rejected(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "max_upload_bytes", 10)  # 10 bytes
    upload = _FakeUpload(_png_bytes((64, 64)), filename="big.png", content_type="image/png")
    with pytest.raises(Exception) as exc:
        save_upload(upload, "listings")
    assert getattr(exc.value, "status_code", None) == 413

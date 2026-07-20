import io
import os
import uuid

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config import settings

# Detected image format -> (stored extension, Pillow save format). The stored
# extension always comes from what Pillow actually decoded, never from the
# client-supplied filename or Content-Type.
ALLOWED_FORMATS = {
    "JPEG": (".jpg", "JPEG"),
    "PNG": (".png", "PNG"),
    "WEBP": (".webp", "WEBP"),
}


def _read_within_limit(file: UploadFile) -> bytes:
    limit = settings.max_upload_bytes
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds the {limit // (1024 * 1024)} MB limit",
        )
    return data


def save_upload(file: UploadFile, subfolder: str) -> str:
    """Validate, re-encode, and store an uploaded image.

    Security note: the file is decoded with Pillow and written back out from
    pixel data only. That proves it is a real image and strips any embedded
    HTML/script payload, so a malicious upload can never be served as an
    executable document from our own origin (stored XSS). The stored extension
    comes from the decoded format, not the untrusted filename.
    """
    raw = _read_within_limit(file)

    try:
        Image.open(io.BytesIO(raw)).verify()  # cheap integrity check
        image = Image.open(io.BytesIO(raw))  # reopen to actually use it
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not a valid image")

    if image.format not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type. Use JPEG, PNG, or WEBP",
        )

    ext, save_format = ALLOWED_FORMATS[image.format]
    if save_format == "JPEG" and image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    folder = os.path.join(settings.upload_dir, subfolder)
    os.makedirs(folder, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(folder, filename)

    image.save(path, format=save_format)

    return f"/{folder}/{filename}"

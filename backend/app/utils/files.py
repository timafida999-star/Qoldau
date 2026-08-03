import io
import os
import uuid
from typing import NamedTuple, Optional

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings

# Detected image format -> (stored extension, Pillow save format). The stored
# extension always comes from what Pillow actually decoded, never from the
# client-supplied filename or Content-Type.
ALLOWED_FORMATS = {
    "JPEG": (".jpg", "JPEG"),
    "PNG": (".png", "PNG"),
    "WEBP": (".webp", "WEBP"),
}

# A modern phone photo is ~4000px and several megabytes; nothing in the UI
# renders larger than this.
MAX_IMAGE_SIDE = 1600
AVATAR_MAX_SIDE = 512
# Grid cards render at ~400px wide, so a 480px thumbnail is enough.
THUMB_SIDE = 480

_SAVE_KWARGS = {
    "JPEG": {"quality": 85, "optimize": True, "progressive": True},
    "WEBP": {"quality": 85},
    "PNG": {"optimize": True},
}


class StoredImage(NamedTuple):
    url: str
    thumb_url: Optional[str]


def _read_within_limit(file: UploadFile) -> bytes:
    limit = settings.max_upload_bytes
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds the {limit // (1024 * 1024)} MB limit",
        )
    return data


def _downscale(image: Image.Image, max_side: int) -> Image.Image:
    largest = max(image.size)
    if largest <= max_side:
        return image
    scale = max_side / largest
    new_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(new_size, Image.LANCZOS)


def save_upload(file: UploadFile, subfolder: str, *, max_side: int = MAX_IMAGE_SIDE, thumb_side: Optional[int] = None) -> StoredImage:
    """Validate, normalize, re-encode, and store an uploaded image.

    Security note: the file is decoded with Pillow and written back out from
    pixel data only. That proves it is a real image and strips any embedded
    HTML/script payload, so a malicious upload can never be served as an
    executable document from our own origin (stored XSS). The stored extension
    comes from the decoded format, not the untrusted filename.

    The image is downscaled to `max_side` and re-encoded at a sane quality —
    phone photos arrive at several megabytes and would otherwise be served to
    every visitor as-is. With `thumb_side` a second, smaller copy is written
    for grid cards.
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

    # Phones record orientation as EXIF metadata instead of rotating pixels.
    # Re-encoding strips the metadata, so bake the rotation into the pixels
    # first or portrait photos come out sideways.
    image = ImageOps.exif_transpose(image)

    if save_format == "JPEG" and image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    image = _downscale(image, max_side)

    folder = os.path.join(settings.upload_dir, subfolder)
    os.makedirs(folder, exist_ok=True)
    stem = uuid.uuid4()
    filename = f"{stem}{ext}"
    image.save(os.path.join(folder, filename), format=save_format, **_SAVE_KWARGS.get(save_format, {}))

    thumb_url = None
    if thumb_side is not None:
        thumb = _downscale(image, thumb_side)
        thumb_name = f"{stem}_thumb{ext}"
        thumb.save(os.path.join(folder, thumb_name), format=save_format, **_SAVE_KWARGS.get(save_format, {}))
        thumb_url = f"/{folder}/{thumb_name}"

    return StoredImage(url=f"/{folder}/{filename}", thumb_url=thumb_url)

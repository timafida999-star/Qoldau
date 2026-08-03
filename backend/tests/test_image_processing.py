"""The image pipeline: EXIF orientation, downscaling, thumbnails, avatar cap.

Phone photos arrive at several megabytes with the rotation stored only in EXIF
metadata. Re-encoding used to strip that metadata without applying it (photos
displayed sideways) and stored the full-size original (grid pages pulled
megabytes per card).
"""
import io
import os

from PIL import Image

from app.config import settings
from app.utils.files import MAX_IMAGE_SIDE, THUMB_SIDE, AVATAR_MAX_SIDE


def _jpeg(size=(2400, 1200), orientation=None) -> bytes:
    image = Image.new("RGB", size, (200, 60, 60))
    exif = image.getexif()
    if orientation is not None:
        exif[274] = orientation  # EXIF tag 274 = Orientation
    buf = io.BytesIO()
    image.save(buf, format="JPEG", exif=exif.tobytes())
    return buf.getvalue()


def upload_images(client, owner, listing_id, blobs):
    files = [("files", (f"img{i}.jpg", blob, "image/jpeg")) for i, blob in enumerate(blobs)]
    return client.post(f"/listings/{listing_id}/images", headers=owner["headers"], files=files)


def _stored_path(subfolder: str, url: str) -> str:
    # Urls are "/<upload_dir>/<subfolder>/<name>"; the basename is enough to
    # find the file on disk regardless of how upload_dir was configured.
    return os.path.join(settings.upload_dir, subfolder, os.path.basename(url))


def test_large_upload_is_downscaled_and_gets_a_thumbnail(client, make_user, make_listing):
    owner = make_user()
    listing = make_listing(owner)

    resp = upload_images(client, owner, listing["id"], [_jpeg((2400, 1200))])

    assert resp.status_code == 201, resp.text
    image = resp.json()[0]
    with Image.open(_stored_path("listings", image["image_url"])) as main:
        assert main.size == (MAX_IMAGE_SIDE, MAX_IMAGE_SIDE // 2)
    assert image["thumb_url"], "expected a thumbnail for listing photos"
    with Image.open(_stored_path("listings", image["thumb_url"])) as thumb:
        assert max(thumb.size) == THUMB_SIDE


def test_small_upload_is_not_upscaled(client, make_user, make_listing):
    owner = make_user()
    listing = make_listing(owner)

    resp = upload_images(client, owner, listing["id"], [_jpeg((300, 200))])

    image = resp.json()[0]
    with Image.open(_stored_path("listings", image["image_url"])) as main:
        assert main.size == (300, 200)


def test_exif_orientation_is_baked_into_pixels(client, make_user, make_listing):
    """Orientation 6 = "rotate 90° CW to display": a 40x20 frame is a 20x40 photo."""
    owner = make_user()
    listing = make_listing(owner)

    resp = upload_images(client, owner, listing["id"], [_jpeg((40, 20), orientation=6)])

    image = resp.json()[0]
    with Image.open(_stored_path("listings", image["image_url"])) as main:
        assert main.size == (20, 40)


def test_avatar_is_capped_and_has_no_thumbnail(client, make_user):
    user = make_user()

    resp = client.post(
        "/users/me/avatar",
        headers=user["headers"],
        files={"file": ("selfie.jpg", _jpeg((1200, 1200)), "image/jpeg")},
    )

    assert resp.status_code == 200, resp.text
    avatar_url = resp.json()["avatar_url"]
    with Image.open(_stored_path("avatars", avatar_url)) as avatar:
        assert max(avatar.size) == AVATAR_MAX_SIDE

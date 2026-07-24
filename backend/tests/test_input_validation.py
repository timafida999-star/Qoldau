"""Length and range bounds on user-supplied input.

The frontend's Zod schemas used to be the only validation in the system, so the
API accepted a one-character password, a 5000-character name, an empty name, a
20,000-character bio, and a 1 MB listing description. Nothing forces a client to
go through the forms.
"""
import uuid

import pytest

from app.schemas.fields import (
    Bio,
    Comment,
    FullName,
    ListingDescription,
    NewPassword,
    Phone,
)


def _bounds(annotated) -> tuple[int, int | None]:
    """(min, max) for a constrained type.

    Handles both shapes used in ``app.schemas.fields``: ``StringConstraints``
    exposes the bounds directly, while ``Field(...)`` tucks them into a
    ``FieldInfo.metadata`` list of ``MinLen``/``MaxLen``.
    """
    low, high = 0, None
    for meta in annotated.__metadata__:
        low = getattr(meta, "min_length", None) or low
        high = getattr(meta, "max_length", None) or high
        for inner in getattr(meta, "metadata", []):
            low = getattr(inner, "min_length", None) or low
            high = getattr(inner, "max_length", None) or high
    return low, high


def _max_len(annotated) -> int:
    high = _bounds(annotated)[1]
    assert high is not None, f"{annotated} has no upper bound"
    return high


def _min_len(annotated) -> int:
    return _bounds(annotated)[0]


def register(client, **overrides):
    payload = {
        "email": f"probe-{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "full_name": "Probe User",
    }
    payload.update(overrides)
    return client.post("/auth/register", json=payload)


# --- registration ------------------------------------------------------------


@pytest.mark.parametrize("password", ["a", "short", "1234567"])
def test_register_rejects_short_passwords(client, password):
    assert register(client, password=password).status_code == 422


def test_register_accepts_a_password_at_the_minimum(client):
    assert register(client, password="12345678").status_code == 201


def test_register_rejects_an_overlong_password(client):
    assert register(client, password="x" * (_max_len(NewPassword) + 1)).status_code == 422


@pytest.mark.parametrize("full_name", ["", "   ", "a", "x" * 5000])
def test_register_rejects_bad_names(client, full_name):
    assert register(client, full_name=full_name).status_code == 422


def test_register_strips_surrounding_whitespace_from_the_name(client, make_user):
    resp = register(client, full_name="   Padded Name   ")
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["full_name"] == "Padded Name"


def test_register_rejects_an_overlong_email(client):
    long_email = "x" * 250 + "@example.com"
    assert register(client, email=long_email).status_code == 422


# --- login must not inherit the registration policy --------------------------


def test_login_still_works_for_an_account_with_a_pre_policy_password(client, db):
    """Accounts created before the 8-character minimum must not be locked out."""
    from app.auth.security import hash_password
    from app.models.user import User

    user = User(
        email="legacy@example.com", hashed_password=hash_password("a"), full_name="Legacy User"
    )
    db.add(user)
    db.commit()

    resp = client.post("/auth/login", json={"email": "legacy@example.com", "password": "a"})
    assert resp.status_code == 200, resp.text
    assert "access_token" in resp.json()


def test_login_with_a_wrong_short_password_is_still_unauthorised_not_invalid(client, make_user):
    """A bad password is a 401, never a 422 - the response must not leak policy."""
    user = make_user()
    resp = client.post("/auth/login", json={"email": user["email"], "password": "a"})
    assert resp.status_code == 401


# --- profile updates ---------------------------------------------------------


@pytest.mark.parametrize("full_name", ["", "   ", "a", "x" * 5000])
def test_profile_update_rejects_bad_names(client, make_user, full_name):
    user = make_user()
    resp = client.patch("/users/me", headers=user["headers"], json={"full_name": full_name})
    assert resp.status_code == 422


def test_profile_update_rejects_an_overlong_bio(client, make_user):
    user = make_user()
    resp = client.patch(
        "/users/me", headers=user["headers"], json={"bio": "x" * (_max_len(Bio) + 1)}
    )
    assert resp.status_code == 422


def test_profile_update_rejects_an_overlong_phone(client, make_user):
    user = make_user()
    resp = client.patch(
        "/users/me", headers=user["headers"], json={"phone": "1" * (_max_len(Phone) + 1)}
    )
    assert resp.status_code == 422


def test_profile_update_accepts_values_at_the_limit(client, make_user):
    user = make_user()
    resp = client.patch(
        "/users/me",
        headers=user["headers"],
        json={"bio": "x" * _max_len(Bio), "phone": "1" * _max_len(Phone)},
    )
    assert resp.status_code == 200, resp.text


def test_clearing_optional_profile_fields_is_still_allowed(client, make_user):
    """An empty bio means "remove it", so it must not trip the length check."""
    user = make_user()
    resp = client.patch("/users/me", headers=user["headers"], json={"bio": "", "phone": ""})
    assert resp.status_code == 200, resp.text


# --- listings ----------------------------------------------------------------


def listing_payload(**overrides):
    payload = {
        "title": "Wooden chair",
        "description": "A sturdy item in decent shape.",
        "category": "furniture",
        "condition": "good",
        "latitude": 43.238,
        "longitude": 76.945,
    }
    payload.update(overrides)
    return payload


def test_listing_rejects_a_huge_description(client, make_user):
    user = make_user()
    resp = client.post(
        "/listings",
        headers=user["headers"],
        json=listing_payload(description="x" * 1_000_000),
    )
    assert resp.status_code == 422


def test_listing_accepts_a_description_at_the_limit(client, make_user):
    user = make_user()
    resp = client.post(
        "/listings",
        headers=user["headers"],
        json=listing_payload(description="x" * _max_len(ListingDescription)),
    )
    assert resp.status_code == 201, resp.text


def test_listing_rejects_an_overlong_address(client, make_user):
    user = make_user()
    resp = client.post(
        "/listings", headers=user["headers"], json=listing_payload(address_text="x" * 5000)
    )
    assert resp.status_code == 422


@pytest.mark.parametrize(
    "coords",
    [
        {"latitude": 999, "longitude": 76.945},
        {"latitude": -91, "longitude": 76.945},
        {"latitude": 43.238, "longitude": -5000},
        {"latitude": 43.238, "longitude": 181},
    ],
)
def test_listing_rejects_coordinates_off_the_globe(client, make_user, coords):
    user = make_user()
    resp = client.post("/listings", headers=user["headers"], json=listing_payload(**coords))
    assert resp.status_code == 422


def test_listing_accepts_coordinates_at_the_extremes(client, make_user):
    user = make_user()
    resp = client.post(
        "/listings", headers=user["headers"], json=listing_payload(latitude=-90, longitude=180)
    )
    assert resp.status_code == 201, resp.text


def test_listing_update_is_bounded_too(client, make_user, make_listing):
    """PATCH must not be a way around the limits POST enforces."""
    user = make_user()
    listing = make_listing(user)
    resp = client.patch(
        f"/listings/{listing['id']}", headers=user["headers"], json={"description": "x" * 1_000_000}
    )
    assert resp.status_code == 422


# --- free text on reviews and reports ---------------------------------------


def test_report_rejects_an_overlong_description(client, make_user):
    user = make_user()
    resp = client.post(
        "/reports",
        headers=user["headers"],
        json={
            "target_type": "listing",
            "target_id": str(uuid.uuid4()),
            "reason": "spam",
            "description": "x" * (_max_len(Comment) + 1),
        },
    )
    assert resp.status_code == 422


def test_review_rejects_an_overlong_comment(client, make_user):
    user = make_user()
    resp = client.post(
        "/reviews",
        headers=user["headers"],
        json={
            "exchange_id": str(uuid.uuid4()),
            "rating": 5,
            "comment": "x" * (_max_len(Comment) + 1),
        },
    )
    # 422 for the comment, not 404 for the exchange: validation runs first.
    assert resp.status_code == 422


# --- the shared field definitions themselves --------------------------------


def test_every_bounded_text_type_has_an_upper_bound():
    for annotated in (FullName, Bio, Phone, ListingDescription, Comment, NewPassword):
        assert _max_len(annotated) > 0


def test_name_requires_real_content():
    assert _min_len(FullName) >= 2

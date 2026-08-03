"""Meeting-point privacy and the "near me" filter.

The exact coordinates of a listing are effectively someone's home address.
They are blurred (deterministically, 150-350 m) for everyone except the owner,
an admin, and the requester whose reservation was accepted. The blur stays
inside the 500 m uncertainty circle the frontend draws.

The "near me" filter (near_lat/near_lng/radius_km) works on the true
coordinates server-side, sorts closest-first, and annotates items with
distance_km.
"""
from app.utils.geo import haversine_km

# Almaty city centre and a point ~20 km away.
CENTER = (43.238, 76.945)
FAR = (43.05, 76.90)


def create_listing_at(client, owner, lat, lng, title="Located item"):
    resp = client.post(
        "/listings",
        headers=owner["headers"],
        json={
            "title": title,
            "description": "A sturdy item in decent shape.",
            "category": "other",
            "condition": "good",
            "latitude": lat,
            "longitude": lng,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def reserve(client, requester, listing_id):
    return client.post(f"/listings/{listing_id}/reservations", headers=requester["headers"])


def accept(client, owner, reservation_id):
    return client.patch(
        f"/reservations/{reservation_id}", headers=owner["headers"], json={"action": "accept"}
    )


# --- who sees what on the detail endpoint -----------------------------------


def test_anonymous_viewer_gets_blurred_coordinates(client, make_user):
    owner = make_user()
    listing = create_listing_at(client, owner, *CENTER)

    body = client.get(f"/listings/{listing['id']}").json()

    assert body["location_is_approximate"] is True
    offset_km = haversine_km(CENTER[0], CENTER[1], body["latitude"], body["longitude"])
    # Blurred by a meaningful amount, but still inside the 500 m circle the UI draws.
    assert 0.1 <= offset_km <= 0.5, f"offset was {offset_km:.3f} km"


def test_blur_is_deterministic(client, make_user):
    """Repeated requests must not be averageable back to the true point."""
    owner = make_user()
    listing = create_listing_at(client, owner, *CENTER)

    first = client.get(f"/listings/{listing['id']}").json()
    second = client.get(f"/listings/{listing['id']}").json()

    assert (first["latitude"], first["longitude"]) == (second["latitude"], second["longitude"])


def test_owner_sees_exact_coordinates(client, make_user):
    owner = make_user()
    listing = create_listing_at(client, owner, *CENTER)

    body = client.get(f"/listings/{listing['id']}", headers=owner["headers"]).json()

    assert body["location_is_approximate"] is False
    assert (body["latitude"], body["longitude"]) == CENTER


def test_pending_requester_still_sees_blurred(client, make_user):
    owner, requester = make_user(), make_user()
    listing = create_listing_at(client, owner, *CENTER)
    reserve(client, requester, listing["id"])

    body = client.get(f"/listings/{listing['id']}", headers=requester["headers"]).json()

    assert body["location_is_approximate"] is True


def test_accepted_requester_sees_exact_coordinates(client, make_user):
    owner, requester = make_user(), make_user()
    listing = create_listing_at(client, owner, *CENTER)
    reservation = reserve(client, requester, listing["id"]).json()
    accept(client, owner, reservation["id"])

    body = client.get(f"/listings/{listing['id']}", headers=requester["headers"]).json()

    assert body["location_is_approximate"] is False
    assert (body["latitude"], body["longitude"]) == CENTER


# --- the list endpoint follows the same rules --------------------------------


def test_list_blurs_for_anonymous_and_not_for_owner(client, make_user):
    owner = make_user()
    create_listing_at(client, owner, *CENTER)

    anon_item = client.get("/listings").json()["items"][0]
    owner_item = client.get("/listings", headers=owner["headers"]).json()["items"][0]

    assert anon_item["location_is_approximate"] is True
    assert owner_item["location_is_approximate"] is False
    assert (owner_item["latitude"], owner_item["longitude"]) == CENTER


def test_list_shows_exact_point_for_accepted_requester(client, make_user):
    owner, requester = make_user(), make_user()
    listing = create_listing_at(client, owner, *CENTER)
    reservation = reserve(client, requester, listing["id"]).json()
    accept(client, owner, reservation["id"])

    items = client.get("/listings", headers=requester["headers"]).json()["items"]

    assert items[0]["id"] == listing["id"]
    assert items[0]["location_is_approximate"] is False


# --- near me ------------------------------------------------------------------


def test_near_filter_limits_and_sorts_by_distance(client, make_user):
    owner = make_user()
    create_listing_at(client, owner, *CENTER, title="Close item")
    create_listing_at(client, owner, *FAR, title="Far item")

    close_only = client.get(
        "/listings", params={"near_lat": CENTER[0], "near_lng": CENTER[1], "radius_km": 5}
    ).json()
    assert [x["title"] for x in close_only["items"]] == ["Close item"]

    both = client.get(
        "/listings", params={"near_lat": CENTER[0], "near_lng": CENTER[1], "radius_km": 100}
    ).json()
    assert [x["title"] for x in both["items"]] == ["Close item", "Far item"]


def test_near_filter_annotates_distance(client, make_user):
    owner = make_user()
    create_listing_at(client, owner, *FAR, title="Far item")

    item = client.get(
        "/listings", params={"near_lat": CENTER[0], "near_lng": CENTER[1], "radius_km": 100}
    ).json()["items"][0]

    expected = haversine_km(CENTER[0], CENTER[1], FAR[0], FAR[1])
    assert item["distance_km"] == round(expected, 1)


def test_distance_is_absent_without_near_filter(client, make_user):
    owner = make_user()
    create_listing_at(client, owner, *CENTER)

    item = client.get("/listings").json()["items"][0]

    assert item["distance_km"] is None


def test_near_params_must_come_together(client):
    assert client.get("/listings", params={"near_lat": 43.2}).status_code == 400
    assert client.get("/listings", params={"near_lng": 76.9}).status_code == 400
    assert client.get("/listings", params={"radius_km": 5}).status_code == 400


def test_near_params_are_validated(client):
    assert client.get("/listings", params={"near_lat": 91, "near_lng": 76.9}).status_code == 422
    assert (
        client.get(
            "/listings", params={"near_lat": 43.2, "near_lng": 76.9, "radius_km": 0}
        ).status_code
        == 422
    )

def test_create_listing(client, make_user):
    owner = make_user()
    resp = client.post(
        "/listings",
        headers=owner["headers"],
        json={
            "title": "Green tea bottle",
            "description": "Barely opened, still good.",
            "category": "other",
            "condition": "good",
            "latitude": 43.25,
            "longitude": 76.94,
            "address_text": "KBTU",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Green tea bottle"
    assert body["category"] == "other"       # enum stored/returned by value, not name
    assert body["status"] == "available"
    assert body["owner"]["id"] == owner["id"]


def test_create_listing_requires_auth(client):
    resp = client.post(
        "/listings",
        json={
            "title": "No auth", "description": "should fail here", "category": "other",
            "condition": "good", "latitude": 43.0, "longitude": 76.0,
        },
    )
    assert resp.status_code == 401


def test_create_listing_validation(client, make_user):
    owner = make_user()
    # title too short, description too short
    resp = client.post(
        "/listings",
        headers=owner["headers"],
        json={"title": "x", "description": "short", "category": "other",
              "condition": "good", "latitude": 43.0, "longitude": 76.0},
    )
    assert resp.status_code == 422


def test_list_and_filter_listings(client, make_user, make_listing):
    owner = make_user()
    make_listing(owner, title="Old books", category="books")
    make_listing(owner, title="Sofa", category="furniture")

    all_items = client.get("/listings").json()
    assert len(all_items) == 2

    books = client.get("/listings", params={"category": "books"}).json()
    assert [x["title"] for x in books] == ["Old books"]

    found = client.get("/listings", params={"search": "sof"}).json()
    assert [x["title"] for x in found] == ["Sofa"]

    none = client.get("/listings", params={"search": "zzzzz"}).json()
    assert none == []


def test_owner_can_update_and_delete_listing(client, make_user, make_listing):
    owner = make_user()
    listing = make_listing(owner)

    updated = client.patch(
        f"/listings/{listing['id']}", headers=owner["headers"], json={"title": "New title"}
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "New title"

    deleted = client.delete(f"/listings/{listing['id']}", headers=owner["headers"])
    assert deleted.status_code == 204
    assert client.get(f"/listings/{listing['id']}").status_code == 404


def test_non_owner_cannot_edit_listing(client, make_user, make_listing):
    owner = make_user()
    stranger = make_user()
    listing = make_listing(owner)

    resp = client.patch(
        f"/listings/{listing['id']}", headers=stranger["headers"], json={"title": "Hijacked"}
    )
    assert resp.status_code == 403

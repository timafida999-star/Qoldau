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

    page = client.get("/listings").json()
    assert page["total"] == 2
    assert len(page["items"]) == 2
    assert page["has_more"] is False

    books = client.get("/listings", params={"category": "books"}).json()
    assert [x["title"] for x in books["items"]] == ["Old books"]

    found = client.get("/listings", params={"search": "sof"}).json()
    assert [x["title"] for x in found["items"]] == ["Sofa"]

    none = client.get("/listings", params={"search": "zzzzz"}).json()
    assert none["items"] == []
    assert none["total"] == 0


def test_pagination(client, make_user, make_listing):
    owner = make_user()
    for i in range(5):
        make_listing(owner, title=f"Item {i}")

    first = client.get("/listings", params={"page": 1, "page_size": 2}).json()
    assert first["total"] == 5
    assert len(first["items"]) == 2
    assert first["has_more"] is True

    third = client.get("/listings", params={"page": 3, "page_size": 2}).json()
    assert len(third["items"]) == 1  # 5 items, last page has the remainder
    assert third["has_more"] is False

    # No overlap between pages.
    p1 = client.get("/listings", params={"page": 1, "page_size": 2}).json()["items"]
    p2 = client.get("/listings", params={"page": 2, "page_size": 2}).json()["items"]
    assert set(x["id"] for x in p1).isdisjoint(x["id"] for x in p2)


def test_page_size_capped(client, make_user):
    # page_size above the max (48) is rejected by validation.
    assert client.get("/listings", params={"page_size": 999}).status_code == 422


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

"""End-to-end exercise of the core lifecycle:
reserve -> owner accepts -> QR exchange -> complete -> reviews.
"""
from app.models.exchange import Exchange


def reserve(client, requester, listing_id):
    return client.post(f"/listings/{listing_id}/reservations", headers=requester["headers"])


def test_cannot_reserve_own_listing(client, make_user, make_listing):
    owner = make_user()
    listing = make_listing(owner)
    resp = reserve(client, owner, listing["id"])
    assert resp.status_code == 400


def test_reserve_creates_pending_request(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)

    resp = reserve(client, requester, listing["id"])
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_duplicate_pending_request_rejected(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    assert reserve(client, requester, listing["id"]).status_code == 201
    assert reserve(client, requester, listing["id"]).status_code == 400


def test_only_owner_can_accept(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    res = reserve(client, requester, listing["id"]).json()

    # requester tries to accept their own request -> forbidden
    resp = client.patch(f"/reservations/{res['id']}", headers=requester["headers"], json={"action": "accept"})
    assert resp.status_code == 403


def test_accept_reserves_listing_and_creates_chat_and_exchange(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    res = reserve(client, requester, listing["id"]).json()

    accepted = client.patch(
        f"/reservations/{res['id']}", headers=owner["headers"], json={"action": "accept"}
    ).json()

    assert accepted["status"] == "accepted"
    assert accepted["chat_id"] is not None
    assert accepted["exchange_id"] is not None
    assert client.get(f"/listings/{listing['id']}").json()["status"] == "reserved"


def test_accept_auto_declines_competing_requests(client, make_user, make_listing):
    owner, r1, r2 = make_user(), make_user(), make_user()
    listing = make_listing(owner)
    res1 = reserve(client, r1, listing["id"]).json()
    reserve(client, r2, listing["id"])

    client.patch(f"/reservations/{res1['id']}", headers=owner["headers"], json={"action": "accept"})

    # r2's request should now be declined
    r2_view = client.get("/reservations/mine", headers=r2["headers"]).json()
    assert r2_view[0]["status"] == "declined"


def test_full_exchange_and_review_flow(client, db, make_user, make_listing):
    owner, requester = make_user("Owner"), make_user("Requester")
    listing = make_listing(owner)
    res = reserve(client, requester, listing["id"]).json()
    accepted = client.patch(
        f"/reservations/{res['id']}", headers=owner["headers"], json={"action": "accept"}
    ).json()
    exchange_id = accepted["exchange_id"]

    # The recipient "scans" the QR — we read the code from the DB to stand in for that.
    qr_uuid = str(db.query(Exchange).filter(Exchange.id == exchange_id).first().qr_uuid)

    # Owner cannot verify their own handoff; only the recipient can.
    assert client.post("/exchanges/verify", headers=owner["headers"], json={"qr_uuid": qr_uuid}).status_code == 403

    verified = client.post("/exchanges/verify", headers=requester["headers"], json={"qr_uuid": qr_uuid})
    assert verified.status_code == 200
    assert verified.json()["status"] == "completed"
    assert client.get(f"/listings/{listing['id']}").json()["status"] == "completed"

    # A second verification of a completed exchange is rejected.
    assert client.post("/exchanges/verify", headers=requester["headers"], json={"qr_uuid": qr_uuid}).status_code == 400

    # Requester reviews the owner -> owner's average rating updates.
    review = client.post(
        "/reviews", headers=requester["headers"],
        json={"exchange_id": exchange_id, "rating": 5, "comment": "Smooth handoff"},
    )
    assert review.status_code == 201

    owner_profile = client.get(f"/users/{owner['id']}").json()
    assert owner_profile["rating_avg"] == 5.0
    assert owner_profile["rating_count"] == 1

    # Cannot review the same exchange twice.
    dup = client.post("/reviews", headers=requester["headers"], json={"exchange_id": exchange_id, "rating": 3})
    assert dup.status_code == 400


def test_cannot_review_before_completion(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    res = reserve(client, requester, listing["id"]).json()
    accepted = client.patch(
        f"/reservations/{res['id']}", headers=owner["headers"], json={"action": "accept"}
    ).json()

    resp = client.post(
        "/reviews", headers=requester["headers"],
        json={"exchange_id": accepted["exchange_id"], "rating": 5},
    )
    assert resp.status_code == 400

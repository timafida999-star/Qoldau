"""Cancelling reservations, including the accepted ones.

An accepted reservation used to be a permanent dead end: accept/decline required
PENDING, and cancel required PENDING *and* the requester. If the counterparty
stopped replying, the listing stayed "reserved" forever and the owner's only
escape was deleting the listing and re-creating it.
"""
from app.models.exchange import Exchange


def reserve(client, requester, listing_id):
    return client.post(f"/listings/{listing_id}/reservations", headers=requester["headers"])


def accept(client, owner, reservation_id):
    return client.patch(
        f"/reservations/{reservation_id}", headers=owner["headers"], json={"action": "accept"}
    )


def cancel(client, actor, reservation_id):
    return client.patch(
        f"/reservations/{reservation_id}", headers=actor["headers"], json={"action": "cancel"}
    )


def make_accepted(client, make_user, make_listing):
    owner, requester = make_user("Owner"), make_user("Requester")
    listing = make_listing(owner)
    reservation = reserve(client, requester, listing["id"]).json()
    accepted = accept(client, owner, reservation["id"]).json()
    return owner, requester, listing, accepted


# --- the reported dead end --------------------------------------------------


def test_owner_can_cancel_an_accepted_reservation(client, make_user, make_listing):
    owner, _requester, listing, accepted = make_accepted(client, make_user, make_listing)
    assert client.get(f"/listings/{listing['id']}").json()["status"] == "reserved"

    resp = cancel(client, owner, accepted["id"])

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "cancelled"
    assert client.get(f"/listings/{listing['id']}").json()["status"] == "available"


def test_requester_can_cancel_an_accepted_reservation(client, make_user, make_listing):
    _owner, requester, listing, accepted = make_accepted(client, make_user, make_listing)

    resp = cancel(client, requester, accepted["id"])

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "cancelled"
    assert client.get(f"/listings/{listing['id']}").json()["status"] == "available"


def test_released_listing_can_be_reserved_by_someone_else(client, make_user, make_listing):
    owner, _requester, listing, accepted = make_accepted(client, make_user, make_listing)
    cancel(client, owner, accepted["id"])

    newcomer = make_user("Newcomer")
    resp = reserve(client, newcomer, listing["id"])

    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "pending"


def test_original_requester_can_request_again_after_cancelling(client, make_user, make_listing):
    _owner, requester, listing, accepted = make_accepted(client, make_user, make_listing)
    cancel(client, requester, accepted["id"])

    assert reserve(client, requester, listing["id"]).status_code == 201


# --- the cancel must not leave a live QR behind -----------------------------


def test_cancelling_invalidates_the_exchange_qr(client, db, make_user, make_listing):
    owner, requester, _listing, accepted = make_accepted(client, make_user, make_listing)
    exchange_id = accepted["exchange_id"]
    qr_uuid = str(db.query(Exchange).filter(Exchange.id == exchange_id).first().qr_uuid)

    cancel(client, owner, accepted["id"])

    # The owner can no longer display the code...
    assert client.get(f"/exchanges/{exchange_id}/qr", headers=owner["headers"]).status_code == 400
    # ...and a code captured before the cancel no longer completes the exchange.
    resp = client.post("/exchanges/verify", headers=requester["headers"], json={"qr_uuid": qr_uuid})
    assert resp.status_code == 400, resp.text


def test_cancelling_does_not_flip_a_released_listing_to_completed(client, db, make_user, make_listing):
    owner, requester, listing, accepted = make_accepted(client, make_user, make_listing)
    qr_uuid = str(db.query(Exchange).filter(Exchange.id == accepted["exchange_id"]).first().qr_uuid)

    cancel(client, owner, accepted["id"])
    client.post("/exchanges/verify", headers=requester["headers"], json={"qr_uuid": qr_uuid})

    assert client.get(f"/listings/{listing['id']}").json()["status"] == "available"


# --- guards -----------------------------------------------------------------


def test_cannot_cancel_a_completed_exchange(client, db, make_user, make_listing):
    owner, requester, listing, accepted = make_accepted(client, make_user, make_listing)
    qr_uuid = str(db.query(Exchange).filter(Exchange.id == accepted["exchange_id"]).first().qr_uuid)
    assert client.post(
        "/exchanges/verify", headers=requester["headers"], json={"qr_uuid": qr_uuid}
    ).status_code == 200

    resp = cancel(client, owner, accepted["id"])

    assert resp.status_code == 400
    assert client.get(f"/listings/{listing['id']}").json()["status"] == "completed"


def test_stranger_cannot_cancel(client, make_user, make_listing):
    _owner, _requester, _listing, accepted = make_accepted(client, make_user, make_listing)
    stranger = make_user("Stranger")

    assert cancel(client, stranger, accepted["id"]).status_code == 403


def test_cannot_cancel_an_already_cancelled_reservation(client, make_user, make_listing):
    owner, _requester, _listing, accepted = make_accepted(client, make_user, make_listing)
    assert cancel(client, owner, accepted["id"]).status_code == 200

    assert cancel(client, owner, accepted["id"]).status_code == 400


def test_cannot_cancel_a_declined_reservation(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    reservation = reserve(client, requester, listing["id"]).json()
    client.patch(
        f"/reservations/{reservation['id']}", headers=owner["headers"], json={"action": "decline"}
    )

    assert cancel(client, requester, reservation["id"]).status_code == 400


# --- existing pending behaviour must be unchanged ---------------------------


def test_requester_can_still_cancel_a_pending_request(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    reservation = reserve(client, requester, listing["id"]).json()

    resp = cancel(client, requester, reservation["id"])

    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    # A pending request never reserved the listing, so nothing to release.
    assert client.get(f"/listings/{listing['id']}").json()["status"] == "available"


def test_owner_still_cannot_cancel_a_pending_request(client, make_user, make_listing):
    """The owner's verb for a request they never agreed to is "decline"."""
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    reservation = reserve(client, requester, listing["id"]).json()

    assert cancel(client, owner, reservation["id"]).status_code == 403

"""The "why me?" note attached to a reservation request.

The owner used to pick a recipient blind: every request looked like a bare
name. The request can now carry a short message, and the owner sees it (plus
the requester's rating, which UserPublic already exposes) before choosing.
"""


def reserve(client, requester, listing_id, json=None):
    kwargs = {"headers": requester["headers"]}
    if json is not None:
        kwargs["json"] = json
    return client.post(f"/listings/{listing_id}/reservations", **kwargs)


def test_request_with_message(client, make_user, make_listing):
    owner, requester = make_user("Owner"), make_user("Requester")
    listing = make_listing(owner)

    resp = reserve(client, requester, listing["id"], json={"message": "My kid starts school on Monday"})

    assert resp.status_code == 201, resp.text
    assert resp.json()["message"] == "My kid starts school on Monday"


def test_request_without_body_still_works(client, make_user, make_listing):
    """The old client posted no body at all; that must keep working."""
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)

    resp = reserve(client, requester, listing["id"])

    assert resp.status_code == 201, resp.text
    assert resp.json()["message"] is None


def test_blank_message_is_stored_as_null(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)

    resp = reserve(client, requester, listing["id"], json={"message": "   "})

    assert resp.status_code == 201, resp.text
    assert resp.json()["message"] is None


def test_message_length_is_capped(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)

    resp = reserve(client, requester, listing["id"], json={"message": "x" * 501})

    assert resp.status_code == 422


def test_owner_sees_message_and_requester_rating(client, make_user, make_listing):
    owner, requester = make_user("Owner"), make_user("Hopeful Requester")
    listing = make_listing(owner)
    reserve(client, requester, listing["id"], json={"message": "I live next door, can pick up today"})

    mine = client.get("/reservations/mine", headers=owner["headers"]).json()

    assert len(mine) == 1
    request = mine[0]
    assert request["role"] == "owner"
    assert request["message"] == "I live next door, can pick up today"
    # Everything the owner needs to choose between requesters:
    assert request["requester"]["full_name"] == "Hopeful Requester"
    assert "rating_avg" in request["requester"]
    assert "rating_count" in request["requester"]


def test_message_survives_accept(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    reservation = reserve(client, requester, listing["id"], json={"message": "Please pick me"}).json()

    accepted = client.patch(
        f"/reservations/{reservation['id']}", headers=owner["headers"], json={"action": "accept"}
    )

    assert accepted.status_code == 200
    assert accepted.json()["message"] == "Please pick me"

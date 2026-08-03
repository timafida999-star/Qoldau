"""The confirmation code as text.

The owner used to see only the QR picture; if the recipient's camera failed
there was nothing to read out loud. The code is now in ExchangeOut — but only
for the owner: giving it to the recipient would let them complete the exchange
without ever meeting.
"""


def make_exchange(client, make_user, make_listing):
    owner, requester = make_user("Owner"), make_user("Requester")
    listing = make_listing(owner)
    reservation = client.post(
        f"/listings/{listing['id']}/reservations", headers=requester["headers"]
    ).json()
    accepted = client.patch(
        f"/reservations/{reservation['id']}", headers=owner["headers"], json={"action": "accept"}
    ).json()
    return owner, requester, accepted["exchange_id"]


def test_owner_sees_the_code_as_text(client, make_user, make_listing):
    owner, _requester, exchange_id = make_exchange(client, make_user, make_listing)

    body = client.get(f"/exchanges/{exchange_id}", headers=owner["headers"]).json()

    assert body["role"] == "owner"
    assert body["qr_code"], "owner needs the code text to read it out loud"


def test_requester_never_gets_the_code(client, make_user, make_listing):
    _owner, requester, exchange_id = make_exchange(client, make_user, make_listing)

    body = client.get(f"/exchanges/{exchange_id}", headers=requester["headers"]).json()

    assert body["role"] == "requester"
    assert body["qr_code"] is None


def test_the_code_actually_verifies_the_exchange(client, make_user, make_listing):
    owner, requester, exchange_id = make_exchange(client, make_user, make_listing)
    code = client.get(f"/exchanges/{exchange_id}", headers=owner["headers"]).json()["qr_code"]

    resp = client.post("/exchanges/verify", headers=requester["headers"], json={"qr_uuid": code})

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "completed"

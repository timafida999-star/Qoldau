def reserve_and_accept(client, owner, requester, listing_id):
    res = client.post(f"/listings/{listing_id}/reservations", headers=requester["headers"]).json()
    client.patch(f"/reservations/{res['id']}", headers=owner["headers"], json={"action": "accept"})
    return res


def test_reservation_request_notifies_owner_only(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)

    client.post(f"/listings/{listing['id']}/reservations", headers=requester["headers"])

    assert client.get("/notifications/unread-count", headers=owner["headers"]).json()["count"] == 1
    assert client.get("/notifications/unread-count", headers=requester["headers"]).json()["count"] == 0

    notif = client.get("/notifications", headers=owner["headers"]).json()[0]
    assert notif["type"] == "reservation_requested"
    assert notif["entity_title"] == listing["title"]


def test_accept_notifies_requester(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    reserve_and_accept(client, owner, requester, listing["id"])

    types = [n["type"] for n in client.get("/notifications", headers=requester["headers"]).json()]
    assert "reservation_accepted" in types


def test_mark_read_and_mark_all_read(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    client.post(f"/listings/{listing['id']}/reservations", headers=requester["headers"])

    notif = client.get("/notifications", headers=owner["headers"]).json()[0]
    client.post(f"/notifications/{notif['id']}/read", headers=owner["headers"])
    assert client.get("/notifications/unread-count", headers=owner["headers"]).json()["count"] == 0

    # generate another, then mark-all
    client.post(f"/listings/{listing['id']}/reservations", headers=make_user()["headers"])
    assert client.get("/notifications/unread-count", headers=owner["headers"]).json()["count"] == 1
    client.post("/notifications/read-all", headers=owner["headers"])
    assert client.get("/notifications/unread-count", headers=owner["headers"]).json()["count"] == 0


def test_cannot_mark_another_users_notification(client, make_user, make_listing):
    owner, requester = make_user(), make_user()
    listing = make_listing(owner)
    client.post(f"/listings/{listing['id']}/reservations", headers=requester["headers"])

    owner_notif = client.get("/notifications", headers=owner["headers"]).json()[0]
    resp = client.post(f"/notifications/{owner_notif['id']}/read", headers=requester["headers"])
    assert resp.status_code == 404

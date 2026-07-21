from app.models.user import User


def make_admin(db, make_user):
    """Register a user, then flip is_admin directly (there is no admin signup)."""
    admin = make_user("Admin")
    db.query(User).filter(User.id == admin["id"]).update({User.is_admin: True})
    db.commit()
    return admin


def test_user_can_report_listing(client, make_user, make_listing):
    owner, reporter = make_user(), make_user()
    listing = make_listing(owner)

    resp = client.post(
        "/reports",
        headers=reporter["headers"],
        json={"target_type": "listing", "target_id": listing["id"], "reason": "spam", "description": "junk"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "open"


def test_non_admin_cannot_list_reports(client, make_user):
    user = make_user()
    assert client.get("/admin/reports", headers=user["headers"]).status_code == 403


def test_admin_can_view_and_resolve_reports(client, db, make_user, make_listing):
    owner, reporter = make_user(), make_user()
    admin = make_admin(db, make_user)
    listing = make_listing(owner)
    report = client.post(
        "/reports",
        headers=reporter["headers"],
        json={"target_type": "listing", "target_id": listing["id"], "reason": "fraud"},
    ).json()

    open_reports = client.get("/admin/reports", headers=admin["headers"], params={"status": "open"})
    assert open_reports.status_code == 200
    assert any(r["id"] == report["id"] for r in open_reports.json())

    resolved = client.patch(f"/admin/reports/{report['id']}", headers=admin["headers"])
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


def test_admin_can_delete_listing(client, db, make_user, make_listing):
    owner = make_user()
    admin = make_admin(db, make_user)
    listing = make_listing(owner)

    resp = client.delete(f"/admin/listings/{listing['id']}", headers=admin["headers"])
    assert resp.status_code == 204
    assert client.get(f"/listings/{listing['id']}").status_code == 404

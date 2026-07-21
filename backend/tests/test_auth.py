def test_register_returns_token(client):
    resp = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123", "full_name": "Alice"},
    )
    assert resp.status_code == 201
    assert resp.json()["access_token"]


def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "password": "password123", "full_name": "Dup"}
    assert client.post("/auth/register", json=payload).status_code == 201
    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400


def test_login_success_and_wrong_password(client, make_user):
    user = make_user(email="bob@example.com", password="password123")

    ok = client.post("/auth/login", json={"email": user["email"], "password": "password123"})
    assert ok.status_code == 200
    assert ok.json()["access_token"]

    bad = client.post("/auth/login", json={"email": user["email"], "password": "wrong"})
    assert bad.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_current_user(client, make_user):
    user = make_user(full_name="Carol")
    me = client.get("/auth/me", headers=user["headers"])
    assert me.status_code == 200
    assert me.json()["full_name"] == "Carol"
    assert me.json()["is_admin"] is False


def test_forged_token_with_wrong_secret_rejected(client, make_user):
    from jose import jwt

    user = make_user()
    forged = jwt.encode({"sub": user["id"]}, "some-other-secret", algorithm="HS256")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401

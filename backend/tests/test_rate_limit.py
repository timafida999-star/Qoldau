"""Rate limiting is disabled for the suite (see conftest); this test flips it on
to prove the login limiter returns 429 with CORS headers intact."""
from app.rate_limit import limiter


def test_login_is_rate_limited(client, make_user):
    user = make_user(email="brute@example.com", password="password123")

    limiter.enabled = True
    try:
        statuses = [
            client.post(
                "/auth/login",
                json={"email": user["email"], "password": "wrong-guess"},
                headers={"Origin": "http://localhost:5173"},
            )
            for _ in range(12)  # limit is 10/minute
        ]
        codes = [r.status_code for r in statuses]

        # The first several attempts return 401 (bad password), then the limiter kicks in.
        assert 401 in codes
        assert 429 in codes

        limited = next(r for r in statuses if r.status_code == 429)
        assert limited.json()["detail"]
        assert limited.headers.get("Retry-After") == "60"
        # 429 must still carry CORS headers (unlike an unhandled 500).
        assert limited.headers.get("access-control-allow-origin") == "http://localhost:5173"
    finally:
        limiter.enabled = False
        limiter.reset()

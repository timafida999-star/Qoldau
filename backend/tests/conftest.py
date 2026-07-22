"""Test configuration.

Uses a dedicated ``qoldau_test`` Postgres database (the models rely on
Postgres-specific UUID and ENUM types, so SQLite is not an option). Each test
runs inside a transaction that is rolled back at the end, so tests are fully
isolated and never leave data behind.
"""
import os
import tempfile
import uuid

# Environment must be set before importing anything under app.*, because
# app.config.Settings() and the SQLAlchemy engine are built at import time.
BASE_DB_URL = os.environ.get("DATABASE_URL", "postgresql://qoldau:qoldau@db:5432/qoldau")
_prefix, _, _base_name = BASE_DB_URL.rpartition("/")
TEST_DB_URL = f"{_prefix}/qoldau_test"
ADMIN_DB_URL = f"{_prefix}/{_base_name}"  # an existing DB we can connect to, to create the test DB

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-definitely-long-enough-1234567890"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="qoldau_test_uploads_")
# Disable rate limiting by default so the suite's rapid requests aren't throttled;
# the dedicated rate-limit test re-enables it explicitly.
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database.base import Base  # noqa: E402
from app.database.session import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import *  # noqa: E402,F401,F403  ensure all models are registered on Base


@pytest.fixture(scope="session", autouse=True)
def _create_test_database():
    """Create a clean qoldau_test database with all tables, once per session."""
    admin_engine = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS qoldau_test WITH (FORCE)"))
        conn.execute(text("CREATE DATABASE qoldau_test"))
    admin_engine.dispose()

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


@pytest.fixture
def db(_create_test_database):
    """A session wrapped in a rolled-back transaction for perfect isolation.

    ``join_transaction_mode="create_savepoint"`` lets router code call
    ``session.commit()`` normally while the outer transaction still rolls
    everything back at the end of the test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


class _PrefixedClient:
    """Wraps TestClient to prepend the /api prefix, so tests can keep using
    resource paths like "/auth/login" while the app serves everything under /api."""

    def __init__(self, client: TestClient, prefix: str = "/api"):
        self._client = client
        self._prefix = prefix

    def _path(self, url: str) -> str:
        return f"{self._prefix}{url}"

    def get(self, url, **kwargs):
        return self._client.get(self._path(url), **kwargs)

    def post(self, url, **kwargs):
        return self._client.post(self._path(url), **kwargs)

    def patch(self, url, **kwargs):
        return self._client.patch(self._path(url), **kwargs)

    def put(self, url, **kwargs):
        return self._client.put(self._path(url), **kwargs)

    def delete(self, url, **kwargs):
        return self._client.delete(self._path(url), **kwargs)


@pytest.fixture
def client(db):
    """A TestClient whose requests share the test's rolled-back session."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield _PrefixedClient(test_client)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(client):
    """Factory: register a user and return {token, id, headers, email}."""
    def _make_user(full_name="Test User", email=None, password="password123"):
        email = email or f"user-{uuid.uuid4().hex[:8]}@example.com"
        resp = client.post(
            "/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        assert resp.status_code == 201, resp.text
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = client.get("/auth/me", headers=headers).json()["id"]
        return {"token": token, "id": user_id, "headers": headers, "email": email, "password": password}

    return _make_user


@pytest.fixture
def make_listing(client):
    """Factory: create a listing owned by the given user, return its JSON."""
    def _make_listing(owner, title="Wooden chair", category="furniture", condition="good"):
        resp = client.post(
            "/listings",
            headers=owner["headers"],
            json={
                "title": title,
                "description": "A sturdy item in decent shape.",
                "category": category,
                "condition": condition,
                "latitude": 43.238,
                "longitude": 76.945,
                "address_text": "KBTU",
            },
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make_listing

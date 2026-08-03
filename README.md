# Qoldau

A platform for giving away useful items for free. Users publish listings, others reserve them,
arrange the handoff through in-app chat, confirm the exchange with a QR code, and leave reviews.
The UI is available in **English, Russian, and Kazakh**.

> **Branches:** `main` is the local **development** setup (this README). `prod` carries the
> **production** deployment (prefixed services, internal nginx, subpath support) — see the README
> on the `prod` branch for deployment. Application code is shared; merge `main` into `prod` to
> ship changes.

## Stack

- **Frontend:** React, TypeScript, Vite, React Router, Axios, Tailwind CSS, shadcn/ui-style
  components, React Hook Form + Zod, Leaflet (OpenStreetMap) with marker clustering, jsQR
  (camera QR scanning), i18next (EN/RU/KK), light/dark theme, route-level code splitting.
- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic, JWT auth, WebSockets (chat), qrcode,
  Pillow (image validation + thumbnails), slowapi (rate limiting).
- **DevOps:** Docker Compose (Postgres + backend + frontend).

## Quick start (Docker)

```bash
# 1. Env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. REQUIRED — generate a JWT secret and paste it into backend/.env as JWT_SECRET_KEY.
#    The backend refuses to start with an empty or weak secret.
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 3. Start everything (migrations run automatically on backend start)
docker compose up --build
```

| Service      | URL                                   | Host port    |
|--------------|---------------------------------------|--------------|
| Frontend     | http://localhost:5173                 | 5173         |
| Backend API  | http://localhost:8000/api             | 8000         |
| API docs     | http://localhost:8000/api/docs        | (Swagger UI) |
| Postgres     | localhost:5433                        | 5433 → 5432  |

**Health check:** `GET http://localhost:8000/api/health` → `{"status":"ok"}`.
Postgres has a `pg_isready` healthcheck, and the backend waits for it before starting.

## Environment variables

Copy the `.env.example` files and adjust — they list every variable you need to set.

**`backend/.env`**

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string. Dev points at the `db` service. |
| `JWT_SECRET_KEY` | **Required.** Strong random secret (≥32 chars). Generate with the command above; the app fails to start otherwise. |
| `JWT_ALGORITHM` | JWT signing algorithm (default `HS256`). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes. |
| `UPLOAD_DIR` | Directory for uploaded images. |
| `RATE_LIMIT_ENABLED` | Toggle API rate limiting (default `true`). |
| `CORS_ORIGINS` | Comma-separated allowed origins (dev: `http://localhost:5173`). |

**`frontend/.env`**

| Variable | Description |
|---|---|
| `VITE_API_URL` | Base URL of the API (dev: `http://localhost:8000/api`). |

## Running without Docker

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL + a real JWT_SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Testing

The backend has a pytest suite of **133 tests**. They run against a dedicated `qoldau_test`
database, and each test is wrapped in a transaction that is rolled back afterwards, so they are
fully isolated and leave no data behind.

```bash
docker compose exec backend pip install -r requirements-dev.txt
docker compose exec backend pytest
```
Run a single suite with `docker compose exec backend pytest tests/test_auth.py`.

## Logs

```bash
docker compose logs -f backend     # follow backend (uvicorn) logs
docker compose logs -f             # all services
```

## Making a user an admin

There's no signup flow for admins by design. Promote an existing user directly in the database:

```bash
docker compose exec db psql -U qoldau -d qoldau \
  -c "UPDATE users SET is_admin = true WHERE email = 'you@example.com';"
```

Admins get an "Admin" link in the navbar and can view/resolve reports and delete listings at `/admin`.

## Project layout

```
backend/app/
  routers/    FastAPI route handlers (auth, users, listings, reservations, chat,
              exchanges, reviews, reports, admin, notifications)
  models/     SQLAlchemy models
  schemas/    Pydantic request/response models
  auth/       JWT + password hashing + auth dependencies
  database/   engine/session/declarative base
  websocket/  chat connection manager, WS route, message size/rate limits
  utils/      file upload/validation/thumbnails, QR code generation, notifications,
              geo.py (distance + meeting-point privacy)
  rate_limit.py, config.py, main.py
backend/tests/   pytest suite

frontend/src/
  pages/       route-level components
  components/  shared UI (incl. components/ui = shadcn-style primitives)
  api/         axios calls per resource
  hooks/       useAuth, useChatSocket, useTheme
  lib/         apiError (normalises API errors), leaflet icons, helpers
  i18n/        translations (en, ru, kk)
  types/       shared TypeScript types
  utils/       label maps, time formatting
```

## Features

**Auth** — register, login, logout, JWT, edit profile, avatar upload. Rate-limited login/register.

**Listings** — create/edit/delete, multi-image upload (validated, re-encoded, thumbnailed),
category + condition, map location picker (Leaflet), status (available/reserved/completed),
search + pagination.

**Home** — grid and map views, filter by category and status, text search, "near me" filter with a
radius, marker clustering on the map, "load more" pagination.

**Meeting-point privacy** — the exact location is only revealed to the owner and to a requester
whose request was accepted. Everyone else sees a deterministically offset point inside a ~500 m
circle, so the map never becomes a directory of home addresses. The radius filter still measures
distance against the real coordinates, so results stay accurate.

**Reservations** — request to reserve with an optional "why me?" message; the owner compares the
requests side by side (message, rating, review count) and picks a recipient. Accepting auto-creates
a chat and an exchange, and auto-declines the other pending requests. Either side can cancel an
accepted reservation until the handoff, which returns the listing to available.

**Chat** — real-time WebSocket messaging per reservation, message history, timestamps, automatic
reconnect on connection loss, message size and rate limits.

**Exchange confirmation** — owner shows a generated QR code; recipient confirms via live camera
scan (jsQR) or by entering the code, which marks the exchange (and listing) completed. The code is
also available as copyable text for when the camera isn't usable.

**Reviews** — 1–5 star rating + comment after a completed exchange; updates the reviewee's cached
average rating; shown on profile pages.

**Notifications** — in-app bell with unread count for reservation, chat, exchange, and review events.

**Reports & admin** — report a listing or user; admins view open/resolved reports at `/admin`,
resolve reports, and delete inappropriate listings.

**Profile** — public profiles with tabs (Listings / Given / Reviews), avatar, bio, rating.

**Internationalisation** — full UI in English, Russian, and Kazakh, with a language switcher.

**Interface resilience** — responsive layout with a burger menu on mobile, a 404 page for unknown
routes, and an error boundary so a failure on one page leaves the rest of the site usable instead
of blanking the screen.

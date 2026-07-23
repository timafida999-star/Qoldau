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
  components, React Hook Form + Zod, Leaflet (OpenStreetMap), jsQR (camera QR scanning),
  i18next (EN/RU/KK), light/dark theme.
- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic, JWT auth, WebSockets (chat), qrcode,
  Pillow (image validation), slowapi (rate limiting).
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

Copy the `.env.example` files and adjust. Each variable is documented in the example files.

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

The backend has a pytest suite covering auth, listings, the full reservation → QR exchange →
review lifecycle, notifications, admin/reports, pagination, and the security hardening (JWT secret
validation, image-upload sanitising, rate limiting). Tests run against a dedicated `qoldau_test`
database and roll back after each test.

```bash
docker compose exec backend pip install -r requirements-dev.txt
docker compose exec backend pytest
```

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
  websocket/  chat connection manager + WS route
  utils/      file upload/validation, QR code generation, notifications
  rate_limit.py, config.py, main.py
backend/tests/   pytest suite

frontend/src/
  pages/       route-level components
  components/  shared UI (incl. components/ui = shadcn-style primitives)
  api/         axios calls per resource
  hooks/       useAuth, useChatSocket, useTheme
  i18n/        translations (en, ru, kk)
  types/       shared TypeScript types
  utils/       label maps, time formatting
```

## Features

**Auth** — register, login, logout, JWT, edit profile, avatar upload. Rate-limited login/register.

**Listings** — create/edit/delete, multi-image upload (validated + re-encoded), category +
condition, map location picker (Leaflet), status (available/reserved/completed), search + pagination.

**Home** — grid and map views, filter by category and status, text search, "load more" pagination.

**Reservations** — request to reserve, owner accepts/declines, requester cancels; accepting
auto-creates a chat and a QR exchange, and auto-declines other pending requests on that listing.

**Chat** — real-time WebSocket messaging per reservation, message history, timestamps.

**QR exchange** — owner shows a generated QR code; recipient confirms via live camera scan (jsQR)
or manual code entry, which marks the exchange (and listing) completed.

**Reviews** — 1–5 star rating + comment after a completed exchange; updates the reviewee's cached
average rating; shown on profile pages.

**Notifications** — in-app bell with unread count for reservation, chat, exchange, and review events.

**Reports & admin** — report a listing or user; admins view open/resolved reports at `/admin`,
resolve reports, and delete inappropriate listings.

**Profile** — public profiles with tabs (Listings / Given / Reviews), avatar, bio, rating.

**Internationalisation** — full UI in English, Russian, and Kazakh, with a language switcher.

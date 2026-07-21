# Qoldau

A platform for giving away useful items for free. Users publish listings, others reserve them,
arrange the handoff through in-app chat, confirm the exchange with a QR code, and leave reviews.

## Status

All core MVP features are implemented end-to-end on both backend and frontend: auth, listings,
reservations, real-time chat, QR exchange confirmation, reviews, and reports/admin.

## Stack

- **Frontend:** React, TypeScript, Vite, React Router, Axios, Tailwind CSS, shadcn/ui-style
  components, React Hook Form + Zod, Leaflet, jsQR (camera QR scanning).
- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic, JWT auth, WebSockets, qrcode.
- **DevOps:** Docker Compose (Postgres + backend + frontend).

## Running locally with Docker

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

- Backend API: http://localhost:8000 (interactive docs at `/docs`)
- Frontend: http://localhost:5173
- Postgres: localhost:5433 (user/pass/db: `qoldau`)

Database migrations (`alembic upgrade head`) run automatically when the backend
container starts, so the schema is created on first boot — no manual step needed.

## Running without Docker

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # point DATABASE_URL at your local Postgres
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

The backend has a pytest suite covering auth, listings, the full reservation →
QR exchange → review lifecycle, notifications, admin/reports, and the security
hardening (JWT secret validation and image-upload sanitising). Tests run against
a dedicated `qoldau_test` database and roll back after each test.

With the stack running (`docker compose up`):

```bash
docker compose exec backend pip install -r requirements-dev.txt
docker compose exec backend pytest
```

## Making a user an admin

There's no signup flow for admins by design. Promote an existing user directly in the database:

```sql
UPDATE users SET is_admin = true WHERE email = 'you@example.com';
```

Admins get an "Admin" link in the navbar and can view/resolve reports and delete listings at `/admin`.

## Project layout

```
backend/app/
  routers/    FastAPI route handlers (auth, users, listings, reservations, chat, exchanges, reviews, reports, admin)
  models/     SQLAlchemy models
  schemas/    Pydantic request/response models
  auth/       JWT + password hashing + auth dependencies
  database/   engine/session/declarative base
  websocket/  chat connection manager + WS route
  utils/      file upload, QR code generation

frontend/src/
  pages/       route-level components
  components/  shared UI (incl. components/ui = shadcn-style primitives)
  api/         axios calls per resource
  hooks/       useAuth, useChatSocket
  types/       shared TypeScript types
  utils/       category/condition/status label maps
```

## Features

**Auth** — register, login, logout, JWT, edit profile, avatar upload.

**Listings** — create/edit/delete, multi-image upload, category + condition, map location picker
(Leaflet/OpenStreetMap), status (available/reserved/completed).

**Home** — grid and map views, filter by category and status.

**Reservations** — request to reserve, owner accepts/declines, requester cancels; accepting
auto-creates a chat and a QR exchange, and auto-declines other pending requests on that listing.

**Chat** — real-time WebSocket messaging per reservation, message history, timestamps.

**QR exchange** — owner shows a generated QR code; recipient confirms via live camera scan
(jsQR) or manual code entry, which marks the exchange (and listing) completed.

**Reviews** — 1–5 star rating + comment after a completed exchange; updates the reviewee's
cached average rating; shown on profile pages.

**Reports & admin** — report a listing or user; admins view open/resolved reports at `/admin`,
resolve reports, and delete inappropriate listings.

**Profile** — public profile pages (avatar, bio, rating, reviews); own profile is editable.

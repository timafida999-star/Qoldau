# Qoldau — Production (deploy branch)

A platform for giving away useful items for free: users publish listings, others reserve them,
arrange the handoff through in-app chat, confirm the exchange with a QR code, and leave reviews.
UI in English, Russian, and Kazakh.

> **This is the `prod` branch** — the production deployment for the shared `esg.kbtu.kz` server.
> The `main` branch holds the local dev setup. App code is shared; `git merge main` into `prod`
> to ship changes.

## Stack

- **Frontend:** React + TypeScript + Vite, served as static files by nginx.
- **Backend:** FastAPI (uvicorn), SQLAlchemy, Alembic, JWT auth, WebSockets (chat), slowapi
  (rate limiting), Pillow (image validation).
- **Database:** PostgreSQL 16.
- **Isolation:** Docker Compose. Three containers on the shared external `esg-network`.

## Services, ports & health checks

| Service          | Internal port | Published to host | Health check                         |
|------------------|---------------|-------------------|--------------------------------------|
| `qoldau-web`     | 80            | no (expose only)  | `GET /` (nginx)                      |
| `qoldau-backend` | 8000          | no (expose only)  | `GET /api/health` → `{"status":"ok"}`|
| `qoldau-db`      | 5432          | no (network only) | `pg_isready`                         |

The Public Nginx should proxy `esg.kbtu.kz/qoldau/` → `qoldau-web:80` (stripping `/qoldau`),
forwarding `Upgrade`/`Connection` headers so the chat WebSocket works.

## Environment variables

Two files, both **gitignored** — copy from the examples and fill in.

**`.env`** (root — Docker Compose auto-loads it)

| Variable | Description |
|---|---|
| `POSTGRES_USER` | Database user for `qoldau-db`. |
| `POSTGRES_PASSWORD` | **Unique**, strong DB password. Must match `DATABASE_URL` in `backend/.env`. |
| `POSTGRES_DB` | Database name. |
| `VITE_BASE_PATH` | Public subpath the app is served under, e.g. `/qoldau/` (trailing slash required). Baked into the frontend build. |

**`backend/.env`** (loaded into the backend container)

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql://<user>:<password>@qoldau-db:5432/<db>` — credentials must match root `.env`. |
| `JWT_SECRET_KEY` | **Required, unique.** ≥32-char random secret. Generate: `python -c "import secrets; print(secrets.token_urlsafe(64))"`. The app refuses to start otherwise. |
| `JWT_ALGORITHM` | JWT algorithm (default `HS256`). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime. |
| `UPLOAD_DIR` | Upload directory inside the container (default `uploads`). |
| `RATE_LIMIT_ENABLED` | Enable API rate limiting (default `true`). |
| `CORS_ORIGINS` | Comma-separated allowed origins. Empty in production (same-origin). |

## Deploy

```bash
# One-time
cp .env.example .env                   # set POSTGRES_PASSWORD, VITE_BASE_PATH=/qoldau/
cp backend/.env.example backend/.env   # set DATABASE_URL (matching password) + JWT_SECRET_KEY

# Deploy / update
git pull
docker compose up -d --build
```

## Logs

All services log to stdout/stderr (captured by Docker):

```bash
docker compose logs -f qoldau-backend    # uvicorn / app logs (follow)
docker compose logs -f qoldau-web        # nginx access/error logs
docker compose logs --tail=100           # recent logs, all services
```

## Resource estimate

Small footprint (idle -> light use):

| Container | RAM | CPU | Notes |
|---|---|---|---|
| `qoldau-db` | ~30–80 MB | negligible idle | grows with cache/connections |
| `qoldau-backend` | ~120–200 MB | < 0.3 vCPU typical | single uvicorn worker |
| `qoldau-web` | ~5–15 MB | negligible | static files via nginx |
| **Total** | **~250–400 MB** | **< 0.5 vCPU** typical, 1 vCPU is plenty | |

**Disk:** ~1.5–2.5 GB for images (postgres + python-slim + nginx + build layers), plus the
Postgres data volume and the uploads volume, which grow with usage (images capped at 5 MB each).
Budget ~5 GB to be comfortable.

## Making a user an admin

```bash
docker compose exec qoldau-db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "UPDATE users SET is_admin = true WHERE email = 'you@example.com';"
```

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.rate_limit import limiter, rate_limit_handler
from app.routers import (
    admin,
    auth,
    chat,
    exchanges,
    listings,
    notifications,
    reports,
    reservations,
    reviews,
    users,
)

# Everything the API serves lives under /api so it can be proxied cleanly behind
# a reverse proxy (the internal nginx forwards /api/ to this service). Docs and
# the OpenAPI schema move under /api too.
app = FastAPI(
    title="Qoldau API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Rate limiting: register the limiter on app.state and a 429 handler that keeps
# CORS headers. Limits are applied per-endpoint via @limiter.limit decorators
# (see routers/auth.py), which raise inside FastAPI's handled layer.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploaded files are served under /api/uploads. Stored image_url values are like
# "/uploads/...", and the frontend prefixes them with the API base (".../api"),
# so the two line up to ".../api/uploads/...".
app.mount("/api/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

api = APIRouter(prefix="/api")
api.include_router(auth.router)
api.include_router(users.router)
api.include_router(listings.router)
api.include_router(reservations.router)
api.include_router(reservations.listing_reservations_router)
api.include_router(chat.router)
api.include_router(chat.ws_router)
api.include_router(exchanges.router)
api.include_router(reviews.router)
api.include_router(notifications.router)
api.include_router(reports.router)
api.include_router(admin.router)


@api.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(api)

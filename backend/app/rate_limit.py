"""Rate limiting, keyed by client IP.

Uses slowapi with in-memory storage
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    enabled=settings.rate_limit_enabled,
)


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a friendly 429 with a Retry-After hint.

    Uses the ``detail`` key so the frontend surfaces it the same way as any
    other API error, and passes through CORS (unlike an unhandled 500).
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please wait a minute and try again shortly."},
        headers={"Retry-After": "60"},
    )

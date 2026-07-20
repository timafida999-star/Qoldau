from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
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

app = FastAPI(title="Qoldau API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(listings.router)
app.include_router(reservations.router)
app.include_router(reservations.listing_reservations_router)
app.include_router(chat.router)
app.include_router(chat.ws_router)
app.include_router(exchanges.router)
app.include_router(reviews.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

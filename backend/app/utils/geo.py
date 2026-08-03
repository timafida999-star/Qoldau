"""Distance math and meeting-point privacy.

Listings carry the exact meeting coordinates, but showing them to everyone
turns the map into a directory of "here is where a stranger with a free sofa
lives". Until the owner accepts a request, everyone else sees a point that is
deterministically offset from the real one.
"""
import hashlib
import hmac
import math
import uuid

EARTH_RADIUS_KM = 6371.0088

# The offset is drawn from [MIN, MAX] metres; the UI shows a circle of
# UNCERTAINTY_RADIUS_M around the offset point, so the real spot is always
# inside the circle (MAX_JITTER_M < UNCERTAINTY_RADIUS_M).
MIN_JITTER_M = 150
MAX_JITTER_M = 350
UNCERTAINTY_RADIUS_M = 500

_M_PER_DEG_LAT = 111_320.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points, in kilometres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def approximate_location(listing_id: uuid.UUID, lat: float, lng: float, secret: str) -> tuple[float, float]:
    """Deterministically blur a listing's coordinates.

    Deterministic per listing so repeated requests cannot be averaged back to
    the true point, and keyed with a server secret so the offset cannot be
    recomputed (and subtracted) by anyone reading this open-source algorithm.
    """
    digest = hmac.new(secret.encode(), str(listing_id).encode(), hashlib.sha256).digest()
    unit_a = int.from_bytes(digest[0:4], "big") / 0xFFFFFFFF
    unit_b = int.from_bytes(digest[4:8], "big") / 0xFFFFFFFF

    distance_m = MIN_JITTER_M + unit_a * (MAX_JITTER_M - MIN_JITTER_M)
    bearing = unit_b * 2 * math.pi

    dlat = (distance_m * math.cos(bearing)) / _M_PER_DEG_LAT
    # Metres per degree of longitude shrink with latitude; clamp for sanity near the poles.
    m_per_deg_lng = _M_PER_DEG_LAT * max(math.cos(math.radians(lat)), 0.01)
    dlng = (distance_m * math.sin(bearing)) / m_per_deg_lng

    return round(lat + dlat, 5), round(lng + dlng, 5)

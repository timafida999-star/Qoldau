"""Length-bounded types shared by the request schemas.
"""
from typing import Annotated

from pydantic import EmailStr, Field, StringConstraints


def _text(*, min_length: int = 0, max_length: int) -> StringConstraints:
    return StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length)


# --- identity ---------------------------------------------------------------

FullName = Annotated[str, _text(min_length=2, max_length=100)]
Email = Annotated[EmailStr, Field(max_length=254)]  # RFC 5321 maximum

NewPassword = Annotated[str, Field(min_length=8, max_length=128)]

ExistingPassword = Annotated[str, Field(max_length=128)]

# --- profile ----------------------------------------------------------------

Phone = Annotated[str, _text(max_length=32)]
Bio = Annotated[str, _text(max_length=500)]

# --- listings ---------------------------------------------------------------

ListingTitle = Annotated[str, _text(min_length=3, max_length=120)]
ListingDescription = Annotated[str, _text(min_length=10, max_length=5000)]
AddressText = Annotated[str, _text(max_length=200)]

Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]

# --- free text attached to reviews and reports ------------------------------

Comment = Annotated[str, _text(max_length=1000)]

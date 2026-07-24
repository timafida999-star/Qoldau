from pydantic import BaseModel

from app.schemas.fields import Email, ExistingPassword


class LoginRequest(BaseModel):
    email: Email
    password: ExistingPassword


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

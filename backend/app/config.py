from pydantic import field_validator
from pydantic_settings import BaseSettings

WEAK_SECRET_MARKERS = ("change-this", "change-me", "changeme", "placeholder", "your-secret")


class Settings(BaseSettings):
    database_url: str = "postgresql://qoldau:qoldau@db:5432/qoldau"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    upload_dir: str = "uploads"
    max_upload_bytes: int = 5 * 1024 * 1024  # 5 MB per image

    class Config:
        env_file = ".env"

    @field_validator("jwt_secret_key")
    @classmethod
    def reject_weak_secret(cls, value: str) -> str:
        """Fail closed: refuse to start with a missing, short, or placeholder secret.

        The JWT secret is the only thing stopping anyone from forging a token for
        any user, so a weak value must break startup rather than silently
        downgrade authentication to "anyone can log in as anyone".
        """
        if not value or len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must be set to a random value of at least 32 characters")
        if any(marker in value.lower() for marker in WEAK_SECRET_MARKERS):
            raise ValueError("JWT_SECRET_KEY looks like a placeholder; generate a real random secret")
        return value


settings = Settings()

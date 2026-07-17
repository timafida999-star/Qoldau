from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://qoldau:qoldau@db:5432/qoldau"
    jwt_secret_key: str = "change-this-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    upload_dir: str = "uploads"

    class Config:
        env_file = ".env"


settings = Settings()

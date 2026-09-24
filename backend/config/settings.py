from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://writoauth:password@postgres:5432/writoauth_db"
    )
    # No hardcoded default: secrets must never ship with an insecure fallback.
    # The app fails loudly at startup if JWT_SECRET_KEY isn't set.
    jwt_secret: str = Field(validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    # 0-100 consistency-score threshold below which a submission is flagged.
    analysis_flag_threshold: float = 75.0
    # Largest document accepted by /api/papers/extract. Student essays
    # are tiny; this cap exists to stop a large upload occupying a
    # request worker, not because bigger files are meaningful.
    max_upload_bytes: int = 10 * 1024 * 1024
    # Comma-separated list of allowed CORS origins (not a secret - a normal
    # local-dev default is fine). e.g. "https://app.example.com,https://foo.com"
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://writoauth:password@mysql:3306/writoauth_db"
    # No hardcoded default: secrets must never ship with an insecure fallback.
    # The app fails loudly at startup if JWT_SECRET_KEY isn't set.
    jwt_secret: str = Field(validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    # 0-100 consistency-score threshold below which a submission is flagged.
    analysis_flag_threshold: float = 75.0

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()

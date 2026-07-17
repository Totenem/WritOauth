from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://writoauth:password@mysql:3306/writoauth_db"
    jwt_secret: str = Field(
        default="ryturdfytgafshgfvhasj", validation_alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = "HS256"
    chroma_db_path: str = "/app/data/chromadb"
    hf_model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    top_k: int = 3
    max_context: int = 4096

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = "your-api-key-here"
    openai_base_url: str = ""

    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    data_dir: str = "./data"

    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 4
    max_tokens: int = 512

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def chroma_path(self) -> str:
        return str(self.data_path / "chroma")

    @property
    def sqlite_url(self) -> str:
        return f"sqlite:///{self.data_path / 'app.sqlite3'}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ACE_",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    app_name: str = "AI Conversation Evaluator"
    env: Literal["local", "test", "production"] = "local"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    root_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    facet_config_path: Path = Path("configs/facets.example.json")
    synthetic_dataset_path: Path = Path("data/synthetic_conversations.json")
    evaluator_backend: str = "mock"
    storage_backend: Literal["sqlalchemy", "memory"] = "sqlalchemy"
    database_url: str = "sqlite:///data/evaluations.db"
    postgres_db: str | None = Field(default=None, validation_alias=AliasChoices("POSTGRES_DB", "ACE_POSTGRES_DB"))
    postgres_host: str | None = Field(default=None, validation_alias=AliasChoices("POSTGRES_HOST", "ACE_POSTGRES_HOST"))
    postgres_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("POSTGRES_PASSWORD", "ACE_POSTGRES_PASSWORD"),
    )
    postgres_port: int | None = Field(default=None, validation_alias=AliasChoices("POSTGRES_PORT", "ACE_POSTGRES_PORT"))
    postgres_user: str | None = Field(default=None, validation_alias=AliasChoices("POSTGRES_USER", "ACE_POSTGRES_USER"))
    facet_batch_size: int = 25
    max_facets_per_request: int = 5000
    trace_enabled: bool = True
    model_cache_size: int = 2
    qwen_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    llama_model_name: str = "meta-llama/Llama-3.2-3B-Instruct"
    mixtral_model_name: str = "mistralai/Ministral-8B-Instruct-2410"
    generation_max_new_tokens: int = 768
    generation_temperature: float = 0.0
    redis_url: str = "redis://redis:6379/0"

    @property
    def resolved_facet_config_path(self) -> Path:
        return self._resolve_path(self.facet_config_path)

    @property
    def resolved_synthetic_dataset_path(self) -> Path:
        return self._resolve_path(self.synthetic_dataset_path)

    @property
    def resolved_database_url(self) -> str:
        if self.database_url == "sqlite:///data/evaluations.db" and self.postgres_db:
            host = self.postgres_host or "localhost"
            port = self.postgres_port or 5432
            user = self.postgres_user or "postgres"
            password = self.postgres_password or ""
            return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{self.postgres_db}"
        if not self.database_url.startswith("sqlite:///"):
            return self.database_url
        raw_path = self.database_url.removeprefix("sqlite:///")
        path = Path(raw_path)
        if path == Path(":memory:"):
            return self.database_url
        resolved = self._resolve_path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{resolved}"

    def _resolve_path(self, path: Path) -> Path:
        return path if path.is_absolute() else self.root_dir / path


@lru_cache
def get_settings() -> Settings:
    return Settings()

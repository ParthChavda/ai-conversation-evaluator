from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
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
    facet_config_path: Path = Path("configs/facets.assignment.json")
    synthetic_dataset_path: Path = Path("data/synthetic_conversations.json")
    evaluator_backend: Literal["qwen"] = "qwen"
    storage_backend: Literal["sqlalchemy", "memory"] = "sqlalchemy"
    database_url: str = "sqlite:///data/evaluations.db"
    facet_batch_size: int = 5
    max_facets_per_request: int = 5000
    trace_enabled: bool = True
    model_cache_size: int = 2
    qwen_model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"
    generation_max_new_tokens: int = 1024
    generation_temperature: float = 0.0

    @property
    def resolved_facet_config_path(self) -> Path:
        return self._resolve_path(self.facet_config_path)

    @property
    def resolved_synthetic_dataset_path(self) -> Path:
        return self._resolve_path(self.synthetic_dataset_path)

    @property
    def resolved_database_url(self) -> str:
        if not self.database_url.startswith("sqlite:///"):
            raise ValueError(
                "Only sqlite:/// database URLs are supported by the demo baseline"
            )
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

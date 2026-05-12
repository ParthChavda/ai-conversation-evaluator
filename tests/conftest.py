import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("ACE_ENV", "test")
    monkeypatch.setenv("ACE_EVALUATOR_BACKEND", "mock")
    monkeypatch.setenv("ACE_STORAGE_BACKEND", "sqlalchemy")
    monkeypatch.setenv("ACE_DATABASE_URL", f"sqlite:///{tmp_path / 'test-evaluations.db'}")
    for key in ["POSTGRES_DB", "POSTGRES_HOST", "POSTGRES_PASSWORD", "POSTGRES_PORT", "POSTGRES_USER"]:
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

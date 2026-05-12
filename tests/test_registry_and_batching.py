from pathlib import Path

from app.facets.registry import FacetRegistry
from app.services.batch_engine import FacetBatchingEngine


def test_registry_loads_enabled_facets():
    registry = FacetRegistry.from_file(Path("configs/facets.example.json"))

    assert len(registry.all()) >= 10
    assert "safety" in registry.categories()


def test_batching_engine_chunks_facets():
    registry = FacetRegistry.from_file(Path("configs/facets.example.json"))
    engine = FacetBatchingEngine(batch_size=4)

    batches = list(engine.batches(registry.all()))

    assert len(batches) == 3
    assert [len(batch) for batch in batches] == [4, 4, 2]

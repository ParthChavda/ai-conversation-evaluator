from collections.abc import Iterator

from app.models.schemas import Facet


class FacetBatchingEngine:
    def __init__(self, batch_size: int):
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")
        self.batch_size = batch_size

    def batches(
        self, facets: list[Facet], batch_size: int | None = None
    ) -> Iterator[list[Facet]]:
        size = batch_size or self.batch_size
        if size < 1:
            raise ValueError("batch_size must be greater than zero")
        for index in range(0, len(facets), size):
            yield facets[index : index + size]

import json
from pathlib import Path
from typing import Iterable

import yaml

from app.models.schemas import Facet


class FacetRegistry:
    def __init__(self, facets: Iterable[Facet]):
        self._facets: dict[str, Facet] = {facet.facet_id: facet for facet in facets}

    @classmethod
    def from_file(cls, path: Path) -> "FacetRegistry":
        if not path.exists():
            raise FileNotFoundError(f"facet config not found: {path}")
        payload = _load_structured_file(path)
        raw_facets = payload.get("facets", payload if isinstance(payload, list) else [])
        return cls(Facet.model_validate(item) for item in raw_facets)

    def all(self, include_disabled: bool = False) -> list[Facet]:
        facets = list(self._facets.values())
        if include_disabled:
            return facets
        return [facet for facet in facets if facet.enabled]

    def get(self, facet_id: str) -> Facet | None:
        return self._facets.get(facet_id)

    def filter(
        self,
        facet_ids: list[str] | None = None,
        categories: list[str] | None = None,
        include_disabled: bool = False,
    ) -> list[Facet]:
        facets = self.all(include_disabled=include_disabled)
        if facet_ids:
            requested = set(facet_ids)
            facets = [facet for facet in facets if facet.facet_id in requested]
        if categories:
            requested_categories = {category.lower() for category in categories}
            facets = [facet for facet in facets if facet.category.lower() in requested_categories]
        return facets

    def categories(self) -> list[str]:
        return sorted({facet.category for facet in self._facets.values()})


def _load_structured_file(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(handle)
        return json.load(handle)

from collections import OrderedDict
from typing import Any


class ModelCache:
    def __init__(self, max_size: int = 2):
        self.max_size = max_size
        self._items: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Any | None:
        value = self._items.get(key)
        if value is not None:
            self._items.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        while len(self._items) > self.max_size:
            self._items.popitem(last=False)

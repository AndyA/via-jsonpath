from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Symbol:
    name: str

    def __str__(self):
        return self.name


def is_in(obj: Any, key: Any) -> bool:
    if isinstance(obj, dict):
        return key in obj

    if isinstance(obj, list):
        return isinstance(key, int) and 0 <= key < len(obj)

    return False


def kv_of(obj: Any) -> Iterable[tuple[Any, Any]]:
    if isinstance(obj, dict):
        return obj.items()

    if isinstance(obj, list):
        return enumerate(obj)

    return []


def cast_array(value: Any) -> list:
    return value if isinstance(value, list) else [value]

from dataclasses import dataclass, field
from typing import Any, Generator, Iterable

from typing_extensions import Self

from .jp import JP, JPField, JPRoot, JPSearch, JPWild

MatchGenerator = Generator[tuple[JP, Any, Self], None, None]


def is_in(obj: Any, key: Any) -> bool:
    if isinstance(obj, dict) and isinstance(key, str) and key in obj:
        return True

    if isinstance(obj, list) and isinstance(key, int) and 0 <= key < len(obj):
        return True

    return False


def kv_of(obj: Any) -> Iterable[tuple[Any, Any]]:
    if isinstance(obj, dict):
        return obj.items()

    if isinstance(obj, list):
        return enumerate(obj)

    return []


@dataclass(frozen=True, kw_only=True)
class TrieNode:
    next: dict[JPField, Self] = field(default_factory=dict)
    data: Any = None
    leaf: bool = False

    def search(self, obj: Any, path=JPRoot) -> MatchGenerator:
        yield from self.visit(obj, path)
        for idx, value in kv_of(obj):
            yield from self.search(value, path + (idx,))

    def visit(self, obj: Any, path=JPRoot) -> MatchGenerator:
        if self.leaf:
            yield path, obj, self

        if isinstance(obj, (list, dict)):
            for key, node in self.next.items():
                if key == JPSearch:
                    yield from node.search(obj, path)
                elif key == JPWild:
                    for idx, value in kv_of(obj):
                        yield from node.visit(value, path + (idx,))
                elif is_in(obj, key):
                    yield from node.visit(obj[key], path + (key,))

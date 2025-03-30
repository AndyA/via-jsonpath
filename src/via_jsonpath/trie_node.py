from dataclasses import dataclass, field
from typing import Any, Generator

from typing_extensions import Self

from via_jsonpath.tools import is_in, kv_of

from .jp import JP, JPField, JPRoot, JPSearch, JPWild

MatchGenerator = Generator[tuple[JP, Any, Self], None, None]


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

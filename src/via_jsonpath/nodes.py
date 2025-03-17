from dataclasses import dataclass, field
from typing import Any, Generator, Self

from .jp import JP, JPField, JPRoot, JPSearch, JPWild
from .sugar import is_in, kv_of

NodeWalk = Generator[tuple[JP, Any, Self], None, None]


@dataclass(frozen=True, kw_only=True)
class Node:
    next: dict[JPField, Self] = field(default_factory=dict)
    leaf = False

    def search(self, obj: Any, path) -> NodeWalk:
        yield from self.visit(obj, path)
        for idx, value in kv_of(obj):
            yield from self.search(value, path + (idx,))

    def visit(self, obj: Any, path=JPRoot) -> NodeWalk:
        if self.leaf:
            yield path, obj, self

        if isinstance(obj, dict) or isinstance(obj, list):
            for key, node in self.next.items():
                if key == JPSearch:
                    yield from node.search(obj, path)
                elif key == JPWild:
                    for idx, value in kv_of(obj):
                        yield from node.visit(value, path + (idx,))
                elif is_in(obj, key):
                    yield from node.visit(obj[key], path + (key,))


@dataclass(frozen=True, kw_only=True)
class LeafNode(Node):
    data: Any
    leaf = True

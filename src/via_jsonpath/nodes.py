from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Generator, Self

from .jp import JP, JPField, JPRoot, JPSearch, JPWild
from .sugar import is_in, kv_of


@dataclass(frozen=True, kw_only=True)
class InnerNode:
    next: dict[JPField, Self] = field(default_factory=dict)
    leaf = False

    @cached_property
    def items(self) -> list[tuple[JPField, Self]]:
        def key_fun(x):
            return type(x[0]).__name__, x[0]

        return sorted(self.next.items(), key=key_fun)

    def search(
        self, obj: Any, *, path=JPRoot
    ) -> Generator[tuple[JP, Self, Any], None, None]:
        yield from self.visit(obj, path=path)
        for idx, value in kv_of(obj):
            next_path = path + (idx,)
            yield from self.search(value, path=next_path)

    def visit(
        self, obj: Any, *, path=JPRoot
    ) -> Generator[tuple[JP, Self, Any], None, None]:
        if self.leaf:
            yield path, obj, self

        if isinstance(obj, dict) or isinstance(obj, list):
            for key, node in self.items:
                if key == JPSearch:
                    yield from node.search(obj, path=path)
                elif key == JPWild:
                    for idx, value in kv_of(obj):
                        yield from node.visit(value, path=path + (idx,))
                elif is_in(obj, key):
                    yield from node.visit(obj[key], path=path + (key,))


@dataclass(frozen=True, kw_only=True)
class LeafNode(InnerNode):
    data: Any
    leaf = True

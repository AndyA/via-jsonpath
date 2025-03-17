from functools import cached_property
from itertools import groupby

from .jp import JP, JPField
from .nodes import InnerNode, LeafNode


class Trie(dict):
    def _invalidate(self) -> None:
        try:
            del self.trie
        except AttributeError:
            pass

    def __setitem__(self, key: JP | str, value: InnerNode) -> None:
        super().__setitem__(JP(key), value)
        self._invalidate()

    def __delitem__(self, key: JP | str) -> None:
        super().__delitem__(JP(key))
        self._invalidate()

    def clear(self) -> None:
        super().clear()
        self._invalidate()

    def setdefault(self, key: JP | str, default: InnerNode) -> InnerNode:
        key = JP(key)
        sentinel = object()
        if (value := self.get(key, sentinel)) is sentinel:
            self[key] = value = default
        return value

    def __getitem__(self, key: JP | str) -> InnerNode:
        return super().__getitem__(JP(key))

    def __contains__(self, key: JP | str) -> bool:
        return super().__contains__(JP(key))

    @cached_property
    def trie(self) -> InnerNode:
        def make_next(items: list[tuple]) -> dict[JPField, InnerNode]:
            return {
                k: make_trie([item[1:] for item in g])
                for k, g in groupby(items, key=lambda p: p[0])
            }

        def make_trie(items: list[tuple]) -> InnerNode:
            if len(items[0]) == 1:  # Leaf?
                return LeafNode(next=make_next(items[1:]), data=items[0][0])
            else:
                return InnerNode(next=make_next(items))

        if items := [(*k, v) for k, v in sorted(self.items())]:
            return make_trie(items)

        # Fake root for empty Trie
        return InnerNode()

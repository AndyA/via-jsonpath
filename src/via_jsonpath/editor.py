from dataclasses import dataclass, field
from itertools import groupby
from typing import Any

from typing_extensions import Self

from .arena import claim
from .jp import JP, JPError, JPField
from .ref import Deleted, Ignored, Ref, container_type, ensure, peek, poke, trim_tail

ValueAtom = tuple[Any, int]
ValueSlot = ValueAtom | list[ValueAtom]


@dataclass
class IndexFountain:
    index: int = -1
    tree: dict[JPField, Self] = field(default_factory=dict)

    def allocate(self, path: JP) -> int:
        node = self
        for part in path:
            node = node.tree.setdefault(part, IndexFountain())
        node.index += 1
        return node.index

    def reset(self, path: JP) -> None:
        node = self
        for part in path:
            if (node := node.tree.get(part)) is None:
                return
        node.tree, node.index = {}, -1


@dataclass
class Editor:
    edits: dict[JP, ValueSlot] = field(default_factory=dict)
    _fountain: IndexFountain = field(default_factory=IndexFountain)
    _sequence: int = 1

    def set(self, key: JP | str, value: Any) -> None:
        if value == Ignored:
            return

        key = JP(key)
        if slots := key.bind_slots:
            if len(slots) > 1:
                raise JPError("Bad wildcard. Only one [*] is allowed")
            key = key.bind([self._fountain.allocate(key[: slots[0] + 1])])

        self.edits[key] = (value, self._sequence)
        self._fountain.reset(key)
        self._sequence += 1

    def edit(self, obj: Any = Deleted) -> Any:
        def assign(ref: Ref, path_values: list, cutoff: int = 0) -> None:
            if path_values and len(path_values[0]) == 1:
                # Reached the leaf, consider assignment
                value, seq = path_values[0][0]
                if seq > cutoff:
                    poke(ref, value)
                    cutoff = seq

                path_values = path_values[1:]

            next_ref = None
            for key, paths in groupby(path_values, lambda x: x[0]):
                if not next_ref:
                    next_ref = ensure(ref, container_type(key))
                assign((next_ref, key), [path[1:] for path in paths], cutoff)

            if next_ref:
                trim_tail(ref)

        root: Ref = (claim({"$": obj}), "$")
        path_values = [(*path, value) for path, value in sorted(self.edits.items())]
        assign(root, path_values)
        return peek(root)

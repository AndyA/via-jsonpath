from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from .jp import JPError


class NopArena:
    def _nop(self, obj: Any) -> Any:
        return obj

    is_not_ours = _nop
    is_ours = _nop
    claim = _nop
    adopt = _nop


@dataclass
class CheckedArena(NopArena):
    owned: set[int] = field(default_factory=set)

    def is_not_ours(self, obj: Any) -> Any:
        if id(obj) in self.owned:
            raise JPError(f"Already owned object {obj} ({id(obj)})")
        return obj

    def is_ours(self, obj: Any) -> Any:
        if id(obj) not in self.owned:
            raise JPError(f"Foreign object {obj} ({id(obj)})")
        return obj

    def claim(self, obj: Any) -> Any:
        self.owned.add(id(obj))
        return obj

    def adopt(self, obj: Any) -> Any:
        return self.claim(self.is_not_ours(obj))


_arena = NopArena()


@contextmanager
def caution():
    global _arena
    # Already cautious?
    if isinstance(_arena, CheckedArena):
        yield _arena.owned
        return

    saved = _arena
    try:
        _arena = CheckedArena()
        yield _arena.owned
    finally:
        _arena = saved


def is_ours(obj: Any) -> Any:
    return _arena.is_ours(obj)


def is_not_ours(obj: Any) -> Any:
    return _arena.is_not_ours(obj)


def adopt(obj: Any) -> Any:
    return _arena.adopt(obj)


def claim(obj: Any) -> Any:
    return _arena.claim(obj)

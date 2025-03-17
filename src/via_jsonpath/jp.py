import json
import re
from functools import cached_property, total_ordering
from itertools import takewhile
from typing import Any, Generator, Sequence

from .sugar import Symbol

JPWild = Symbol("JPWild")
JPSearch = Symbol("JPSearch")
JPField = str | int | Symbol
JPTuple = tuple[JPField, ...]


def is_wildcard(field: JPField) -> bool:
    return field in {JPWild, JPSearch}


class JPError(ValueError):
    pass


@total_ordering
class JP(JPTuple):
    """
    A JSONPath path
    """

    JP_TOKENS = re.compile(r"(\$|\\.|\.+|[\"\[\]])")
    JP_KEY = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    def __new__(cls, path: str | JPTuple) -> "JP":
        if isinstance(path, cls):
            return path
        if isinstance(path, str):
            path = (*cls._parse_path(path),)
        return tuple.__new__(cls, path)

    @cached_property
    def _key(self) -> tuple:
        return tuple((type(f).__name__, f) for f in self)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return self._key < other._key
        return NotImplemented

    @classmethod
    def _parse_path(cls, path: str) -> Generator[JPField, None, None]:
        splits = re.split(cls.JP_TOKENS, path)
        tokens = (tok for tok in splits if len(tok))

        def need_tok():
            if (tok := next(tokens, None)) is None:
                raise JPError("Unexpected end of path")
            return tok

        def expect_tok(want):
            if (tok := need_tok()) != want:
                raise JPError(f"Expected {want}, got {tok}")
            return tok

        def parse_index() -> JPField:
            if (tok := need_tok()) == "*":
                return JPWild

            if tok == '"':
                str = "".join([*takewhile(lambda t: t != '"', tokens)])
                return json.loads(f'"{str}"')

            try:
                return int(tok)
            except ValueError:
                raise JPError(f"Expected index, got {tok}")

        tok = expect_tok("$")

        for tok in tokens:
            want_field = False
            if tok in {".", ".."}:
                if tok == "..":
                    yield JPSearch
                want_field = True
                tok = need_tok()

            if tok == "[":
                yield parse_index()
                tok = expect_tok("]")
                continue

            if want_field:
                if tok == "*":
                    yield JPWild
                    continue
                elif cls.JP_KEY.match(tok):
                    yield tok
                    continue

            raise JPError(f"Unexpected {tok}")

    @cached_property
    def _str(self):
        parts = ["$"]
        for field in self:
            if field == JPSearch:
                parts.append("..")
            elif field == JPWild:
                parts.append("[*]")
            elif isinstance(field, int):
                parts.append(f"[{field}]")
            elif re.match(self.JP_KEY, field):
                if parts[-1] != "..":
                    parts.append(".")
                parts.append(field)
            else:
                parts.append(f"[{json.dumps(field)}]")
        return "".join(parts)

    def __str__(self) -> str:
        return self._str

    def __add__(self, other: Any) -> "JP":
        res = super().__add__(JP(other))
        assert res != NotImplemented
        return JP(res)

    def __radd__(self, other: Any) -> "JP":
        return JP(other).__add__(self)

    def __getitem__(self, index) -> "JP":
        res = super().__getitem__(index)
        assert res != NotImplemented
        if isinstance(index, slice):
            return JP(res)
        return res

    @cached_property
    def parent(self) -> "JP":
        if not len(self):
            raise JPError("No parent of root path")
        return self[:-1]

    @cached_property
    def bind_slots(self) -> tuple[int, ...]:
        return tuple(i for i, f in enumerate(self) if is_wildcard(f))

    @cached_property
    def is_concrete(self) -> bool:
        return not self.bind_slots

    def bind(self, indexes: Sequence[JPField | JPTuple]) -> "JP":
        slots = self.bind_slots
        if len(slots) < len(indexes):
            raise JPError(f"Too many indexes to bind to path {self}")
        parts = [(f,) for f in self]
        for slot, idx in zip(slots, indexes):
            parts[slot] = idx if isinstance(idx, type(self)) else (idx,)
        return JP(tuple(f for p in parts for f in p))


JPRoot = JP("$")

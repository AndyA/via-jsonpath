from dataclasses import dataclass, field
from functools import cached_property
from itertools import count
from typing import Any, Callable, Optional

from typing_extensions import Self

from .editor import Editor
from .jp import JP
from .jp_dict import JPDict
from .ref import Deleted, Ignored, peek

Path = JP | str
MapFunction = Callable[[Any], Any]


def cast_array(value: Any) -> list:
    return value if isinstance(value, list) else [value]


@dataclass(kw_only=True, frozen=True)
class ViaContext:
    path: JP
    data: Any
    up: Optional["ViaContext"] = None

    @cached_property
    def root(self) -> "ViaContext":
        if self.up:
            return self.up.root
        return self

    def get(self, path: Path) -> Any:
        path = JP(path)
        slot = self.data
        for idx in path:
            if slot == Deleted:
                break
            slot = peek((slot, idx))
        return slot


ViaFunction = Callable[[ViaContext], Any]
DstFunction = Callable[[ViaContext], Path]
DstPath = Path | DstFunction


def lit(value: Any) -> ViaFunction:
    """Literal value for via."""
    return lambda _: value


@dataclass(kw_only=True, frozen=True)
class Rule:
    src: Path | list[Path] = JP("$")
    dst: DstPath | list[DstPath] = None
    via: ViaFunction | list[ViaFunction] = field(default_factory=list)
    map: MapFunction | list[MapFunction] = field(default_factory=list)


@dataclass(kw_only=True, frozen=True)
class SrcRule:
    src: JP
    dsts: Optional[DstPath | list[DstPath]]
    vias: list[ViaFunction]
    maps: list[MapFunction]
    seq: int


@dataclass(kw_only=True, frozen=True)
class RuleSet:
    rules: list[Rule]

    def __add__(self, other: Any) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        return type(self)(*self.rules, *other.rules)

    def __repr__(self) -> str:
        rules = ", ".join(str(rule) for rule in self.rules)
        return f"{type(self).__name__}({rules})"

    @cached_property
    def searcher(self) -> JPDict[list[SrcRule]]:
        seq = count()
        searcher = JPDict[list[SrcRule]]()
        for rule in self.rules:
            for src in [JP(s) for s in cast_array(rule.src)]:
                dsts = (
                    None
                    if rule.dst is None
                    else [d if callable(d) else JP(d) for d in cast_array(rule.dst)]
                )

                searcher.setdefault(src, []).append(
                    SrcRule(
                        src=src,
                        dsts=dsts,
                        vias=cast_array(rule.via),
                        maps=cast_array(rule.map),
                        seq=next(seq),
                    )
                )

        return searcher.trie


SearchHits = list[tuple[SrcRule, JP, Any]]


class Via(RuleSet):
    def __init__(self, *rules: Rule):
        super().__init__(rules=rules)

    def _search(self, ctx: ViaContext) -> SearchHits:
        res = self.searcher.visit(ctx.data, path=JP("$"))
        return [
            (rule, path, data)
            for path, data, node in res
            for rule in node.data
            if data not in (Deleted, Ignored)
        ]

    def _build_editor(self, ctx: ViaContext, hits: SearchHits) -> None:
        editor = Editor()
        for rule, path, data in hits:
            next_ctx = ViaContext(path=path, data=data, up=ctx)

            for via in rule.vias:
                data = via(next_ctx) if callable(via) else via
                next_ctx = ViaContext(path=path, data=data, up=ctx)

            if rule.maps:
                for map in rule.maps:
                    data = map(data)
                next_ctx = ViaContext(path=path, data=data, up=ctx)

            if rule.dsts is None:
                editor.set(path, data)
                continue

            for dst in rule.dsts:
                if callable(dst):
                    dst = dst(next_ctx)
                editor.set(dst, data)

        return editor

    def __call__(self, ctx: ViaContext, out: Any = Deleted) -> Any:
        hits = self._search(ctx)
        hits.sort(key=lambda hit: hit[0].seq)
        return self._build_editor(ctx, hits).edit(out)

    def transform(self, data: Any, out: Any = Deleted) -> Any:
        return self(ViaContext(path=JP("$"), data=data), out)

    @classmethod
    def chain(cls, *vias: tuple[Self]) -> Self:
        return cls(Rule(via=list(vias)))

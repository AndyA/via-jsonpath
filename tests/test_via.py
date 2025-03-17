from copy import deepcopy
from dataclasses import dataclass
from functools import cached_property
from typing import Any

import pytest

from via_jsonpath.jp import JP
from via_jsonpath.ref import Deleted, caution
from via_jsonpath.via import Rule, Via, ViaContext


@dataclass(kw_only=True, frozen=True)
class ViaCase:
    via: Via
    obj: Any
    want: Any
    out: Any = Deleted

    @cached_property
    def obj_copy(self):
        return deepcopy(self.obj)

    @cached_property
    def out_copy(self):
        return deepcopy(self.out)

    def run_transform(self) -> Any:
        return self.via.transform(self.obj_copy, out=self.out_copy)

    def check(self):
        with caution():
            got = self.run_transform()
            print(f"want: {self.want}")
            print(f"got: {got}")
            assert got == self.want
            assert self.obj_copy == self.obj
            assert self.out_copy == self.out


class TestVia:
    def test_transform(self):
        obj1 = {
            "xx:id": 1234,
            "meta": {"xx:id": 1235, "tags": ["a", "b", "c"]},
            "sidecar": {
                "meta": {"xx:id": 1236, "tags": ["d", "e", "f"]},
            },
        }

        test_cases = [
            ViaCase(
                via=Via(),
                obj={"foo": 1},
                want=Deleted,
            ),
            ViaCase(
                via=Via(Rule(src="$.bar")),
                obj={"foo": 1},
                want=Deleted,
            ),
            ViaCase(
                via=Via(Rule(src="$.foo")),
                obj={"foo": 1},
                want={"foo": 1},
            ),
            ViaCase(
                via=Via(Rule()),
                obj={"foo": 1},
                want={"foo": 1},
            ),
            ViaCase(
                via=Via(Rule(src="$.foo", dst="$.bar")),
                obj={"foo": 1},
                want={"bar": 1},
            ),
            ViaCase(
                via=Via(Rule(src='$..["xx:id"]')),
                obj=obj1,
                want={
                    "meta": {"xx:id": 1235},
                    "sidecar": {"meta": {"xx:id": 1236}},
                    "xx:id": 1234,
                },
            ),
            ViaCase(
                via=Via(Rule(src='$..["xx:id"]', dst="$.ids[*]")),
                obj=obj1,
                want={"ids": [1234, 1235, 1236]},
            ),
            ViaCase(
                via=Via(
                    Rule(
                        src='$..["xx:id"]',
                        dst="$.ids[*]",
                        via=Via(
                            Rule(src="$", dst="$.id"),
                            Rule(src="$", map=str, dst="$.id_str"),
                            Rule(via=True, dst="$.checked"),
                        ),
                    )
                ),
                obj=obj1,
                want={
                    "ids": [
                        {"checked": True, "id": 1234, "id_str": "1234"},
                        {"checked": True, "id": 1235, "id_str": "1235"},
                        {"checked": True, "id": 1236, "id_str": "1236"},
                    ]
                },
            ),
            ViaCase(
                via=Via(
                    Rule(),
                    Rule(src='$..["xx:id"]', map=str),
                    Rule(src='$.meta["xx:id"]'),
                ),
                obj=obj1,
                want={
                    "xx:id": "1234",
                    "meta": {"xx:id": 1235, "tags": ["a", "b", "c"]},
                    "sidecar": {"meta": {"xx:id": "1236", "tags": ["d", "e", "f"]}},
                },
            ),
            ViaCase(
                via=Via(Rule(src="$..tags[*]", dst="$[*]")),
                obj=obj1,
                want=["a", "b", "c", "d", "e", "f"],
            ),
        ]

        for tc in test_cases:
            tc.check()

    def test_context(self):
        def root_pluck(path: str):
            path = JP(path)
            assert len(path.bind_slots) == 1

            def pluck(ctx: ViaContext) -> Any:
                return ctx.root.get(path.bind([ctx.data]))

            return pluck

        test_cases = [
            ViaCase(
                via=Via(
                    Rule(
                        src="$.authors[*]",
                        dst=["$.people[*].meta", "$.also[*]"],
                        via=Via(
                            Rule(
                                src="$.uid",
                                via=root_pluck("$.dictionary[*].name"),
                                dst="$.name",
                            ),
                            Rule(src="$.uid", dst="$.id"),
                        ),
                    )
                ),
                obj={
                    "dictionary": {
                        "andy": {"name": "Andrew"},
                        "smoo": {"name": "Samantha"},
                    },
                    "authors": [
                        {"uid": "andy"},
                        {"uid": "smoo"},
                        {"uid": "pizzo"},
                    ],
                },
                want={
                    "also": [
                        {"id": "andy", "name": "Andrew"},
                        {"id": "smoo", "name": "Samantha"},
                        {"id": "pizzo"},
                    ],
                    "people": [
                        {"meta": {"id": "andy", "name": "Andrew"}},
                        {"meta": {"id": "smoo", "name": "Samantha"}},
                        {"meta": {"id": "pizzo"}},
                    ],
                },
            ),
        ]

        for tc in test_cases:
            tc.check()

    def test_dst_func(self):
        def transpose(path: str):
            path = JP(path)
            assert len(path.bind_slots) == 2

            def dst_func(ctx: ViaContext) -> str:
                x = ctx.path[-2]
                y = ctx.path[-1]
                return path.bind([y, x])

            return dst_func

        obj1 = {
            "matrix": [
                ["a", "b", "c"],
                ["d", "e", "f"],
            ],
        }

        obj2 = {
            "matrix": [
                ["a"],
                ["b", "c"],
                ["d", "e", "f"],
            ],
        }

        test_cases = [
            ViaCase(
                via=Via(
                    Rule(
                        src="$.matrix[*][*]",
                        dst=transpose("$.transposed.y[*].x[*]"),
                    )
                ),
                obj=obj1,
                want={
                    "transposed": {
                        "y": [
                            {"x": ["a", "d"]},
                            {"x": ["b", "e"]},
                            {"x": ["c", "f"]},
                        ]
                    }
                },
            ),
            ViaCase(
                via=Via(
                    Rule(
                        src="$.matrix[*][*]",
                        dst=transpose("$.transposed[*][*]"),
                    )
                ),
                obj=obj2,
                want={
                    "transposed": [
                        ["a", "b", "d"],
                        [Deleted, "c", "e"],
                        [Deleted, Deleted, "f"],
                    ]
                },
            ),
        ]

        for tc in test_cases:
            tc.check()

    def test_chain(self):
        test_cases = [
            ViaCase(
                via=Via.chain(
                    Via(Rule(src='$..["xx:id"]', map=lambda x: x * 2)),
                    Via(Rule(src='$..["xx:id"]', dst="$.ids[*]")),
                    Via(Rule(src="$.ids[*]", map=str)),
                ),
                obj={"xx:id": 2468, "meta": {"xx:id": 2470}},
                want={"ids": ["4936", "4940"]},
            ),
        ]

        for tc in test_cases:
            tc.check()

    def test_add(self):
        via1 = Via(Rule(src="$.foo"))
        via2 = Via(Rule(src="$.bar"))

        ViaCase(
            via=via1 + via2, obj={"foo": 1, "bar": 2}, want={"foo": 1, "bar": 2}
        ).check()

        with pytest.raises(TypeError):
            via1 + 1

    def test_str(self):
        via = Via(Rule(src="$.foo"))
        via2 = eval(str(via))
        assert str(via) == "Via(Rule(src='$.foo', dst=None, via=[], map=[]))"

        ViaCase(via=via2, obj={"foo": 1, "bar": 2}, want={"foo": 1}).check()

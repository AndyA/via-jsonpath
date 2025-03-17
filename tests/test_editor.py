from copy import deepcopy
from dataclasses import dataclass
from functools import cached_property
from typing import Any

import pytest

from via_jsonpath.editor import Editor, IndexFountain
from via_jsonpath.jp import JP, JPError
from via_jsonpath.ref import Deleted, Ignored, caution


class TestIndexFountain:
    def test_allocate(self):
        fountain = IndexFountain()
        assert fountain.allocate(JP("$.foo")) == 0
        assert fountain.allocate(JP("$.foo")) == 1
        assert fountain.allocate(JP("$.bar")) == 0
        assert fountain.allocate(JP("$.foo.boz")) == 0
        assert fountain.allocate(JP("$.foo.boz")) == 1
        assert fountain.allocate(JP("$.bar")) == 1

        fountain.reset(JP("$.foo"))
        assert fountain.allocate(JP("$.foo")) == 0
        assert fountain.allocate(JP("$.foo.boz")) == 0

        fountain.reset(JP("$.boz"))  # NOP, no error


@dataclass(frozen=True, kw_only=True)
class EditorCase:
    edits: list[tuple[str, Any]]
    obj: Any
    want: Any

    @cached_property
    def obj_copy(self):
        return deepcopy(self.obj)

    def run_edit(self) -> Any:
        editor = Editor()
        for key, value in self.edits:
            editor.set(key, value)
        return editor.edit(self.obj_copy)

    def check(self):
        with caution():
            got = self.run_edit()
            print(f"want: {self.want}")
            print(f"got: {got}")
            assert got == self.want
            assert self.obj == self.obj_copy


class TestEditor:
    def test_edit(self):
        obj1 = {"foo": "hello", "tags": ["a"]}

        test_cases = [
            EditorCase(edits=[], obj=Deleted, want=Deleted),
            EditorCase(edits=[("$", [])], obj={}, want=[]),
            EditorCase(
                edits=[("$.foo.bar", True)],
                obj=Deleted,
                want={
                    "foo": {"bar": True},
                },
            ),
            EditorCase(
                edits=[("$.foo.bar", True), ("$.tags[1]", "z")],
                obj={"tags": ["a", "b", "c"]},
                want={"foo": {"bar": True}, "tags": ["a", "z", "c"]},
            ),
            EditorCase(
                edits=[("$.foo.bar[*]", 2), ("$.foo.bar[*]", 1)],
                obj={"tags": ["a", "b", "c"]},
                want={"tags": ["a", "b", "c"], "foo": {"bar": [2, 1]}},
            ),
            EditorCase(edits=[("$", []), ("$", {})], obj=Deleted, want={}),
            EditorCase(
                edits=[("$[0].extract", True)], obj=Deleted, want=[{"extract": True}]
            ),
            EditorCase(
                edits=[
                    ("$.extract", True),
                    ("$", {}),
                    ("$.foo.bar.baz[0]", True),
                ],
                obj=Deleted,
                want={"foo": {"bar": {"baz": [True]}}},
            ),
            EditorCase(
                edits=[
                    ("$.bar", obj1),
                    ("$.bar.baz", obj1),
                    ("$.tags[1]", "z"),
                ],
                obj=obj1,
                want={
                    "foo": "hello",
                    "tags": ["a", "z"],
                    "bar": {
                        "foo": "hello",
                        "tags": ["a"],
                        "baz": {"foo": "hello", "tags": ["a"]},
                    },
                },
            ),
        ]

        for tc in test_cases:
            tc.check()

    def test_subtle(self):
        test_cases = [
            EditorCase(
                edits=[
                    ("$.list[*]", 1),
                    ("$.list[*]", 2),
                    ("$.list[*]", 3),
                    ("$.list[1]", Ignored),
                    ("$.list[2]", 5),
                    ("$.list[3]", 6),
                ],
                obj=Deleted,
                want={"list": [1, 2, 5, 6]},
            ),
            EditorCase(
                edits=[
                    ("$.list[*]", 1),
                    ("$.list[1]", 4),
                    ("$.list[*]", 2),
                    ("$.list[3]", 6),
                    ("$.list[*]", 3),
                    ("$.list[2]", 5),
                ],
                obj=Deleted,
                want={"list": [1, 2, 5, 6]},
            ),
            EditorCase(
                edits=[
                    ("$.list[*]", 1),
                    ("$.list[1]", 4),
                    ("$.list[*]", 2),
                    ("$.list[2]", 5),
                    ("$.list[*]", 3),
                    ("$.list[3]", 6),
                ],
                obj=Deleted,
                want={"list": [1, 2, 3, 6]},
            ),
            EditorCase(
                edits=[
                    ("$.list[2].manual", "five"),
                    ("$.list[0].auto", "one"),
                    ("$.list[1].manual", "four"),
                    ("$.list[1].auto", "two"),
                    ("$.list[2].auto", "three"),
                    ("$.list[3].manual", "six"),
                ],
                obj=Deleted,
                want={
                    "list": [
                        {"auto": "one"},
                        {"auto": "two", "manual": "four"},
                        {"auto": "three", "manual": "five"},
                        {"manual": "six"},
                    ]
                },
            ),
            EditorCase(
                edits=[
                    ("$.list[2].manual", 5),
                    ("$.list[*].auto", 1),
                    ("$.list[1].manual", 4),
                    ("$.list[*].auto", 2),
                    ("$.list[*].auto", 3),
                    ("$.list[3].manual", 6),
                ],
                obj=Deleted,
                want={
                    "list": [
                        {"auto": 1},
                        {"auto": 2, "manual": 4},
                        {"auto": 3, "manual": 5},
                        {"manual": 6},
                    ]
                },
            ),
            EditorCase(
                edits=[
                    ("$.tags", []),
                    ("$.tags[*]", "one"),
                    ("$.foo.bar[*]", 1),
                    ("$.foo.bar[*]", 2),
                    ("$.foo.bar[*]", 3),
                    ("$.tags[*]", "two"),
                    ("$.foo.bar", []),
                    ("$.foo.bar[*]", 4),
                    ("$.foo.bar[*]", 5),
                    ("$.tags[*]", "three"),
                ],
                obj=Deleted,
                want={
                    "foo": {"bar": [4, 5]},
                    "tags": ["one", "two", "three"],
                },
            ),
        ]

        for tc in test_cases:
            tc.check()

    def test_negative(self):
        with pytest.raises(JPError, match=r"wildcard"):
            Editor().set("$.foo[*][*]", 2)

from dataclasses import dataclass
from typing import Any

from via_jsonpath import Trie


@dataclass(frozen=True, kw_only=True)
class VisitCase:
    paths: list[str]
    want: list
    obj: Any

    def run_visit(self) -> list:
        t = Trie()
        for path in self.paths:
            t.setdefault(path, []).append(path)
        return [
            (str(path), obj, node.data) for path, obj, node in t.trie.visit(self.obj)
        ]


class TestNodes:
    def test_visit(self):
        obj1 = {
            "foo": "hello",
            "tags": ["a", "b", "c"],
        }

        obj2 = {
            "xx:id": 1234,
            "meta": {"xx:id": 1235, "tags": ["a", "b", "c"]},
            "sidecar": {
                "meta": {"xx:id": 1236, "tags": ["d", "e", "f"]},
            },
        }

        obj3 = {
            "x": 1,
            "y": {"x": 2},
            "z": {"y": {"x": 3, "a": {"x": 4}}},
            "q": [{"x": 5}, {"x": 6}, {"y": {"x": 7}}],
        }

        test_cases = [
            VisitCase(paths=[], want=[], obj=obj1),
            VisitCase(paths=["$.foo.bar"], want=[], obj=obj1),
            VisitCase(
                paths=["$.foo"],
                want=[("$.foo", "hello", ["$.foo"])],
                obj=obj1,
            ),
            VisitCase(
                paths=["$.foo", "$.*"],
                want=[
                    ("$.foo", "hello", ["$.*"]),
                    ("$.tags", ["a", "b", "c"], ["$.*"]),
                    ("$.foo", "hello", ["$.foo"]),
                ],
                obj=obj1,
            ),
            VisitCase(
                paths=["$.*.*"],
                want=[
                    ("$.tags[0]", "a", ["$.*.*"]),
                    ("$.tags[1]", "b", ["$.*.*"]),
                    ("$.tags[2]", "c", ["$.*.*"]),
                ],
                obj=obj1,
            ),
            VisitCase(
                paths=["$[*][1]"],
                want=[("$.tags[1]", "b", ["$[*][1]"])],
                obj=obj1,
            ),
            VisitCase(
                paths=['$..["xx:id"]'],
                want=[
                    ('$["xx:id"]', 1234, ['$..["xx:id"]']),
                    ('$.meta["xx:id"]', 1235, ['$..["xx:id"]']),
                    ('$.sidecar.meta["xx:id"]', 1236, ['$..["xx:id"]']),
                ],
                obj=obj2,
            ),
            VisitCase(
                paths=["$..tags"],
                want=[
                    ("$.meta.tags", ["a", "b", "c"], ["$..tags"]),
                    ("$.sidecar.meta.tags", ["d", "e", "f"], ["$..tags"]),
                ],
                obj=obj2,
            ),
            VisitCase(
                paths=["$..tags[1]"],
                want=[
                    ("$.meta.tags[1]", "b", ["$..tags[1]"]),
                    ("$.sidecar.meta.tags[1]", "e", ["$..tags[1]"]),
                ],
                obj=obj2,
            ),
            VisitCase(
                paths=["$..x"],
                want=[
                    ("$.x", 1, ["$..x"]),
                    ("$.y.x", 2, ["$..x"]),
                    ("$.z.y.x", 3, ["$..x"]),
                    ("$.z.y.a.x", 4, ["$..x"]),
                    ("$.q[0].x", 5, ["$..x"]),
                    ("$.q[1].x", 6, ["$..x"]),
                    ("$.q[2].y.x", 7, ["$..x"]),
                ],
                obj=obj3,
            ),
            VisitCase(
                paths=["$..y..x"],
                want=[
                    ("$.y.x", 2, ["$..y..x"]),
                    ("$.z.y.x", 3, ["$..y..x"]),
                    ("$.z.y.a.x", 4, ["$..y..x"]),
                    ("$.q[2].y.x", 7, ["$..y..x"]),
                ],
                obj=obj3,
            ),
            VisitCase(
                paths=["$..y..x", "$..x"],
                want=[
                    ("$.x", 1, ["$..x"]),
                    ("$.y.x", 2, ["$..y..x"]),
                    ("$.y.x", 2, ["$..x"]),
                    ("$.z.y.x", 3, ["$..y..x"]),
                    ("$.z.y.a.x", 4, ["$..y..x"]),
                    ("$.z.y.x", 3, ["$..x"]),
                    ("$.z.y.a.x", 4, ["$..x"]),
                    ("$.q[0].x", 5, ["$..x"]),
                    ("$.q[1].x", 6, ["$..x"]),
                    ("$.q[2].y.x", 7, ["$..y..x"]),
                    ("$.q[2].y.x", 7, ["$..x"]),
                ],
                obj=obj3,
            ),
        ]

        for tc in test_cases:
            got = tc.run_visit()
            print(f"want: {tc.want}")
            print(f"got: {got}")
            assert got == tc.want
            assert got == tc.want

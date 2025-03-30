from dataclasses import dataclass
from typing import Any

from via_jsonpath import JP, scan


@dataclass(kw_only=True, frozen=True)
class ScanCase:
    obj: Any
    want: list[tuple[Any, JP]]
    inner: bool = False
    empty: bool = False

    def check(self):
        got = list(scan(self.obj, inner=self.inner, empty=self.empty))
        print(f"want: {self.want}")
        print(f"got: {got}")
        assert got == self.want


def test_scan():
    test_cases = [
        ScanCase(
            obj={"foo": 1},
            want=[(1, JP("$.foo"))],
        ),
        ScanCase(
            obj=[{"foo": 1}],
            want=[(1, JP("$[0].foo"))],
        ),
        ScanCase(
            obj=[{"foo": 1}, {"bar": 2}],
            want=[(1, JP("$[0].foo")), (2, JP("$[1].bar"))],
        ),
        ScanCase(
            obj=[{"foo": 1}, {"bar": 2}],
            inner=True,
            want=[
                ([{"foo": 1}, {"bar": 2}], ()),
                ({"foo": 1}, (0,)),
                (1, (0, "foo")),
                ({"bar": 2}, (1,)),
                (2, (1, "bar")),
            ],
        ),
        ScanCase(
            obj={"foo": []},
            empty=True,
            want=[
                ([], JP("$.foo")),
            ],
        ),
    ]
    for case in test_cases:
        case.check()

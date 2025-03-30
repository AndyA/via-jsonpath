#!/usr/bin/env -S uv run -q --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "via-jsonpath",
# ]
#
# [tool.uv.sources]
# via-jsonpath = { path = "../", editable = true }
# ///

import json
from dataclasses import dataclass
from functools import cached_property
from itertools import groupby
from typing import Iterable, Optional

from via_jsonpath import JP, Deleted, Editor


@dataclass(kw_only=True, frozen=True)
class Smat:
    f: str
    i: int
    p: str
    s: Optional[str] = None
    n: Optional[int | float] = None
    b: Optional[bool] = None
    o: Optional[str] = None

    @cached_property
    def key(self) -> tuple[str, int]:
        return self.f, self.i

    @cached_property
    def path(self) -> JP:
        return JP(self.p)

    @cached_property
    def value(self):
        if self.s is not None:
            return self.s
        if self.n is not None:
            return self.n
        if self.b is not None:
            return self.b
        if self.o is not None:
            return json.loads(self.o)
        raise ValueError("No value found")

    @classmethod
    def load(cls, path: str) -> Iterable["Smat"]:
        with open(path) as f:
            for ln in f:
                yield Smat(**json.loads(ln))


for key, smats in groupby(Smat.load("tmp/smat.json"), lambda x: x.key):
    print(f"# key: {key}")
    editor = Editor()
    for smat in smats:
        editor.set(smat.path, smat.value)
    obj = editor.edit(Deleted)
    print(json.dumps(obj, indent=2))

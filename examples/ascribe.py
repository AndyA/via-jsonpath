import json
from dataclasses import dataclass
from typing import Any

from via_jsonpath.jp import JP
from via_jsonpath.ref import Deleted, Ref, assign, container_type, peek


@dataclass(frozen=True, kw_only=True)
class Model:
    root: Ref = ({"$": Deleted}, "$")

    def set(self, path: JP, value: Any):
        path = JP(path)
        ref = self.root
        for part in path:
            next = peek(ref)
            if next == Deleted:
                next = container_type(part)()
                assign(ref, next)
            ref = (next, part)
        assign(ref, value)

    @property
    def data(self) -> Any:
        return peek(self.root)

    def edit(self, obj: Any = Deleted) -> Any:
        pass


m = Model()
m.set("$.foo", "hello")
m.set("$.bar[0].hello.world", [1, 2, 3])
m.set("$.bar", [])
print(json.dumps(m.data, indent=2))

from typing import Any, Iterable

from via_jsonpath.jp import JP, JPRoot


def is_in(obj: Any, key: Any) -> bool:
    if isinstance(obj, dict) and isinstance(key, str) and key in obj:
        return True

    if isinstance(obj, list) and isinstance(key, int) and 0 <= key < len(obj):
        return True

    return False


def kv_of(obj: Any) -> Iterable[tuple[Any, Any]]:
    if isinstance(obj, dict):
        return obj.items()

    if isinstance(obj, list):
        return enumerate(obj)

    return []


def scan(
    obj: Any,
    *,
    inner: bool = False,
    empty: bool = False,
    path: JP = JPRoot,
) -> Iterable[tuple[Any, JP]]:
    def scanner(obj, path):
        if isinstance(obj, (list, dict)):
            if inner or (empty and not obj):
                yield obj, path
            for idx, value in kv_of(obj):
                yield from scanner(value, path + (idx,))
        else:
            yield obj, path

    return scanner(obj, path)

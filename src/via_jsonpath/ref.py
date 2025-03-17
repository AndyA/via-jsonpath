from contextlib import contextmanager
from copy import copy
from typing import Any, Optional

from .jp import JPError
from .symbol import Symbol

Deleted = Symbol("Deleted")
Ignored = Symbol("Ignored")
Ref = tuple[dict, str] | tuple[list, int]


def _nop(obj: Any) -> Any:
    return obj


RESET = _nop, _nop, _nop, _nop


def _c_is_not_ours(obj: Any) -> Any:
    if id(obj) in _owned:
        raise JPError(f"Already owned object {obj} ({id(obj)})")
    return obj


def _c_is_ours(obj: Any) -> Any:
    if id(obj) not in _owned:
        raise JPError(f"Foreign object {obj} ({id(obj)})")
    return obj


def _c_claim(obj: Any) -> Any:
    _owned.add(id(obj))
    return obj


def _c_adopt(obj: Any) -> Any:
    return _c_claim(_c_is_not_ours(obj))


CAUTION = _c_adopt, _c_claim, _c_is_ours, _c_is_not_ours

_adopt, _claim, _is_ours, _is_not_ours = RESET
_owned: Optional[set] = None


@contextmanager
def caution():
    global _adopt, _claim, _is_ours, _is_not_ours, _owned
    # Already cautious?
    if _owned is not None:
        yield _owned
        return

    try:
        _adopt, _claim, _is_ours, _is_not_ours = CAUTION
        _owned = set()
        yield _owned
    finally:
        _adopt, _claim, _is_ours, _is_not_ours = RESET
        _owned = None


def adopt(obj: Any) -> Any:
    return _adopt(obj)


def claim(obj: Any) -> Any:
    return _claim(obj)


def is_ours(obj: Any) -> Any:
    return _is_ours(obj)


def is_not_ours(obj: Any) -> Any:
    return _is_not_ours(obj)


def is_dict_ref(ref: Ref) -> bool:
    return isinstance(ref[0], dict) and isinstance(ref[1], str)


def is_list_ref(ref: Ref) -> bool:
    return isinstance(ref[0], list) and isinstance(ref[1], int)


def peek(ref: Ref) -> Any:
    obj, key = ref
    if is_dict_ref(ref):
        return obj.get(key, Deleted)

    if is_list_ref(ref):
        return obj[key] if 0 <= key < len(obj) else Deleted

    raise JPError(f"Cannot get {key} from {type(obj).__name__}")


def trim_tail(ref: Ref) -> Ref:
    if is_list_ref(ref):
        obj = _is_ours(ref[0])
        while obj and obj[-1] == Deleted:
            obj.pop()


def poke(ref: Ref, value: Any) -> None:
    if value == Ignored:
        return

    obj, key = _is_ours(ref[0]), ref[1]

    if is_dict_ref(ref):
        if value == Deleted:
            obj.pop(key, None)
        else:
            obj[key] = value
    elif is_list_ref(ref):
        assert key >= 0
        if value == Deleted and key >= len(obj):
            return
        obj.extend([Deleted] * (key - len(obj) + 1))
        obj[key] = value
    else:
        raise JPError(f"Cannot set {key} in {type(obj).__name__}")


def copy_in(obj: Any) -> Any:
    return _adopt(copy(obj))


def ensure(ref: Ref, next_type: type) -> Ref:
    next_ref = peek(ref)

    if next_ref == Deleted:
        next_ref = _adopt(next_type())
    else:
        if not isinstance(next_ref, next_type):
            raise JPError(
                "Cannot vivify: type mismatch "
                f"{type(next_ref).__name__} != {next_type.__name__}"
            )
        next_ref = copy_in(next_ref)

    poke(ref, next_ref)

    return next_ref


def container_type(key: Any) -> type:
    return dict if isinstance(key, str) else list


def vivify(ref: Ref, key: Any) -> Ref:
    next_ref = ensure(ref, container_type(key))
    return (next_ref, key)

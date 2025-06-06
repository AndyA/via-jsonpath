from copy import copy
from typing import Any

from .arena import adopt, is_ours
from .jp import JPError
from .symbol import Symbol

Deleted = Symbol("Deleted")
Ignored = Symbol("Ignored")
Ref = tuple[dict[str, Any], str] | tuple[list[Any], int]


def is_dict_ref(ref: Ref) -> bool:
    return isinstance(ref[0], dict) and isinstance(ref[1], str)


def is_list_ref(ref: Ref) -> bool:
    return isinstance(ref[0], list) and isinstance(ref[1], int)


def peek(ref: Ref) -> Any:
    obj, key = ref
    if is_dict_ref(ref):
        assert isinstance(key, str)
        assert isinstance(obj, dict)
        return obj.get(key, Deleted)

    if is_list_ref(ref):
        assert isinstance(key, int)
        assert isinstance(obj, list)
        return obj[key] if 0 <= key < len(obj) else Deleted

    raise JPError(f"Cannot get {key} from {type(obj).__name__}")


def trim_tail(ref: Ref) -> None:
    if is_list_ref(ref):
        obj = is_ours(ref[0])
        while obj and obj[-1] == Deleted:
            obj.pop()


def assign(ref: Ref, value: Any) -> None:
    obj, key = ref
    if is_dict_ref(ref):
        assert isinstance(key, str)
        assert isinstance(obj, dict)
        if value == Deleted:
            obj.pop(key, None)
        else:
            obj[key] = value
    elif is_list_ref(ref):
        assert isinstance(key, int)
        assert isinstance(obj, list)
        assert key >= 0
        if value == Deleted and key >= len(obj):
            return
        obj.extend([Deleted] * (key - len(obj) + 1))
        obj[key] = value
    else:
        raise JPError(f"Cannot set {key} in {type(obj).__name__}")


def poke(ref: Ref, value: Any) -> None:
    if value != Ignored:
        is_ours(ref[0])
        assign(ref, value)


def copy_in(obj: Any) -> Any:
    return adopt(copy(obj))


def ensure(ref: Ref, next_type: type) -> dict[str, Any] | list[Any]:
    next_ref = peek(ref)

    if next_ref == Deleted:
        next_ref = adopt(next_type())
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


def vivify(ref: Ref, key: str | int) -> Ref:
    next_ref = ensure(ref, container_type(key))
    # Keep pylance happy
    if isinstance(next_ref, dict):
        assert isinstance(key, str)
        return (next_ref, key)
    else:
        assert isinstance(key, int)
        return (next_ref, key)

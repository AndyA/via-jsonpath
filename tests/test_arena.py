import pytest

from via_jsonpath import JPError
from via_jsonpath.arena import adopt, caution, claim, is_not_ours, is_ours
from via_jsonpath.ref import copy_in, peek, poke, vivify


def test_arena():
    with caution():
        yours = {"hello": "world"}
        ours = copy_in(yours)

        yours["hello"] = "goodbye"
        assert ours["hello"] == "world"

        assert is_ours(ours) is ours
        assert is_not_ours(yours) is yours

        with pytest.raises(JPError, match=r"Foreign object"):
            is_ours(yours)

        with pytest.raises(JPError, match=r"Already owned"):
            is_not_ours(ours)

        claim(yours)
        assert is_ours(yours) is yours

    with caution():
        obj = adopt({"foo": {"tag": "here"}})
        ref = (obj, "foo")
        with pytest.raises(JPError, match=r"Foreign object"):
            poke((peek(ref), "bar"), "hello")
        poke(vivify(ref, "bar"), "hello")

    # Check re-entrancy
    with caution() as o1:
        with caution() as o2:
            assert o1 is o2

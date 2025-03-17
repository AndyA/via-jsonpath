import pytest

from via_jsonpath import JPError
from via_jsonpath.ref import (
    Deleted,
    Ignored,
    adopt,
    caution,
    claim,
    copy_in,
    is_not_ours,
    is_ours,
    peek,
    poke,
    trim_tail,
    vivify,
)


def test_caution():
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


def test_peek():
    a_dict = {"hello": "world"}
    assert peek((a_dict, "hello")) == "world"
    assert peek((a_dict, "goodbye")) == Deleted
    with pytest.raises(JPError, match=r"Cannot get"):
        peek((a_dict, 3))

    a_list = [1, 2, 3]
    assert peek((a_list, 1)) == 2
    assert peek((a_list, 3)) == Deleted
    with pytest.raises(JPError, match=r"Cannot get"):
        peek((a_list, "hello"))


def test_poke():
    a_dict = {"hello": "world"}

    poke((a_dict, "hello"), Ignored)
    poke((a_dict, "foo"), Ignored)
    poke((a_dict, 3), Ignored)
    assert a_dict == {"hello": "world"}

    poke((a_dict, "hello"), "goodbye")
    assert a_dict == {"hello": "goodbye"}

    poke((a_dict, "goodbye"), "world")
    assert a_dict == {"hello": "goodbye", "goodbye": "world"}

    poke((a_dict, "goodbye"), Deleted)
    assert a_dict == {"hello": "goodbye"}

    a_list = [1, 2, 3]

    poke((a_list, 1), 4)
    assert a_list == [1, 4, 3]

    poke((a_list, 1), Deleted)
    assert a_list == [1, Deleted, 3]

    poke((a_list, 2), Deleted)
    trim_tail((a_list, 2))
    assert a_list == [1]

    poke((a_list, 2), "Hello")
    assert a_list == [1, Deleted, "Hello"]

    poke((a_list, 30), Deleted)
    assert a_list == [1, Deleted, "Hello"]

    with pytest.raises(JPError, match=r"Cannot set"):
        poke((a_list, "hello"), 1)


def test_vivify():
    a_dict = {"hello": "world", "tags": ["safe"]}
    assert vivify((a_dict, "goodbye"), "next") == ({}, "next")
    assert a_dict == {"hello": "world", "goodbye": {}, "tags": ["safe"]}

    with pytest.raises(JPError, match=r"Cannot vivify"):
        vivify((a_dict, "hello"), "next")

    assert vivify((a_dict, "meta"), 1) == ([], 1)
    assert a_dict == {
        "hello": "world",
        "goodbye": {},
        "meta": [],
        "tags": ["safe"],
    }

    assert vivify((a_dict, "tags"), 0) == (["safe"], 0)
    assert a_dict == {
        "hello": "world",
        "goodbye": {},
        "meta": [],
        "tags": ["safe"],
    }

    assert vivify((a_dict, "tags"), 0) == (["safe"], 0)
    assert a_dict == {
        "hello": "world",
        "goodbye": {},
        "meta": [],
        "tags": ["safe"],
    }

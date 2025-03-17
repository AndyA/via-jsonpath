from via_jsonpath.sugar import Symbol, cast_array, is_in, kv_of


def test_symbol():
    assert Symbol("foo") == Symbol("foo")
    assert Symbol("foo") != Symbol("bar")
    assert str(Symbol("foo")) == "foo"


def test_is_in():
    assert not is_in({}, "foo")
    assert is_in({"foo": "bar"}, "foo")
    assert not is_in({"foo": "bar"}, "bar")
    assert not is_in([], 0)
    assert is_in([1, 2, 3], 0)
    assert not is_in([1, 2, 3], 3)
    assert not is_in([1, 2, 3], 4)
    assert not is_in([1, 2, 3], -1)
    assert not is_in("hello", "h")


def test_kv_of():
    assert list(kv_of({})) == []
    assert list(kv_of({"foo": "bar"})) == [("foo", "bar")]
    assert list(kv_of([1, 2, 3])) == [(0, 1), (1, 2), (2, 3)]
    assert list(kv_of("hello")) == []


def test_cast_array():
    assert cast_array(1) == [1]
    assert cast_array([1]) == [1]
    assert cast_array([]) == []
    assert cast_array(None) == [None]
    assert cast_array("hello") == ["hello"]
    assert cast_array({"foo": "bar"}) == [{"foo": "bar"}]
    assert cast_array(Symbol("foo")) == [Symbol("foo")]

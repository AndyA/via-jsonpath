from via_jsonpath.symbol import Symbol


def test_symbol():
    assert Symbol("foo") == Symbol("foo")
    assert Symbol("foo") != Symbol("bar")
    assert str(Symbol("foo")) == "foo"

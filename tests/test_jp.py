from random import shuffle

import pytest

from via_jsonpath import JP, JPError, JPSearch, JPWild


class TestJP:
    def test_new(self):
        assert JP("$") == JP("$")
        assert JP("$.foo") == JP("$.foo")
        assert JP(JP("$.foo")) == JP("$.foo")
        jp = JP("$.foo.bar")
        assert JP(jp) is jp
        assert JP(("foo", "bar")) == JP("$.foo.bar")
        assert JP(("foo", "bar", JPWild)) == JP("$.foo.bar[*]")

    def test_parse(self):
        assert tuple(JP("$")) == ()
        assert tuple(JP("$.foo[3]")) == ("foo", 3)
        assert tuple(JP("$.foo[*]")) == ("foo", JPWild)
        assert tuple(JP("$.foo.*")) == ("foo", JPWild)
        assert tuple(JP("$..x")) == (JPSearch, "x")
        assert tuple(JP('$["\\n"]')) == ("\n",)

        with pytest.raises(JPError, match=r"Unexpected end"):
            JP("$.")
        with pytest.raises(JPError, match=r"Expected ]"):
            JP("$[3.")
        with pytest.raises(JPError, match=r"Expected index"):
            JP("$[a]")
        with pytest.raises(JPError, match=r"Unexpected \^"):
            JP("$.^")
        with pytest.raises(JPError, match=r"Unexpected \^"):
            JP("$^")

    def test_bind_slots(self):
        assert JP("$").bind_slots == ()
        assert JP("$[*][*]").bind_slots == (0, 1)
        assert JP("$.foo[*].bar[*]").bind_slots == (1, 3)

    def test_order(self):
        want = [
            JP("$[*]"),
            JP("$[0]"),
            JP("$[1]"),
            JP("$.foo"),
            JP("$.foo[3]"),
            JP("$.foo[19]"),
        ]
        shuffled = want.copy()
        shuffle(shuffled)
        got = sorted(shuffled)
        print(got)
        assert got == want

        with pytest.raises(TypeError):
            JP("$") < 3

    def test_str(self):
        assert str(JP("$")) == "$"
        assert str(JP("$.foo")) == "$.foo"
        assert str(JP("$.foo.bar")) == "$.foo.bar"
        assert str(JP("$.foo[3]")) == "$.foo[3]"
        assert str(JP("$.foo[*]")) == "$.foo[*]"
        assert str(JP("$..x")) == "$..x"
        assert str(JP('$["\\n"]')) == '$["\\n"]'
        assert str(JP('$.["foo"]')) == "$.foo"

    def test_add(self):
        assert JP("$") + "$.foo" == JP("$.foo")
        assert JP("$.foo") + (3,) == JP("$.foo[3]")
        assert JP("$.foo") + JP("$.bar") == JP("$.foo.bar")
        assert JP("$") + JP("$.foo") == JP("$.foo")
        assert JP("$.foo") + JP("$") == JP("$.foo")
        assert (5,) + JP("$.foo") + (3, "bar") == JP("$[5].foo[3].bar")
        assert "$.foo" + JP("$[*]") == JP("$.foo[*]")

        with pytest.raises(TypeError):
            JP("$") + 3

    def test_getitem(self):
        assert JP("$.foo")[0] == "foo"
        assert JP("$.foo[*]")[1] == JPWild
        assert JP("$.foo[*]")[:-1] == JP("$.foo")

    def test_parent(self):
        assert JP("$.foo").parent == JP("$")
        with pytest.raises(JPError, match=r"No parent"):
            JP("$").parent

    def test_is_concrete(self):
        assert JP("$").is_concrete
        assert not JP("$.foo[*]").is_concrete
        assert not JP("$..foo").is_concrete

    def test_bind(self):
        assert JP("$[*]").bind([1]) == JP("$[1]")
        assert JP("$.foo.[*]").bind([JP("$.bar.baz")]) == JP("$.foo.bar.baz")
        assert JP("$.foo.[*]").bind([JP("$.bar.baz[*]")]) == JP("$.foo.bar.baz[*]")
        with pytest.raises(JPError, match=r"Too many"):
            JP("$.foo[*].bar[*]").bind([1, 2, 3])

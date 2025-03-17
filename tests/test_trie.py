from via_jsonpath import JP, Node, Trie


class TestTrie:
    def test_simple(self):
        t = Trie()

        t["$.foo"] = 1
        t["$.bar"] = 2
        t[JP("$[0]")] = 3
        assert dict(t) == {JP("$.foo"): 1, JP("$.bar"): 2, JP("$[0]"): 3}

        del t[JP("$.foo")]
        assert dict(t) == {JP("$.bar"): 2, JP("$[0]"): 3}
        assert t["$.bar"] == 2
        assert JP("$.bar") in t

        t.setdefault("$.baz", ["safe"])
        assert dict(t) == {JP("$.bar"): 2, JP("$[0]"): 3, JP("$.baz"): ["safe"]}
        t.setdefault("$.baz", [])
        assert dict(t) == {JP("$.bar"): 2, JP("$[0]"): 3, JP("$.baz"): ["safe"]}

        t.clear()
        assert dict(t) == {}

    def test_trie(self):
        t = Trie()
        assert t.trie == Node(next={})
        assert t.trie is t.trie

        t["$.foo.bar"] = 1
        t["$.foo.baz"] = 2
        t["$.foo[0]"] = 3

        assert t.trie == Node(
            next={
                "foo": Node(
                    next={
                        "bar": Node(data=1, leaf=True),
                        "baz": Node(data=2, leaf=True),
                        0: Node(data=3, leaf=True),
                    }
                )
            }
        )
        assert t.trie is t.trie

        t.clear()
        assert t.trie == Node()

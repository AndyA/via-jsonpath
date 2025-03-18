from via_jsonpath import JP, JPDict, TrieNode


class TestJPDict:
    def test_simple(self):
        t = JPDict()

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
        t = JPDict()
        assert t.trie == TrieNode(next={})
        assert t.trie is t.trie

        t["$.foo.bar"] = 1
        t["$.foo.baz"] = 2
        t["$.foo[0]"] = 3

        assert t.trie == TrieNode(
            next={
                "foo": TrieNode(
                    next={
                        "bar": TrieNode(data=1, leaf=True),
                        "baz": TrieNode(data=2, leaf=True),
                        0: TrieNode(data=3, leaf=True),
                    }
                )
            }
        )
        assert t.trie is t.trie

        t.clear()
        assert t.trie == TrieNode()

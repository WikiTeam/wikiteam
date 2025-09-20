from wikiteam3.dumpgenerator.api.page_titles import read_until_end

def test_read_until_end():
    data = [
        "a",
        "b",
        "c",
        "d",
        "e",
    ]
    data_with_end = [i+"\n" for i in data]
    data_with_end.append("--END--")
    assert list(read_until_end(data_with_end)) == data
    assert list(read_until_end(data_with_end, start="c")) == ["c", "d", "e"]
    assert list(read_until_end(data_with_end, start="x")) == []
    assert list(read_until_end(data_with_end + ["--END--\n"])) == data + ["--END--"] # two end markers

    try:
        _ = list(read_until_end([])) == []
        assert False, "Should raise EOFError"
    except EOFError:
        pass
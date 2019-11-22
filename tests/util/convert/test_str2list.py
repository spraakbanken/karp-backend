from karp.util.convert import str2list


def test_empty_str():
    convert = str2list(",")
    result = convert("")
    assert len(result) == 1


def test_single_item():
    convert = str2list(",")
    result = convert("item")
    assert len(result) == 1


def test_3_items():
    convert = str2list(",")
    result = convert("item1,item2,item3")
    assert len(result) == 3
    assert result[0] == "item1"

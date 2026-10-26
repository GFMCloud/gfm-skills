from csvtidy import tidy


def test_trims_and_dedupes():
    rows = [[" a ", "b"], ["a", "b "], ["c", "d"]]
    assert list(tidy(rows)) == [("a", "b"), ("c", "d")]

from typing import Optional

from pytest import mark

from pkscrd.core.selection.service import hidden_partially


class Test_hidden_partially:

    _CASES = {
        "長さが異なる": ([0, 1, 2], [0, 1], False),
        "None ではない置換": ([0, 1, 2], [None, None, 3], False),
        "None からの置換": ([None, None, None], [0, None, None], False),
        "None 全置換": ([0, 1, 2], [None, None, None], True),
        "None 一部置換": ([0, 1, 2], [None, None, 2], True),
        "完全一致": ([0, 1, 2, 3], [0, 1, 2, 3], True),
        "空同士": ([], [], True),
    }

    @mark.parametrize(("ref", "tgt", "expected"), _CASES.values(), ids=_CASES.keys())
    def test(self, ref: list[Optional[int]], tgt: list[Optional[int]], expected: bool):
        assert hidden_partially(ref, tgt) == expected

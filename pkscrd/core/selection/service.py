from typing import Optional


def hidden_partially(ref: list[Optional[int]], tgt: list[Optional[int]]) -> bool:
    """`tgt` が `ref` を部分的に隠した結果かどうか判定する."""
    return len(ref) == len(tgt) and all(r == t or t is None for r, t in zip(ref, tgt))

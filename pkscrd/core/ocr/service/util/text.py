import re
from typing import Optional

from pkscrd.core.ocr.model import Fraction


def parse_fraction(text: str) -> Optional[Fraction]:
    """読み込んだ分数をパースする. 対応しないテキストのときは None を返す."""
    match = _FRACTION_PATTERN.match(text)
    if not match:
        return None
    return Fraction(int(match.group(1)), int(match.group(2)))


_FRACTION_PATTERN = re.compile(r"(\d+)/(\d+)")

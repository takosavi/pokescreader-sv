"""WinOCR に特有のテキスト処理."""

import functools
import itertools
import re
from typing import Iterable, Iterator

import unicodedata

from pkscrd.core.ocr.model import LogFormat
from .core import OcrResult, OcrWord


def normalize_fraction(text: str) -> str:
    """分数表現の読み間違いを補正し, パース可能な形式に変換する."""
    return (
        unicodedata.normalize("NFKC", text)
        .replace(" ", "")
        .replace("引", "5/")
        .replace("卩", "/1")
        .replace("ハ", "/1")
        .replace("八", "/1")
    )


def reorder_lines(
    result: OcrResult,
    fmt: LogFormat,
    *,
    padding: int = 50,
    sort_offset: int = -5,
) -> Iterator[Iterator[str]]:
    """複数行ログの読み込み結果において各文字の座標を確認し, 行と単語を並べ直す."""

    def line_index(word: OcrWord) -> int:
        line_bottom = word.bounding_rect.y + word.bounding_rect.height - padding
        if word.text == "ー":
            line_bottom += fmt.line_height * 0.3
        return int(line_bottom + sort_offset) // fmt.line_height

    def sort_key(word: OcrWord) -> tuple[int, float]:
        return line_index(word), word.bounding_rect.x

    groups = itertools.groupby(
        sorted(
            (word for line in result.lines or [] for word in line.words or []),
            key=sort_key,
        ),
        key=line_index,
    )
    return (reorder_words(words) for _, words in groups)


def reorder_words(words: Iterable[OcrWord]) -> Iterator[str]:
    """行に含まれる単語群から単語区切りを探し, 単語を再作成する."""

    iterator = iter(words)
    buffer = [next(iterator)]
    for word in iterator:
        last = buffer[-1]
        last_right = last.bounding_rect.x + last.bounding_rect.width
        if word.bounding_rect.x < last_right + 20:  # HACK ちゃんと測る
            buffer.append(word)
            continue

        yield "".join(w.text for w in buffer)
        buffer = [word]

    yield "".join(w.text for w in buffer)


def fix_general(text: str) -> str:
    """一般的な読み間違いを補正する."""
    return _apply_replacements(text, _GENERAL_REPLACEMENTS)


def fix_word(text: str) -> str:
    """ログに含まれる単語の読み間違いを補正する."""

    text = fix_general(unicodedata.normalize("NFKC", text).replace(" ", ""))

    # エクスクラメーションマークをスラッシュと間違える癖がある. スラッシュは出てこないので一律で置き換える.
    text = text.replace("/", "!")

    text = text.replace("上かった", "上がった")
    text = text.replace("下かった", "下がった")
    text = text.replace("遊ひます", "遊びます")
    text = fix_move_name(text)

    return _apply_regex_replacements(text, _WORD_REPLACEMENT_PATTERNS)


def fix_line(words: Iterable[str]) -> list[str]:
    """ログに含まれる行の読み間違いを補正する."""

    words = list(words)
    for patterns, replacement in _LINE_REPLACEMENT_PATTERNS:
        if len(words) == len(patterns) and all(
            pattern.match(word) for word, pattern in zip(words, patterns)
        ):
            return replacement
    if len(words) > 2 and words[-2].endswith("は") and words[-1] == "たあれた!":
        words[-1] = "たおれた!"
    return words


def fix_move_name(text: str) -> str:
    """技の名前に該当する個所のテキストを補正する."""
    return _apply_replacements(text, _MOVE_NAME_REPLACEMENTS)


_GENERAL_REPLACEMENTS = (
    ("-", "ー"),
    ("△", "ム"),
    ("ヰ", "キ"),
    ("ホケモンを", "ポケモンを"),
    ("ゖ", "け"),
)
_WORD_REPLACEMENT_PATTERNS = (
    (re.compile(r"シン[クグ]ル[ハバ八]トル"), "シングルバトル"),
    (re.compile(r"[タダ][フブ]ル[ハバ八]トル"), "ダブルバトル"),
    (re.compile(r"マルチ[ハバ八]トル"), "マルチバトル"),
    (re.compile(r"降参[かが]選[はば]れました"), "降参が選ばれました"),
)
_LINE_REPLACEMENT_PATTERNS = (
    (
        [re.compile(r"^効果は$"), re.compile("^[八ハ][ツッ]クンた!$")],
        ["効果は", "バツグンだ!"],
    ),
    (
        [re.compile(r"^降参[かが]$"), re.compile("^選[はば]れました$")],
        ["降参が", "選ばれました"],
    ),
)
_MOVE_NAME_REPLACEMENTS = (
    ("八一スト", "バースト"),
    ("八ースト", "バースト"),
)


def _apply_replacements(text: str, patterns: Iterable[tuple[str, str]]) -> str:
    return functools.reduce(_apply_replacement, patterns, text)


def _apply_replacement(text: str, pattern: tuple[str, str]) -> str:
    return text.replace(*pattern)


def _apply_regex_replacements(
    text: str,
    patterns: Iterable[tuple[re.Pattern, str]],
) -> str:
    return functools.reduce(_apply_regex_replacement, patterns, text)


def _apply_regex_replacement(text: str, pattern: tuple[re.Pattern, str]) -> str:
    return pattern[0].sub(pattern[1], text)

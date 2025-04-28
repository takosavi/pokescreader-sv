import tempfile
from typing import Iterator

from pytest import fixture


@fixture
def tempdir() -> Iterator[str]:
    with tempfile.TemporaryDirectory() as name:
        yield name

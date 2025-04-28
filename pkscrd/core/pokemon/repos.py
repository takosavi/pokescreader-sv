import csv
import gzip
import dataclasses
from importlib.resources import files
from typing import Iterator, Optional

from pkscrd.core.pokemon.model import Type


@dataclasses.dataclass(frozen=True)
class Pokemon:
    pokedex_number: int
    form_index: int
    name: str
    form_name: Optional[str]
    type1: Type
    type2: Optional[Type]


def load_pokemons() -> Iterator[Pokemon]:
    with (
        files("pkscrd.core.pokemon.resources")
        .joinpath("pokemons.tsv.gz")
        .open("rb") as file,
        gzip.open(file, "rt", encoding="utf-8") as f,
    ):
        reader = csv.reader(f, delimiter="\t")
        yield from (
            Pokemon(
                int(row[0]),
                int(row[1]),
                row[2],
                row[3] or None,
                Type(row[4]),
                Type(row[5]) if row[5] else None,
            )
            for row in reader
        )

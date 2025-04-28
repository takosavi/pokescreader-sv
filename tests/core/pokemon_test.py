from pytest import fixture, mark

from pkscrd.core.pokemon.model import Pokemon, PokemonId, Type
from pkscrd.core.pokemon.repos import load_pokemons
from pkscrd.core.pokemon.service import PokemonMapper


class TestPokemonMapper:

    @fixture
    def mapper(self) -> PokemonMapper:
        return PokemonMapper(load_pokemons())

    _CASES = {
        "ID直マッピング": (
            PokemonId(898, 2),
            Pokemon(PokemonId(898, 2), "黒バドレックス", [(Type.PSYCHIC, Type.GHOST)]),
        ),
        "アローラ": (
            PokemonId(37, 1),
            Pokemon(PokemonId(37, 1), "アローラロコン", [(Type.ICE,)]),
        ),
        "ガラル": (
            PokemonId(52, 2),
            Pokemon(PokemonId(52, 2), "ガラルニャース", [(Type.STEEL,)]),
        ),
        "ヒスイ": (
            PokemonId(58, 1),
            Pokemon(PokemonId(58, 1), "ヒスイガーディ", [(Type.FIRE, Type.ROCK)]),
        ),
        "パルデア": (
            PokemonId(128, 1),
            Pokemon(PokemonId(128, 1), "パルデアケンタロス", [(Type.FIGHTING,)]),
        ),
        "けしん": (
            PokemonId(641, 0),
            Pokemon(PokemonId(641, 0), "けしんトルネロス", [(Type.FLYING,)]),
        ),
        "れいじゅう": (
            PokemonId(641, 1),
            Pokemon(PokemonId(641, 1), "れいじゅうトルネロス", [(Type.FLYING,)]),
        ),
        "オス": (
            PokemonId(678, 0),
            Pokemon(PokemonId(678, 0), "ニャオニクスオス", [(Type.PSYCHIC,)]),
        ),
        "メス": (
            PokemonId(678, 1),
            Pokemon(PokemonId(678, 1), "ニャオニクスメス", [(Type.PSYCHIC,)]),
        ),
        "フォルムそのまま結合": (
            PokemonId(386, 0),
            Pokemon(PokemonId(386, 0), "デオキシスノーマルフォルム", [(Type.PSYCHIC,)]),
        ),
        "フォルム名採用: 〇〇のすがた": (
            PokemonId(479, 0),
            Pokemon(PokemonId(479, 0), "ロトム", [(Type.ELECTRIC, Type.GHOST)]),
        ),
        "フォルム名採用: それ以外": (
            PokemonId(479, 1),
            Pokemon(PokemonId(479, 1), "ヒートロトム", [(Type.ELECTRIC, Type.FIRE)]),
        ),
        "タイプ候補上書き": (
            PokemonId(892, 0),
            Pokemon(
                PokemonId(892, 0),
                "ウーラオス",
                [(Type.FIGHTING, Type.WATER), (Type.FIGHTING, Type.DARK)],
            ),
        ),
        "該当なし": (PokemonId(9999, 99), None),
    }

    @mark.parametrize(("id", "expected"), _CASES.values(), ids=_CASES.keys())
    def test_get(self, mapper: PokemonMapper, id: PokemonId, expected: Pokemon):
        assert mapper.get(id) == expected

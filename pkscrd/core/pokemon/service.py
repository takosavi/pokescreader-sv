from typing import Iterable, Optional

from .model import Pokemon, PokemonId, Type
from .repos import Pokemon as PokemonR


class PokemonMapper:
    """ID からポケモンにマッピングする. 選出画面向け."""

    def __init__(self, pokemons: Iterable[PokemonR]):
        converted = (
            Pokemon(
                id=PokemonId(p.pokedex_number, p.form_index),
                name=PokemonMapper._fix_name(p),
                typesets=PokemonMapper._fix_typesets(p),
            )
            for p in pokemons
        )
        self._mapping = {p.id: p for p in converted}

    def get(self, id: PokemonId) -> Optional[Pokemon]:
        return self._mapping.get(id)

    @staticmethod
    def _fix_name(pokemon: PokemonR) -> str:
        if mapped := PokemonMapper._NAME_MAPPING.get(
            (pokemon.pokedex_number, pokemon.form_index)
        ):
            return mapped

        if pokemon.form_name == "アローラのすがた":
            return f"アローラ{pokemon.name}"
        if pokemon.form_name == "ガラルのすがた":
            return f"ガラル{pokemon.name}"
        if pokemon.form_name == "ヒスイのすがた":
            return f"ヒスイ{pokemon.name}"
        if pokemon.form_name == "パルデアのすがた":
            return f"パルデア{pokemon.name}"
        if pokemon.form_name == "けしんフォルム":
            return f"けしん{pokemon.name}"
        if pokemon.form_name == "れいじゅうフォルム":
            return f"れいじゅう{pokemon.name}"
        if pokemon.form_name == "オスのすがた":
            return f"{pokemon.name}オス"
        if pokemon.form_name == "メスのすがた":
            return f"{pokemon.name}メス"

        # フォルム名をそのまま結合するポケモン
        if pokemon.pokedex_number in {
            386,  # デオキシス
            647,  # ケルディオ
            710,  # バケッチャ
            711,  # パンプジン
            741,  # オドリドリ
        }:  # デオキシス
            return f"{pokemon.name}{pokemon.form_name}"

        # フォルム名がそのまま名前になるポケモン
        if pokemon.pokedex_number in {
            479,  # ロトム
            646,  # キュレム
            720,  # フーパ
        }:
            assert pokemon.form_name
            if pokemon.form_name.endswith("のすがた"):
                return pokemon.form_name[:-4]
            return pokemon.form_name

        return pokemon.name

    @staticmethod
    def _fix_typesets(pokemon: PokemonR) -> list[tuple[Type] | tuple[Type, Type]]:
        return PokemonMapper._TYPE_MAPPING.get(
            (pokemon.pokedex_number, pokemon.form_index),
            [(pokemon.type1, pokemon.type2) if pokemon.type2 else (pokemon.type1,)],
        )

    # 元の DB では読み上げに適さない名称を置き換える.
    _NAME_MAPPING = {
        (128, 2): "パルデアケンタロスほのお",
        (128, 3): "パルデアケンタロスみず",
        (233, 0): "ポリゴンツー",
        (413, 0): "ミノマダムくさき",
        (413, 1): "ミノマダムすなち",
        (413, 2): "ミノマダムゴミ",
        (483, 1): "オリジンディアルガ",
        (484, 1): "オリジンパルキア",
        (487, 0): "ギラティナアナザーフォルム",
        (487, 1): "ギラティナオリジンフォルム",
        (492, 0): "シェイミ",
        (492, 1): "シェイミスカイフォルム",
        (550, 0): "バスラオあかすじ",
        (550, 1): "バスラオあおすじ",
        (550, 2): "バスラオしろすじ",
        (555, 1): "ヒヒダルマダルマモード",
        (555, 3): "ガラルヒヒダルマダルマモード",
        # HACK メロエッタは所説
        (718, 0): "50パーセントジガルデ",
        (718, 1): "パーフェクトジガルデ",
        (718, 2): "10パーセントジガルデ",
        (745, 0): "ルガルガンまひる",
        (745, 1): "ルガルガンまよなか",
        (745, 2): "ルガルガンたそがれ",
        # HACK ヨワシは所説
        (800, 1): "日食ネクロズマ",
        (800, 2): "月食ネクロズマ",
        (898, 1): "白バドレックス",
        (898, 2): "黒バドレックス",
        (901, 1): "アカツキガチグマ",
        (931, 0): "イキリンコグリーン",
        (931, 1): "イキリンコブルー",
        (931, 2): "イキリンコイエロー",
        (931, 3): "イキリンコホワイト",
        (1017, 0): "くさオーガポン",
        (1017, 1): "みずオーガポン",
        (1017, 2): "ほのおオーガポン",
        (1017, 3): "いわオーガポン",
    }

    # 画像ではタイプが判断できないポケモンを置き換える
    _TYPE_MAPPING: dict[tuple[int, int], list[tuple[Type] | tuple[Type, Type]]] = {
        # ウーラオス
        (892, 0): [(Type.FIGHTING, Type.WATER), (Type.FIGHTING, Type.DARK)],
        (892, 1): [(Type.FIGHTING, Type.WATER), (Type.FIGHTING, Type.DARK)],
        # ザシアン
        (888, 0): [(Type.FAIRY, Type.STEEL), (Type.FAIRY,)],
        # ザマゼンタ
        (889, 0): [(Type.FIGHTING, Type.STEEL), (Type.FIGHTING,)],
    }

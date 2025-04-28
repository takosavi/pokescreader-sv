import collections
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Iterable, Iterator, NamedTuple, Optional

import numpy as np
from cv2.typing import MatLike

from pkscrd.core.terastal.model import TeraType


class TerastalOmenModel(NamedTuple):
    mask_inner: MatLike
    mask_outer: MatLike


def load_terastal_omen_model(path: Optional[str] = None) -> TerastalOmenModel:
    path_ = Path(path) if path else _get_resources() / "terastal-omen.npz"
    with path_.open("rb") as file:
        data = np.load(file)
        return TerastalOmenModel(**data)


def dump_terastal_omen_model(path: str, model: TerastalOmenModel) -> None:
    np.savez_compressed(
        path,
        mask_inner=model.mask_inner,
        mask_outer=model.mask_outer,
    )


def load_tera_type_models(
    path: Optional[str] = None,
) -> Iterator[tuple[TeraType, MatLike]]:
    path_ = Path(path) if path else _get_resources() / "tera-type.npz"
    with path_.open("rb") as file:
        data = np.load(file)
        for name in data.files:
            tera_type = TeraType(name.split("-")[0])
            yield tera_type, data[name]


def dump_tera_type_models(
    path: str,
    models: Iterable[tuple[TeraType, MatLike]],
) -> None:
    data: dict[str, MatLike] = {}
    counter: collections.Counter[TeraType] = collections.Counter()
    for tera_type, model in models:
        index = counter[tera_type]
        counter[tera_type] += 1
        data[f"{tera_type}-{index:08d}"] = model
    np.savez_compressed(path, **data)  # type: ignore


def _get_resources() -> Traversable:
    return files("pkscrd.core.terastal.resources")

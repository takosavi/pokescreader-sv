import os

import numpy as np

from pkscrd.core.terastal.model import TeraType
from pkscrd.core.terastal.repos import (
    TerastalOmenModel,
    load_terastal_omen_model,
    load_tera_type_models,
    dump_terastal_omen_model,
    dump_tera_type_models,
)


def test_保存したテラスタル前兆モデルを復元できる(tempdir: str):
    path = os.path.join(tempdir, "terastal-omen.npz")
    saved = TerastalOmenModel(
        mask_inner=np.zeros((1, 2), dtype=np.uint8),
        mask_outer=np.zeros((3, 4), dtype=np.uint8),
    )
    dump_terastal_omen_model(path, saved)

    loaded = load_terastal_omen_model(path)
    assert np.array_equal(saved.mask_inner, loaded.mask_inner)
    assert np.array_equal(saved.mask_outer, loaded.mask_outer)


def test_保存したテラスタイプモデルを復元できる(tempdir: str):
    path = os.path.join(tempdir, "terastal-omen.npz")
    saved = [
        (TeraType.FIRE, np.arange(0, 46080).reshape(180, 256)),
        (TeraType.FIRE, np.arange(1, 46081).reshape(180, 256)),
        (TeraType.WATER, np.arange(2, 46082).reshape(180, 256)),
    ]
    dump_tera_type_models(path, saved)

    loaded = list(load_tera_type_models(path))
    assert len(saved) == len(loaded)
    for s, l_ in zip(saved, loaded):
        assert s[0] is l_[0]
        assert np.array_equal(s[1], l_[1])

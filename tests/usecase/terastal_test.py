from pkscrd.core.notification.model import TeraTypeNotification
from pkscrd.core.terastal.model import (
    TeraType,
    TeraTypeDetectionSummary,
    TeraTypeDetection,
)
from pkscrd.usecase.terastal import notify_tera_type


def test_notify_tera_type():
    assert notify_tera_type(
        TeraTypeDetectionSummary(
            primary=TeraTypeDetection(type=TeraType.STELLA, color_score=1.0),
            possible=[
                TeraTypeDetection(type=TeraType.NORMAL, color_score=0.1),
                TeraTypeDetection(type=TeraType.FIRE, color_score=0.1),
                TeraTypeDetection(type=TeraType.WATER, color_score=0.1),
                TeraTypeDetection(type=TeraType.ELECTRIC, color_score=0.1),
                TeraTypeDetection(type=TeraType.GRASS, color_score=0.1),
                TeraTypeDetection(type=TeraType.ICE, color_score=0.1),
                TeraTypeDetection(type=TeraType.FIGHTING, color_score=0.1),
                TeraTypeDetection(type=TeraType.POISON, color_score=0.1),
                TeraTypeDetection(type=TeraType.GROUND, color_score=0.1),
                TeraTypeDetection(type=TeraType.FLYING, color_score=0.1),
                TeraTypeDetection(type=TeraType.PSYCHIC, color_score=0.1),
                TeraTypeDetection(type=TeraType.BUG, color_score=0.1),
                TeraTypeDetection(type=TeraType.ROCK, color_score=0.1),
                TeraTypeDetection(type=TeraType.GHOST, color_score=0.1),
                TeraTypeDetection(type=TeraType.DRAGON, color_score=0.1),
                TeraTypeDetection(type=TeraType.DARK, color_score=0.1),
                TeraTypeDetection(type=TeraType.STEEL, color_score=0.1),
                TeraTypeDetection(type=TeraType.FAIRY, color_score=0.1),
                TeraTypeDetection(type=TeraType.STELLA, color_score=0.1),
            ],
        )
    ) == TeraTypeNotification(
        primary=TeraType.STELLA,
        possible=[
            TeraType.NORMAL,
            TeraType.FIRE,
            TeraType.WATER,
            TeraType.ELECTRIC,
            TeraType.GRASS,
            TeraType.ICE,
            TeraType.FIGHTING,
            TeraType.POISON,
            TeraType.GROUND,
            TeraType.FLYING,
            TeraType.PSYCHIC,
            TeraType.BUG,
            TeraType.ROCK,
            TeraType.GHOST,
            TeraType.DRAGON,
            TeraType.DARK,
            TeraType.STEEL,
            TeraType.FAIRY,
            TeraType.STELLA,
        ],
    )

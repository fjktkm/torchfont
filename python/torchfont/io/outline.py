"""Shared constants for glyph outline command encoding."""

TYPE_TO_IDX: dict[str, int] = {
    "pad": 0,
    "moveTo": 1,
    "lineTo": 2,
    "curveTo": 3,
    "closePath": 4,
    "eos": 5,
}

TYPE_DIM: int = len(TYPE_TO_IDX)
COORD_DIM: int = 6

__all__ = ["COORD_DIM", "TYPE_DIM", "TYPE_TO_IDX"]

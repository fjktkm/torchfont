"""Shared constants for glyph command encoding."""

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
CMD_DIM: int = TYPE_DIM + COORD_DIM

__all__ = ["CMD_DIM", "COORD_DIM", "TYPE_DIM", "TYPE_TO_IDX"]

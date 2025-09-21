import torch
from fontTools.pens.basePen import BasePen
from fontTools.ttLib.ttGlyphSet import _TTGlyphSet
from torch import Tensor

TYPE_TO_IDX: dict[str, int] = {
    "pad": 0,
    "moveTo": 1,
    "lineTo": 2,
    "curveTo": 3,
    "closePath": 4,
    "eos": 5,
}
ZERO: tuple[float, float] = (0, 0)
TYPE_DIM: int = len(TYPE_TO_IDX)
COORD_DIM: int = 6
CMD_DIM: int = TYPE_DIM + COORD_DIM


class TensorPen(BasePen):
    def __init__(
        self,
        glyph_set: _TTGlyphSet,
    ) -> None:
        super().__init__(glyph_set)
        self.types: list[int] = []
        self.coords: list[tuple[float, float, float, float, float, float]] = []

    def _moveTo(self, pt: tuple[float, float]) -> None:  # noqa: N802
        self.types.append(TYPE_TO_IDX["moveTo"])
        self.coords.append((*ZERO, *ZERO, *pt))

    def _lineTo(self, pt: tuple[float, float]) -> None:  # noqa: N802
        self.types.append(TYPE_TO_IDX["lineTo"])
        self.coords.append((*ZERO, *ZERO, *pt))

    def _curveToOne(  # noqa: N802
        self,
        pt1: tuple[float, float],
        pt2: tuple[float, float],
        pt3: tuple[float, float],
    ) -> None:
        self.types.append(TYPE_TO_IDX["curveTo"])
        self.coords.append((*pt1, *pt2, *pt3))

    def _closePath(self) -> None:  # noqa: N802
        self.types.append(TYPE_TO_IDX["closePath"])
        self.coords.append((*ZERO, *ZERO, *ZERO))

    def get_tensor(self) -> tuple[Tensor, Tensor]:
        types_list = [*self.types, TYPE_TO_IDX["eos"]]
        coords_list = [*self.coords, (*ZERO, *ZERO, *ZERO)]

        n = len(types_list)
        types = torch.as_tensor(types_list, dtype=torch.long)
        coords = torch.as_tensor(coords_list, dtype=torch.float32).view(n, COORD_DIM)

        return types, coords

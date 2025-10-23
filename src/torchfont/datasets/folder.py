from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from functools import cache, partial
from pathlib import Path
from typing import SupportsIndex

import numpy as np
from fontTools.ttLib import TTFont
from torch import Tensor
from torch.utils.data import Dataset
from tqdm.auto import tqdm

from torchfont.io.pens import TensorPen


def _load_meta(
    file: str,
    cps_filter: Sequence[SupportsIndex] | None,
) -> tuple[bool, SupportsIndex, np.ndarray]:
    with TTFont(file) as font:
        if "fvar" in font:
            insts = font["fvar"].instances
            is_var, n_inst = (True, len(insts)) if insts else (False, 1)
        else:
            is_var, n_inst = False, 1

        cmap = font.getBestCmap()
        cps = np.fromiter(cmap.keys(), dtype=np.uint32)

        if cps_filter is not None:
            cps = np.intersect1d(cps, np.asarray(cps_filter), assume_unique=False)

    return is_var, n_inst, cps


@cache
def load_font(file: str) -> TTFont:
    return TTFont(file)


def default_loader(
    file: str,
    instance_index: SupportsIndex | None,
    codepoint: SupportsIndex,
) -> tuple[Tensor, Tensor]:
    font = load_font(file)

    if instance_index is not None:
        inst = font["fvar"].instances[instance_index]
        glyph_set = font.getGlyphSet(location=inst.coordinates)
    else:
        glyph_set = font.getGlyphSet()

    cmap = font.getBestCmap()
    name = cmap[codepoint]
    glyph = glyph_set[name]
    pen = TensorPen(glyph_set)
    glyph.draw(pen)
    types, coords = pen.get_tensor()

    upem = font["head"].unitsPerEm
    coords.mul_(1.0 / float(upem))

    return types, coords


class FontFolder(Dataset[object]):
    def __init__(
        self,
        root: Path | str,
        *,
        codepoint_filter: Sequence[SupportsIndex] | None = None,
        loader: Callable[
            [str, SupportsIndex | None, SupportsIndex],
            object,
        ] = default_loader,
        transform: Callable[[object], object] | None = None,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.files = sorted(str(fp) for fp in self.root.rglob("*.[oOtT][tT][fF]"))
        self.loader = loader
        self.transform = transform

        meta_loader = partial(_load_meta, cps_filter=codepoint_filter)
        with ProcessPoolExecutor() as ex:
            metadata = list(
                tqdm(
                    ex.map(meta_loader, self.files),
                    total=len(self.files),
                    desc="Loading fonts",
                ),
            )

        is_var = [is_var for is_var, _, _ in metadata]
        n_inst = [n_inst for _, n_inst, _ in metadata]
        cps = [cps for _, _, cps in metadata]

        self._is_var = np.array(is_var, dtype=bool)
        self._n_inst = np.array(n_inst, dtype=np.uint16)
        n_cp = np.array([cps.size for cps in cps])

        n_sample = n_cp * self._n_inst

        self._sample_offsets = np.r_[0, np.cumsum(n_sample, dtype=np.int64)]
        self._cp_offsets = np.r_[0, np.cumsum(n_cp, dtype=np.int64)]
        self._inst_offsets = np.r_[0, np.cumsum(self._n_inst, dtype=np.int64)]

        self._flat_cps = np.concatenate(cps) if cps else np.array([], dtype=np.uint32)
        unique_cps = np.unique(self._flat_cps)
        self._content_map = {cp: i for i, cp in enumerate(unique_cps)}

        self.num_content_classes = len(self._content_map)
        self.num_style_classes = int(self._inst_offsets[-1])

    def __len__(self) -> int:
        return int(self._sample_offsets[-1])

    def __getitem__(self, idx: int) -> object:
        font_idx = np.searchsorted(self._sample_offsets, idx, side="right") - 1
        sample_idx = idx - self._sample_offsets[font_idx]

        n_cps = self._cp_offsets[font_idx + 1] - self._cp_offsets[font_idx]
        inst_idx, cp_idx = divmod(sample_idx, n_cps)
        cp = self._flat_cps[self._cp_offsets[font_idx] + cp_idx]

        style_idx = self._inst_offsets[font_idx] + inst_idx
        content_idx = self._content_map[cp]

        file = self.files[font_idx]
        inst_idx = inst_idx if self._is_var[font_idx] else None

        sample = self.loader(file, inst_idx, cp)
        if self.transform is not None:
            sample = self.transform(sample)

        target = (style_idx, content_idx)

        return sample, target

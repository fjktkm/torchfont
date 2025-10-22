from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from fontTools.ttLib import TTFont
from torch.utils.data import Dataset
from tqdm.auto import tqdm

if TYPE_CHECKING:
    from fontTools.ttLib.tables._f_v_a_r import NamedInstance


def _load_meta(
    path: Path | str,
    cps_filter: Sequence[int] | None,
) -> tuple[bool, int, np.ndarray]:
    path = Path(path).expanduser().resolve()

    with TTFont(path) as font:
        if "fvar" in font:
            insts: list[NamedInstance] = font["fvar"].instances
            is_var, n_inst = (True, len(insts)) if insts else (False, 1)
        else:
            is_var, n_inst = False, 1

        cmap: dict[int, str] = font.getBestCmap()
        cps = np.fromiter(cmap.keys(), dtype=np.uint32)

        if cps_filter is not None:
            cps = np.intersect1d(cps, np.asarray(cps_filter), assume_unique=False)

    return is_var, n_inst, cps


class FontFolder(Dataset[dict[str, object]]):
    def __init__(
        self,
        root: Path | str,
        *,
        codepoint_filter: Sequence[int] | None = None,
        transform: Callable[[dict[str, object]], dict[str, object]] | None = None,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.paths = sorted(str(fp) for fp in self.root.rglob("*.[oOtT][tT][fF]"))
        self.transform = transform

        loader = partial(_load_meta, cps_filter=codepoint_filter)
        with ProcessPoolExecutor() as ex:
            metadata = list(
                tqdm(
                    ex.map(loader, self.paths),
                    total=len(self.paths),
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

    def __getitem__(self, idx: int) -> dict[str, object]:
        font_idx = np.searchsorted(self._sample_offsets, idx, side="right") - 1
        sample_idx = idx - self._sample_offsets[font_idx]

        n_cps = self._cp_offsets[font_idx + 1] - self._cp_offsets[font_idx]
        inst_idx, cp_idx = divmod(sample_idx, n_cps)
        cp = self._flat_cps[self._cp_offsets[font_idx] + cp_idx]

        style_idx = self._inst_offsets[font_idx] + inst_idx
        content_idx = self._content_map[cp]

        sample: dict[str, object] = {
            "path": self.paths[int(font_idx)],
            "is_variable": bool(self._is_var[font_idx]),
            "instance_index": int(inst_idx),
            "codepoint": int(cp),
            "style_label": int(style_idx),
            "content_label": int(content_idx),
        }

        return self.transform(sample) if self.transform else sample

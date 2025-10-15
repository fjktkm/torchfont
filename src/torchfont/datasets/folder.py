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

_KEEP_TABLES = {"cmap", "maxp", "fvar"}


def _load_meta(
    path: Path | str,
    cps_filter: Sequence[int] | None,
) -> tuple[bool, int, np.ndarray]:
    path = Path(path).expanduser().resolve()

    with TTFont(path) as font:
        for tag in list(font.keys()):
            if tag not in _KEEP_TABLES:
                del font[tag]

        if "fvar" in font:
            insts: list[NamedInstance] = font["fvar"].instances
            is_var, n_inst = (True, len(insts)) if insts else (False, 1)
        else:
            is_var, n_inst = False, 1

        cmap: dict[int, str] = font.getBestCmap()
        cps = np.fromiter(cmap.keys(), dtype=np.uint32)

        if cps_filter:
            cps = np.intersect1d(
                cps,
                np.asarray(cps_filter, dtype=np.uint32),
                assume_unique=False,
            )

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
        self.paths = sorted(fp for fp in self.root.rglob("*.[oOtT][tT][fF]"))
        self.transform = transform

        loader = partial(_load_meta, cps_filter=codepoint_filter)
        with ProcessPoolExecutor() as ex:
            results = list(
                tqdm(
                    ex.map(loader, self.paths),
                    total=len(self.paths),
                    desc="Loading fonts",
                ),
            )

        is_var, n_inst, cps_list = zip(*results, strict=True)
        self._is_var = np.asarray(is_var, dtype=bool)
        self._n_inst = np.asarray(n_inst, dtype=np.uint32)

        self._cps_counts = np.array([a.size for a in cps_list], dtype=np.uint32)
        self._cps_offsets = np.concatenate([[0], np.cumsum(self._cps_counts)])
        self._flat_cps = np.concatenate(cps_list)

        lens_per_font = self._n_inst * self._cps_counts
        self._sample_offsets = np.concatenate([[0], np.cumsum(lens_per_font)])
        self._inst_offsets = np.concatenate([[0], np.cumsum(self._n_inst)])

        self._unique_cps = np.unique(self._flat_cps)
        self.num_content_classes = len(self._unique_cps)
        self.num_style_classes = int(self._inst_offsets[-1])

    def __len__(self) -> int:
        return int(self._sample_offsets[-1])

    def __getitem__(self, idx: int) -> dict[str, object]:
        font_idx = int(np.searchsorted(self._sample_offsets, idx, side="right") - 1)
        local_idx = int(idx - self._sample_offsets[font_idx])

        n_cps = int(self._cps_counts[font_idx])
        inst_idx, cp_local_idx = divmod(local_idx, n_cps)

        cp_global_idx = int(self._cps_offsets[font_idx] + cp_local_idx)
        cp = int(self._flat_cps[cp_global_idx])

        style_idx = int(self._inst_offsets[font_idx] + inst_idx)
        content_idx = int(np.searchsorted(self._unique_cps, cp))

        sample: dict[str, object] = {
            "path": self.paths[font_idx],
            "is_variable": bool(self._is_var[font_idx]),
            "instance_index": inst_idx,
            "codepoint": cp,
            "style_label": style_idx,
            "content_label": content_idx,
        }

        return self.transform(sample) if self.transform else sample

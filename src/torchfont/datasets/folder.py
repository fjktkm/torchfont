"""Utilities for turning local font folders into indexed glyph datasets.

Notes:
    Fonts are cached by absolute path to minimize redundant disk access during
    dataset iteration, so edits on disk require an explicit cache clear.

Examples:
    Iterate glyph samples from a directory of fonts::

        from torchfont.datasets import FontFolder

        dataset = FontFolder(root="~/fonts")
        sample, target = dataset[0]

"""

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
    """Load metadata required to enumerate glyph samples from a font file.

    Args:
        file (str): Absolute path to the font file that will be inspected.
        cps_filter (Sequence[SupportsIndex] | None): Optional iterable of code
            points to retain. Only code points present in both this filter and
            the font's cmap survive.

    Returns:
        tuple[bool, SupportsIndex, np.ndarray]: Flag indicating whether the font
        exposes variable instances, the number of available instances (``1`` for
        static fonts), and the code points available after filtering.

    See Also:
        FontFolder: Consumes this metadata to construct dataset indices.

    """
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
    """Load a font file and cache the resulting ``TTFont`` instance.

    Args:
        file (str): Path to the font file to load.

    Returns:
        TTFont: Cached font instance for the supplied ``file``.

    Warnings:
        Editing a font file on disk is not reflected unless
        ``load_font.cache_clear()`` is invoked before the next access, because
        ``TTFont`` instances are memoized for performance.

    """
    return TTFont(file)


def default_loader(
    file: str,
    instance_index: SupportsIndex | None,
    codepoint: SupportsIndex,
) -> tuple[Tensor, Tensor]:
    """Convert a glyph outline to tensor representations.

    Args:
        file (str): Path to the font containing the glyph.
        instance_index (SupportsIndex | None): Optional index for the font
            variation instance. ``None`` selects the default font master.
        codepoint (SupportsIndex): Unicode code point mapped to the glyph to be
            converted.

    Returns:
        tuple[Tensor, Tensor]: First element contains pen instruction types and
        the second contains normalized outline coordinates in EM units.

    Examples:
        Create tensors for the lowercase letter ``a``::

            types, coords = default_loader("font.otf", None, ord("a"))

    """
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
    """Dataset that yields glyph samples from a directory of font files.

    The dataset flattens every available code point and variation instance into
    a single indexable sequence. Each item returns the loader output along with
    style and content targets.

    Attributes:
        files (list[str]): Sorted list of discovered font file paths.
        num_content_classes (int): Total number of unique Unicode code points.
        num_style_classes (int): Total number of variation instances across
            fonts.

    See Also:
        torchfont.datasets.repo.FontRepo: Extends the same indexing machinery
        with sparse Git checkout support.

    """

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
        """Initialize the dataset by scanning font files and indexing samples.

        Args:
            root (Path | str): Directory containing font files. Both OTF and TTF
                files are discovered recursively.
            codepoint_filter (Sequence[SupportsIndex] | None): Optional iterable
                of Unicode code points used to restrict the dataset content.
            loader (Callable[[str, SupportsIndex | None, SupportsIndex], object]):
                Callable that loads a glyph sample from a font file.
            transform (Callable[[object], object] | None): Optional
                transformation applied to each loader output before the item is
                returned.

        Examples:
            Restrict the dataset to uppercase ASCII glyphs::

                dataset = FontFolder(
                    root="~/fonts",
                    codepoint_filter=[ord(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
                )

        """
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
        """Return the total number of glyph samples discoverable in the dataset.

        Returns:
            int: Total number of glyph samples available in the dataset.

        """
        return int(self._sample_offsets[-1])

    def __getitem__(self, idx: int) -> tuple[object, tuple[int, int]]:
        """Load a glyph sample and its associated targets.

        Args:
            idx (int): Zero-based index locating a sample across all fonts, code
                points, and instances.

        Returns:
            tuple[object, tuple[int, int]]: ``(sample, target)`` pair where
            ``sample`` is produced by the configured loader and ``target`` is
            ``(style_idx, content_idx)``, describing the variation instance and
            Unicode code point class.

        Raises:
            IndexError: If ``idx`` falls outside the range ``[0, len(self))``.

        Examples:
            Retrieve the first glyph sample and its target pair::

                sample, target = dataset[0]

        """
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

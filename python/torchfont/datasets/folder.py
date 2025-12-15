"""Utilities for turning local font folders into indexed glyph datasets.

Notes:
    Glyph data is cached inside the native backend for the lifetime of each
    dataset instance. Recreate the dataset when editing font files on disk to
    ensure changes are observed.

Examples:
    Iterate glyph samples from a directory of fonts::

        from torchfont.datasets import FontFolder

        dataset = FontFolder(root="~/fonts")
        sample, target = dataset[0]

"""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import SupportsIndex

import torch
from torch.utils.data import Dataset

from torchfont import _torchfont
from torchfont.io.outline import COORD_DIM


class FontFolder(Dataset[object]):
    """Dataset that yields glyph samples from a directory of font files.

    The dataset flattens every available code point and variation instance into
    a single indexable sequence. Each item returns the loader output along with
    style and content targets.

    Attributes:
        num_content_classes (int): Total number of unique Unicode code points
            discoverable across the indexed fonts.
        num_style_classes (int): Total number of variation instances across the
            indexed fonts.

    See Also:
        torchfont.datasets.repo.FontRepo: Extends the same indexing machinery
        with Git synchronization for remote repositories.

    """

    def __init__(
        self,
        root: Path | str,
        *,
        codepoint_filter: Sequence[SupportsIndex] | None = None,
        patterns: Sequence[str] | None = None,
        transform: Callable[[object], object] | None = None,
    ) -> None:
        """Initialize the dataset by scanning font files and indexing samples.

        Args:
            root (Path | str): Directory containing font files. Both OTF and TTF
                files are discovered recursively.
            codepoint_filter (Sequence[SupportsIndex] | None): Optional iterable
                of Unicode code points used to restrict the dataset content.
            patterns (Sequence[str] | None): Optional gitignore-style patterns
                describing which font paths to include.
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
        self.root = Path(root)
        self.transform = transform
        self.patterns = (
            tuple(str(pattern) for pattern in patterns)
            if patterns is not None
            else None
        )
        self.codepoint_filter = (
            [int(cp) for cp in codepoint_filter]
            if codepoint_filter is not None
            else None
        )

        backend_patterns = list(self.patterns) if self.patterns is not None else None
        self._dataset = _torchfont.FontDataset(
            str(self.root),
            self.codepoint_filter,
            backend_patterns,
        )
        self.num_style_classes = int(self._dataset.style_class_count)
        self.num_content_classes = int(self._dataset.content_class_count)

    def __len__(self) -> int:
        """Return the total number of glyph samples discoverable in the dataset.

        Returns:
            int: Total number of glyph samples available in the dataset.

        """
        return int(self._dataset.sample_count)

    def __getitem__(self, idx: int) -> tuple[object, tuple[int, int]]:
        """Load a glyph sample and its associated targets.

        Args:
            idx (int): Zero-based index locating a sample across all fonts, code
                points, and instances.

        Returns:
            tuple[object, tuple[int, int]]: ``(sample, target)`` pair where
            ``sample`` is produced by the compiled backend and ``target`` is
            ``(style_idx, content_idx)``, describing the variation instance and
            Unicode code point class.

        Raises:
            IndexError: If ``idx`` falls outside the range ``[0, len(self))``.

        Examples:
            Retrieve the first glyph sample and its target pair::

                sample, target = dataset[0]

        """
        raw_types, raw_coords, style_idx, content_idx = self._dataset.item(int(idx))
        types = torch.as_tensor(raw_types, dtype=torch.long)
        coords = torch.as_tensor(raw_coords, dtype=torch.float32).view(-1, COORD_DIM)
        sample: object = (types, coords)

        if self.transform is not None:
            sample = self.transform(sample)

        target = (style_idx, content_idx)

        return sample, target

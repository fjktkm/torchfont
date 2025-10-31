"""Transform primitives for manipulating tensorized glyph sequences.

Examples:
    Compose a preprocessing pipeline for glyph tensors::

        from torchfont.transforms import Compose, LimitSequenceLength
        transform = Compose([LimitSequenceLength(256)])

Overview:
    The re-exported classes cover sequencing, truncation, and patch-based reshaping.

"""

from torchfont.transforms.transforms import (
    Compose,
    LimitSequenceLength,
    Patchify,
)

__all__ = [
    "Compose",
    "LimitSequenceLength",
    "Patchify",
]

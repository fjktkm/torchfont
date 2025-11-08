"""Transform primitives tailored to tensorized glyph sequences.

Notes:
    Each exported utility focuses on a single responsibility—sequencing,
    truncation, or patchification—so pipelines remain easy to audit and
    extend.

Examples:
    Compose a lightweight preprocessing pipeline::

        from torchfont.transforms import Compose, LimitSequenceLength

        transform = Compose([LimitSequenceLength(256)])

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

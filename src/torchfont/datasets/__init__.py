"""Dataset utilities for loading glyph samples from font files.

Examples:
    Build a dataset sourced from the Google Fonts index::

        from torchfont.datasets import GoogleFonts
        ds = GoogleFonts(root="data/google_fonts", ref="main", download=True)

"""

from torchfont.datasets.folder import FontFolder
from torchfont.datasets.google_fonts import GoogleFonts
from torchfont.datasets.repo import FontRepo

__all__ = [
    "FontFolder",
    "FontRepo",
    "GoogleFonts",
]

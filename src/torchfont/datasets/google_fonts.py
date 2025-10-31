"""Dataset utilities for working with the Google Fonts repository.

Examples:
    Assemble a dataset backed by the live Google Fonts index::

        ds = GoogleFonts(root="data/google_fonts", ref="main", download=True)

Resources:
    The repository layout and licensing details can be explored at
    https://github.com/google/fonts.

"""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import SupportsIndex

from torchfont.datasets.folder import default_loader
from torchfont.datasets.repo import FontRepo

REPO_URL = "https://github.com/google/fonts"
DEFAULT_PATTERNS = (
    "apache/*/*.ttf",
    "ofl/*/*.ttf",
    "ufl/*/*.ttf",
    "!ofl/adobeblank/AdobeBlank-Regular.ttf",
)


class GoogleFonts(FontRepo):
    """Dataset that materializes glyph samples from the Google Fonts project.

    See Also:
        FontRepo: Base class that implements sparse Git checkout handling.

    """

    def __init__(
        self,
        root: Path | str,
        ref: str,
        *,
        patterns: Sequence[str] | None = None,
        codepoint_filter: Sequence[int] | None = None,
        loader: Callable[
            [str, SupportsIndex | None, SupportsIndex],
            object,
        ] = default_loader,
        transform: Callable[[object], object] | None = None,
        download: bool = False,
    ) -> None:
        """Initialize a sparse clone of Google Fonts and index glyph samples.

        Args:
            root: Local directory that stores the sparse checkout of the Google
                Fonts repository.
            ref: Git reference (branch, tag, or commit) to fetch.
            patterns: Optional sparse-checkout patterns describing which files to
                materialize. Defaults to ``DEFAULT_PATTERNS`` if omitted. Refer to
                the Google Fonts contributor docs for directory structure details:
                <https://github.com/google/fonts/tree/main#readme>.
            codepoint_filter: Optional iterable of Unicode code points to include
                when indexing glyph samples.
            loader: Callable that loads glyph data for a font/code point pair.
            transform: Optional callable applied to each sample returned from the
                loader.
            download: Whether to perform the repository clone and sparse checkout
                when the directory is missing or empty.

        Examples:
            Reuse an existing checkout without hitting the network::

                ds = GoogleFonts(root="data/google_fonts", ref="main", download=False)

        """
        if patterns is None:
            patterns = DEFAULT_PATTERNS

        super().__init__(
            root=root,
            url=REPO_URL,
            ref=ref,
            patterns=patterns,
            codepoint_filter=codepoint_filter,
            loader=loader,
            transform=transform,
            download=download,
        )

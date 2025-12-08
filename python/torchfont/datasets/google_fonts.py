"""Dataset utilities tailored to the official Google Fonts repository.

References:
    Repository layout and licensing details are documented at
    https://github.com/google/fonts.

Examples:
    Assemble a dataset backed by the live Google Fonts index::

        ds = GoogleFonts(root="data/google_fonts", ref="main", download=True)

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
        torchfont.datasets.repo.FontRepo: Implements the sparse Git checkout
        handling shared with this dataset.

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
            root (Path | str): Local directory that stores the sparse checkout of
                the Google Fonts repository.
            ref (str): Git reference (branch, tag, or commit) to fetch.
            patterns (Sequence[str] | None): Optional sparse-checkout patterns
                describing which files to materialize. Defaults to
                ``DEFAULT_PATTERNS``. See the contributor guide at
                https://github.com/google/fonts/tree/main#readme for directory
                conventions.
            codepoint_filter (Sequence[int] | None): Optional iterable of Unicode
                code points to include when indexing glyph samples.
            loader (Callable[[str, SupportsIndex | None, SupportsIndex], object]):
                Callable that loads glyph data for a font/code point pair.
            transform (Callable[[object], object] | None): Optional callable
                applied to each sample returned from the loader.
            download (bool): Whether to perform the clone and sparse checkout
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

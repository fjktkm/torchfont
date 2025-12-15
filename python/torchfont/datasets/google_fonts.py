"""Dataset utilities tailored to the official Google Fonts repository.

References:
    Repository layout and licensing details are documented at
    https://github.com/google/fonts.

Examples:
    Assemble a dataset backed by the live Google Fonts index::

        ds = GoogleFonts(root="data/google/fonts", ref="main", download=True)

"""

from collections.abc import Callable, Sequence
from pathlib import Path

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
        torchfont.datasets.repo.FontRepo: Implements the Git synchronization
        and indexing logic shared with this dataset.

    """

    def __init__(
        self,
        root: Path | str,
        ref: str,
        *,
        patterns: Sequence[str] | None = None,
        codepoint_filter: Sequence[int] | None = None,
        transform: Callable[[object], object] | None = None,
        download: bool = False,
    ) -> None:
        """Initialize a shallow clone of Google Fonts and index glyph samples.

        Args:
            root (Path | str): Local directory that stores the shallow clone of
                the Google Fonts repository.
            ref (str): Git reference (branch, tag, or commit) to fetch.
            patterns (Sequence[str] | None): Optional path patterns applied when
                scanning the working tree for fonts. Defaults to ``DEFAULT_PATTERNS``.
                See the contributor guide at
                https://github.com/google/fonts/tree/main#readme for directory
                conventions.
            codepoint_filter (Sequence[int] | None): Optional iterable of Unicode
                code points to include when indexing glyph samples.
            transform (Callable[[object], object] | None): Optional callable
                applied to each sample returned from the backend.
            download (bool): Whether to perform the clone and checkout when the
                directory is missing or empty.

        Examples:
            Reuse an existing checkout without hitting the network::

                ds = GoogleFonts(root="data/google/fonts", ref="main", download=False)

        """
        if patterns is None:
            patterns = DEFAULT_PATTERNS

        super().__init__(
            root=root,
            url=REPO_URL,
            ref=ref,
            patterns=patterns,
            codepoint_filter=codepoint_filter,
            transform=transform,
            download=download,
        )

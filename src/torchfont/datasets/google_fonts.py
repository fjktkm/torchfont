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
    def __init__(
        self,
        root: Path | str,
        ref: str,
        *,
        patterns: Sequence[str] | None = None,
        codepoint_filter: Sequence[int] | None = None,
        transform: Callable | None = None,
        download: bool = False,
    ) -> None:
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

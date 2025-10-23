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

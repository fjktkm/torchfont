from collections.abc import Callable
from pathlib import Path

from torchfont.datasets.repo import FontRepo


class GoogleFonts(FontRepo):
    REPO_URL = "https://github.com/google/fonts.git"
    DEFAULT_PATTERNS = [
        "apache/*/*.ttf",
        "ofl/*/*.ttf",
        "ufl/*/*.ttf",
        "!ofl/adobeblank/AdobeBlank-Regular.ttf",
    ]

    def __init__(
        self,
        root: Path | str,
        ref: str,
        patterns: list[str] | None = None,
        codepoint_filter: list[int] | None = None,
        transform: Callable | None = None,
        download: bool = False,
    ) -> None:
        if patterns is None:
            patterns = self.DEFAULT_PATTERNS

        super().__init__(
            root=root,
            url=self.REPO_URL,
            ref=ref,
            patterns=patterns,
            codepoint_filter=codepoint_filter,
            transform=transform,
            download=download,
        )

from collections.abc import Sequence

class FontDataset:
    def __init__(
        self,
        root: str,
        codepoint_filter: Sequence[int] | None = ...,
        patterns: Sequence[str] | None = ...,
    ) -> None: ...

    sample_count: int

    style_class_count: int

    content_class_count: int

    def item(
        self,
        idx: int,
    ) -> tuple[list[int], list[float], int, int]: ...

from collections.abc import Iterable, Iterator, Sequence
from typing import Generic, TypeVar

_T = TypeVar("_T")

class CombinedLoader(Iterable[tuple[list[_T], int, int]], Generic[_T]):
    def __init__(
        self,
        iterables: Sequence[Iterable[_T]],
        mode: str = "min_size",
    ) -> None: ...
    def __iter__(self) -> Iterator[tuple[list[_T], int, int]]: ...

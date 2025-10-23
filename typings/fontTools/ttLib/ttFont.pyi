import logging
from collections.abc import Mapping
from os import PathLike
from types import TracebackType
from typing import IO, Literal, Self, overload

from fontTools.ttLib.tables._f_v_a_r import table__f_v_a_r
from fontTools.ttLib.tables._h_e_a_d import table__h_e_a_d
from fontTools.ttLib.ttGlyphSet import _TTGlyphSet

log: logging.Logger

class TTFont:
    def __init__(
        self,
        file: str | PathLike[str] | IO[bytes] | None = ...,
        *,
        recalcBBoxes: bool = ...,
        recalcTimestamp: bool = ...,
        ignoreDecompileErrors: bool = ...,
        lazy: bool | None = ...,
        fontNumber: int | None = ...,
    ) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    @overload
    def __getitem__(self, tag: Literal["fvar"]) -> table__f_v_a_r: ...
    @overload
    def __getitem__(self, tag: Literal["head"]) -> table__h_e_a_d: ...
    def __contains__(self, tag: str) -> bool: ...
    def getGlyphSet(
        self,
        *,
        location: Mapping[str, float] | None = ...,
        normalized: bool = ...,
    ) -> _TTGlyphSet: ...
    def getBestCmap(self) -> dict[int, str]: ...

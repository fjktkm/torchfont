from collections.abc import Mapping

class _TTGlyph:
    def draw(self, pen: object) -> None: ...

class _TTGlyphSet(Mapping[str, _TTGlyph]): ...

__all__ = ["_TTGlyph", "_TTGlyphSet"]

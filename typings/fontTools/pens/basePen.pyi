from collections.abc import Mapping

from fontTools.ttLib.ttGlyphSet import _TTGlyph, _TTGlyphSet

class BasePen:
    glyphSet: _TTGlyphSet | Mapping[str, _TTGlyph] | None

    def __init__(
        self,
        glyphSet: _TTGlyphSet | Mapping[str, _TTGlyph] | None = ...,
    ) -> None: ...

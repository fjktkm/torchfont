from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e
from fontTools.varLib.instancer import instantiateVariableFont
from pympler import asizeof

LICENSE_DIRS = ("apache", "ofl", "ufl")
FONT_ROOT = Path("./fonts")

font_paths = [fp for lic in LICENSE_DIRS for fp in (FONT_ROOT / lic).rglob("*.ttf")]

print(f"Found {len(font_paths)} .ttf files.\n")

total_size = 0
total_fonts = 0
total_glyphs = 0

for path in font_paths:
    try:
        font = TTFont(str(path))

        if "fvar" in font:
            try:
                for inst in font["fvar"].instances:
                    inst_font: TTFont = instantiateVariableFont(
                        font,
                        inst.coordinates,
                        inplace=False,
                        updateFontNames=True,
                    )

                    size = asizeof.asizeof(inst_font)
                    glyph_count = len(inst_font.getGlyphOrder())

                    total_size += size
                    total_fonts += 1
                    total_glyphs += glyph_count

                    name_table: table__n_a_m_e = inst_font["name"]
                    print(
                        f"{name_table.getBestFamilyName():<32}"
                        f"{name_table.getBestSubFamilyName():<32}"
                        f"{glyph_count:>5d}"
                        f"{' glyphs':<27}"
                        f"{size / 1024**2:>8.2f} MB"
                    )
            except Exception as _:
                size = asizeof.asizeof(font)
                glyph_count = len(font.getGlyphOrder())

                total_size += size
                total_fonts += 1
                total_glyphs += glyph_count

                name_table: table__n_a_m_e = font["name"]
                print(
                    f"{name_table.getBestFamilyName():<32}"
                    f"{name_table.getBestSubFamilyName():<32}"
                    f"{glyph_count:>5d}"
                    f"{' glyphs':<27}"
                    f"{size / 1024**2:>8.2f} MB"
                )

        else:
            size = asizeof.asizeof(font)
            glyph_count = len(font.getGlyphOrder())

            total_size += size
            total_fonts += 1
            total_glyphs += glyph_count

            name_table: table__n_a_m_e = font["name"]
            print(
                f"{name_table.getBestFamilyName():<32}"
                f"{name_table.getBestSubFamilyName():<32}"
                f"{glyph_count:>5d}"
                f"{' glyphs':<27}"
                f"{size / 1024**2:>8.2f} MB"
            )
    except Exception as e:
        print(f"Error processing {path.name}: {e}")

print("\n" + "-" * 50)
print(f"Total fonts (including variable instances): {total_fonts}")
print(f"Total glyphs: {total_glyphs}")
print(f"Total size: {total_size / 1024**2:.2f} MB")

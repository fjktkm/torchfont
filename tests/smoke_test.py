from torchfont.datasets import GoogleFonts

dataset = GoogleFonts(
    root="data/google_fonts",
    ref="main",
    patterns=("ufl/*/*.ttf",),
    codepoint_filter=range(0x80),
    download=True,
)
assert dataset is not None
assert len(dataset) > 0

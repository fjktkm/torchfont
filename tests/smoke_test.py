from torchfont.datasets import GoogleFonts

dataset = GoogleFonts(
    root="data/google_fonts",
    ref="main",
    patterns=["ufl/*/*.ttf"],
    codepoint_filter=list(range(0x00, 0x80)),
    download=True,
)
if dataset is not None and len(dataset) > 0:
    print("Smoke test succeeded")
else:
    raise RuntimeError("Smoke test failed")

from torchfont.datasets import GoogleFonts


def test_dataset_init() -> None:
    dataset = GoogleFonts(
        root="data/google_fonts",
        ref="main",
        patterns=["ufl/*/*.ttf"],
        codepoint_filter=list(range(0x00, 0x80)),
        download=True,
    )

    assert dataset.num_style_classes > 0
    assert dataset.num_content_classes > 0

    assert dataset.url == "https://github.com/google/fonts"
    assert dataset.ref == "main"
    assert dataset.commit_hash is not None
    assert dataset.patterns == ["ufl/*/*.ttf"]


def test_dataset_len() -> None:
    dataset = GoogleFonts(
        root="data/google_fonts",
        ref="main",
        patterns=["ufl/*/*.ttf"],
        codepoint_filter=list(range(0x00, 0x80)),
        download=True,
    )
    assert len(dataset) > 0


def test_dataset_getitem() -> None:
    dataset = GoogleFonts(
        root="data/google_fonts",
        ref="main",
        patterns=["ufl/*/*.ttf"],
        codepoint_filter=list(range(0x00, 0x80)),
        download=True,
    )
    sample = dataset[0]
    assert sample is not None


def test_dataset_iter() -> None:
    dataset = GoogleFonts(
        root="data/google_fonts",
        ref="main",
        patterns=["ufl/*/*.ttf"],
        codepoint_filter=list(range(0x00, 0x80)),
        download=True,
    )

    for sample in dataset:
        assert sample is not None

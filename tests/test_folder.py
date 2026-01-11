import torch
from torchfont.datasets import FontFolder


def test_font_folder_static_fonts() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=(
            "lato/Lato-Regular.ttf",
            "ubuntu/Ubuntu-Regular.ttf",
            "ptsans/PT_Sans-Web-Regular.ttf",
        ),
        codepoint_filter=range(0x80),
    )

    assert len(dataset.style_classes) > 0
    assert len(dataset.content_classes) > 0
    assert len(dataset) > 0


def test_font_folder_variable_fonts() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("roboto/Roboto*.ttf", "notosansjp/NotoSansJP*.ttf"),
        codepoint_filter=range(0x80),
    )

    assert len(dataset.style_classes) > 0
    assert len(dataset.content_classes) > 0
    assert len(dataset) > 0


def test_font_folder_all_fonts() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("*.ttf",),
        codepoint_filter=range(0x80),
    )

    assert len(dataset.style_classes) > 0
    assert len(dataset.content_classes) > 0
    assert len(dataset) > 0


def test_font_folder_getitem() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("lato/Lato-Regular.ttf",),
        codepoint_filter=range(0x41, 0x5B),
    )

    assert len(dataset) > 0

    types, coords, style_idx, content_idx = dataset[0]

    assert types.dtype == torch.long
    assert types.ndim == 1

    assert coords.dtype == torch.float32
    assert coords.ndim == 2
    assert coords.shape[1] == 6
    assert isinstance(style_idx, int)
    assert isinstance(content_idx, int)
    assert 0 <= style_idx < len(dataset.style_classes)
    assert 0 <= content_idx < len(dataset.content_classes)


def test_font_folder_cjk_support() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("notosansjp/NotoSansJP*.ttf",),
        codepoint_filter=[ord(c) for c in "あいうえお"],
    )

    assert len(dataset) > 0
    types, coords, style_idx, content_idx = dataset[0]
    assert types is not None
    assert coords is not None
    assert style_idx is not None
    assert content_idx is not None


def test_font_folder_codepoint_filter() -> None:
    dataset_upper = FontFolder(
        root="tests/fonts",
        patterns=("lato/Lato-Regular.ttf",),
        codepoint_filter=range(0x41, 0x5B),
    )

    dataset_lower = FontFolder(
        root="tests/fonts",
        patterns=("lato/Lato-Regular.ttf",),
        codepoint_filter=range(0x61, 0x7B),
    )

    assert len(dataset_upper) > 0
    assert len(dataset_lower) > 0

    assert len(dataset_upper.content_classes) <= 26
    assert len(dataset_lower.content_classes) <= 26


def test_font_folder_pattern_filter() -> None:
    dataset_all = FontFolder(
        root="tests/fonts",
        patterns=("*.ttf",),
        codepoint_filter=range(0x80),
    )

    dataset_roboto = FontFolder(
        root="tests/fonts",
        patterns=("roboto/Roboto*.ttf", "notosansjp/NotoSans*.ttf"),
        codepoint_filter=range(0x80),
    )

    dataset_lato = FontFolder(
        root="tests/fonts",
        patterns=("lato/Lato-Regular.ttf",),
        codepoint_filter=range(0x80),
    )

    assert len(dataset_all) > 0
    assert len(dataset_roboto) > 0
    assert len(dataset_lato) > 0
    assert len(dataset_all.style_classes) >= len(dataset_roboto.style_classes)
    assert len(dataset_all.style_classes) >= len(dataset_lato.style_classes)


def test_font_folder_empty_result() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("nonexistent*.ttf",),
        codepoint_filter=range(0x80),
    )
    assert len(dataset) == 0
    assert len(dataset.style_classes) == 0
    assert len(dataset.content_classes) == 0


def test_content_classes() -> None:
    """Test content_classes returns Unicode character strings"""
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("lato/Lato-Regular.ttf",),
        codepoint_filter=range(0x41, 0x44),  # A, B, C
    )

    assert len(dataset.content_classes) == 3
    assert dataset.content_classes == ["A", "B", "C"]
    assert all(isinstance(c, str) and len(c) == 1 for c in dataset.content_classes)


def test_content_class_to_idx() -> None:
    """Test content_class_to_idx maps characters to indices"""
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("lato/Lato-Regular.ttf",),
        codepoint_filter=range(0x41, 0x44),
    )

    assert dataset.content_class_to_idx["A"] == 0
    assert dataset.content_class_to_idx["B"] == 1
    assert dataset.content_class_to_idx["C"] == 2

    # Round-trip test
    for idx, char in enumerate(dataset.content_classes):
        assert dataset.content_class_to_idx[char] == idx


def test_style_classes() -> None:
    """Test style_classes returns descriptive names"""
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("lato/*.ttf",),
        codepoint_filter=range(0x41, 0x44),
    )

    assert len(dataset.style_classes) > 0
    assert all(isinstance(s, str) for s in dataset.style_classes)


def test_style_class_to_idx() -> None:
    """Test style_class_to_idx maps names to indices"""
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("lato/*.ttf",),
        codepoint_filter=range(0x41, 0x44),
    )

    # Round-trip test
    for idx, name in enumerate(dataset.style_classes):
        assert dataset.style_class_to_idx[name] == idx

from typing import cast

import pytest
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

    assert dataset.num_style_classes > 0
    assert dataset.num_content_classes > 0
    assert len(dataset) > 0


def test_font_folder_variable_fonts() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("roboto/Roboto*.ttf", "notosansjp/NotoSansJP*.ttf"),
        codepoint_filter=range(0x80),
    )

    assert dataset.num_style_classes > 0
    assert dataset.num_content_classes > 0
    assert len(dataset) > 0


def test_font_folder_all_fonts() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("*.ttf",),
        codepoint_filter=range(0x80),
    )

    assert dataset.num_style_classes > 0
    assert dataset.num_content_classes > 0
    assert len(dataset) > 0


def test_font_folder_getitem() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("lato/Lato-Regular.ttf",),
        codepoint_filter=range(0x41, 0x5B),
    )

    assert len(dataset) > 0

    sample, target = dataset[0]
    assert isinstance(sample, tuple)
    types, coords = cast("tuple[torch.Tensor, torch.Tensor]", sample)

    assert types.dtype == torch.long
    assert types.ndim == 1

    assert coords.dtype == torch.float32
    assert coords.ndim == 2
    assert coords.shape[1] == 6

    assert isinstance(target, tuple)
    assert len(target) == 2
    style_idx, content_idx = target
    assert isinstance(style_idx, int)
    assert isinstance(content_idx, int)
    assert 0 <= style_idx < dataset.num_style_classes
    assert 0 <= content_idx < dataset.num_content_classes


def test_font_folder_cjk_support() -> None:
    dataset = FontFolder(
        root="tests/fonts",
        patterns=("notosansjp/NotoSansJP*.ttf",),
        codepoint_filter=[ord(c) for c in "あいうえお"],
    )

    assert len(dataset) > 0
    sample, _target = dataset[0]
    assert sample is not None


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

    assert dataset_upper.num_content_classes <= 26
    assert dataset_lower.num_content_classes <= 26


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
    assert dataset_all.num_style_classes >= dataset_roboto.num_style_classes
    assert dataset_all.num_style_classes >= dataset_lato.num_style_classes


def test_font_folder_empty_result() -> None:
    with pytest.raises(ValueError, match="no font files found"):
        FontFolder(
            root="tests/fonts",
            patterns=("nonexistent*.ttf",),
            codepoint_filter=range(0x80),
        )

from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import TYPE_CHECKING, cast

import torch
from fontTools.ttLib import TTFont
from torch import Tensor

from torchfont.transforms.pens import TensorPen

if TYPE_CHECKING:
    from fontTools.ttLib.tables._f_v_a_r import NamedInstance


class Compose:
    def __init__(
        self,
        transforms: Sequence[Callable[[dict[str, object]], dict[str, object]]],
    ) -> None:
        self.transforms = transforms

    def __call__(self, sample: dict[str, object]) -> dict[str, object]:
        for t in self.transforms:
            sample = t(sample)
        return sample


class OpenFont:
    def __init__(
        self,
        *,
        enable_cache: bool = True,
        cache_maxsize: int | None = None,
    ) -> None:
        self._open = (
            lru_cache(maxsize=cache_maxsize)(TTFont) if enable_cache else TTFont
        )

    def __call__(self, sample: dict[str, object]) -> dict[str, object]:
        path = cast("str", sample["path"])

        font = self._open(path)

        sample["font"] = font

        return sample


class ToTensor:
    def __call__(self, sample: dict[str, object]) -> dict[str, object]:
        font = cast("TTFont", sample["font"])
        is_variable = cast("bool", sample["is_variable"])
        inst_idx = cast("int", sample["instance_index"])
        codepoint = cast("int", sample["codepoint"])

        if is_variable:
            inst: NamedInstance = font["fvar"].instances[inst_idx]
            glyph_set = font.getGlyphSet(location=inst.coordinates)
        else:
            glyph_set = font.getGlyphSet()

        cmap = font.getBestCmap()
        name = cmap[codepoint]
        glyph = glyph_set[name]
        pen = TensorPen(glyph_set)
        glyph.draw(pen)
        types, coords = pen.get_tensor()

        sample["command_types"] = types
        sample["command_coordinates"] = coords

        return sample


class LimitSequenceLength:
    def __init__(self, max_len: int = 512) -> None:
        self.max_len = max_len

    def __call__(self, sample: dict[str, object]) -> dict[str, object]:
        types = cast("Tensor", sample["command_types"])
        coords = cast("Tensor", sample["command_coordinates"])

        sample["command_types"] = types[: self.max_len]
        sample["command_coordinates"] = coords[: self.max_len]

        return sample


class Normalize:
    def __call__(self, sample: dict[str, object]) -> dict[str, object]:
        coords = cast("Tensor", sample["command_coordinates"])
        font = cast("TTFont", sample["font"])

        upem: int = font["head"].unitsPerEm
        coords.mul_(1.0 / float(upem))

        sample["coords"] = coords

        return sample


class Patchify:
    def __init__(self, patch_size: int = 8) -> None:
        self.patch_size = patch_size

    def __call__(self, sample: dict[str, object]) -> dict[str, object]:
        types = cast("Tensor", sample["command_types"])
        coords = cast("Tensor", sample["command_coordinates"])

        seq_len = types.size(0)
        pad = (-seq_len) % self.patch_size
        num_patches = (seq_len + pad) // self.patch_size

        pad_types = torch.cat([types, types.new_zeros(pad)], 0)
        pad_coords = torch.cat([coords, coords.new_zeros(pad, coords.size(1))], 0)

        patch_types = pad_types.view(num_patches, self.patch_size)
        patch_coords = pad_coords.view(num_patches, self.patch_size, coords.size(1))

        sample["command_types"] = patch_types
        sample["command_coordinates"] = patch_coords

        return sample


class CloseFont:
    def __call__(self, sample: dict[str, object]) -> dict[str, object]:
        del sample["font"]
        return sample

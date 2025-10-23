from collections.abc import Callable, Sequence

import torch
from torch import Tensor


class Compose:
    def __init__(self, transforms: Sequence[Callable[..., object]]) -> None:
        self.transforms = transforms

    def __call__(self, sample: object) -> object:
        for t in self.transforms:
            sample = t(sample)
        return sample


class LimitSequenceLength:
    def __init__(self, max_len: int) -> None:
        self.max_len = max_len

    def __call__(self, sample: tuple[Tensor, Tensor]) -> tuple[Tensor, Tensor]:
        types, coords = sample

        types = types[: self.max_len]
        coords = coords[: self.max_len]

        return types, coords


class Patchify:
    def __init__(self, patch_size: int) -> None:
        self.patch_size = patch_size

    def __call__(self, sample: tuple[Tensor, Tensor]) -> tuple[Tensor, Tensor]:
        types, coords = sample

        seq_len = types.size(0)
        pad = (-seq_len) % self.patch_size
        num_patches = (seq_len + pad) // self.patch_size

        pad_types = torch.cat([types, types.new_zeros(pad)], 0)
        pad_coords = torch.cat([coords, coords.new_zeros(pad, coords.size(1))], 0)

        patch_types = pad_types.view(num_patches, self.patch_size)
        patch_coords = pad_coords.view(num_patches, self.patch_size, coords.size(1))

        return patch_types, patch_coords

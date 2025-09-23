import logging
from typing import cast

import numpy as np
import torch
from lightning.pytorch.utilities.combined_loader import CombinedLoader
from torch import Tensor
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Subset
from tqdm import tqdm

from torchfont.datasets import GoogleFonts
from torchfont.transforms import (
    CloseFont,
    Compose,
    LimitSequenceLength,
    Normalize,
    OpenFont,
    Patchify,
    ToTensor,
)

logging.getLogger("fontTools").setLevel(logging.ERROR)

transforms = Compose(
    [
        OpenFont(),
        ToTensor(),
        LimitSequenceLength(),
        Normalize(),
        Patchify(patch_size=32),
        CloseFont(),
    ]
)

dataset = GoogleFonts(
    root="data/google_fonts",
    ref="main",
    download=True,
    transform=transforms,
)

num_splits = 8
n = len(dataset)
indices = torch.arange(n)
splits = torch.tensor_split(indices, num_splits)
subsets = [Subset(dataset, idxs.tolist()) for idxs in splits]


def collate_fn(
    batch: list[dict[str, object]],
) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    types_list = [cast(Tensor, item["command_types"]) for item in batch]
    coords_list = [cast(Tensor, item["command_coordinates"]) for item in batch]
    style_label_list = [cast(int, item["style_label"]) for item in batch]
    content_label_list = [cast(int, item["content_label"]) for item in batch]

    types_tensor = pad_sequence(types_list, batch_first=True, padding_value=0)
    coords_tensor = pad_sequence(coords_list, batch_first=True, padding_value=0.0)

    style_label_tensor = torch.as_tensor(style_label_list, dtype=torch.long)
    content_label_tensor = torch.as_tensor(content_label_list, dtype=torch.long)

    return types_tensor, coords_tensor, style_label_tensor, content_label_tensor


def combine_fn(
    batch: list[tuple[Tensor, Tensor, Tensor, Tensor]],
) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    types_list, coords_list, style_label_list, content_label_list = zip(
        *batch, strict=True
    )

    sizes = [t.size(0) for t in types_list]
    offsets = np.concatenate(([0], np.cumsum(sizes)))
    total_samples = int(offsets[-1])

    max_seq_len = max(x.size(1) for x in types_list)
    types_ref, coords_ref = types_list[0], coords_list[0]

    combined_types = types_ref.new_zeros(total_samples, max_seq_len, types_ref.size(2))
    combined_coords = coords_ref.new_zeros(
        total_samples, max_seq_len, coords_ref.size(2), coords_ref.size(3)
    )

    for i, (types, coords) in enumerate(zip(types_list, coords_list, strict=True)):
        start, end = offsets[i], offsets[i + 1]
        seq_len = types.size(1)
        combined_types[start:end, :seq_len] = types
        combined_coords[start:end, :seq_len] = coords

    combined_style_label = torch.cat(style_label_list, 0)
    combined_content_label = torch.cat(content_label_list, 0)

    return combined_types, combined_coords, combined_style_label, combined_content_label


loaders = [
    DataLoader(
        subset,
        batch_size=64,
        shuffle=True,
        num_workers=1,
        prefetch_factor=2,
        collate_fn=collate_fn,
    )
    for subset in subsets
]
dataloader = CombinedLoader(loaders)
_ = iter(dataloader)
total = len(dataloader)

for batch, _, _ in tqdm(dataloader, total=total, desc="Iterating over datasets"):
    types, coords, style_labels, content_labels = combine_fn(batch)

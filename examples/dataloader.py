import logging
from typing import cast

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

    types_batch = pad_sequence(types_list, batch_first=True, padding_value=0)
    coords_batch = pad_sequence(coords_list, batch_first=True, padding_value=0.0)

    style_label_tensor = torch.as_tensor(style_label_list, dtype=torch.long)
    content_label_tensor = torch.as_tensor(content_label_list, dtype=torch.long)

    return types_batch, coords_batch, style_label_tensor, content_label_tensor


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

it = iter(dataloader)
total = len(dataloader)

with tqdm(
    total=total,
    desc="Iterating over datasets",
) as pbar:
    for batch in it:
        pbar.update()

import logging

from tqdm import tqdm

from torchfont.datasets import GoogleFonts
from torchfont.transforms import (
    Compose,
    LimitSequenceLength,
    Patchify,
)

logging.getLogger("fontTools").setLevel(logging.ERROR)

transforms = Compose(
    (
        LimitSequenceLength(max_len=512),
        Patchify(patch_size=32),
    ),
)

dataset = GoogleFonts(
    root="data/google_fonts",
    ref="main",
    transform=transforms,
    download=True,
)

for i in tqdm(
    range(len(dataset)),
    desc="Iterating over dataset",
):
    sample = dataset[i]

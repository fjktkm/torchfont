import logging

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
        Patchify(),
        CloseFont(),
    ]
)

dataset = GoogleFonts(
    root="data/google_fonts",
    ref="main",
    download=True,
    transform=transforms,
)

for i in tqdm(
    range(len(dataset)),
    desc="Iterating over dataset",
):
    sample = dataset[i]

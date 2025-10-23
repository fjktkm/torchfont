import logging

from tqdm import tqdm

from torchfont.datasets import GoogleFonts

logging.getLogger("fontTools").setLevel(logging.ERROR)


dataset = GoogleFonts(
    root="data/google_fonts",
    ref="main",
    loader=lambda x, y, z: (x, y, z),
    download=True,
)

for i in tqdm(
    range(len(dataset)),
    desc="Iterating over dataset",
):
    sample = dataset[i]

from torchfont.datasets import GoogleFonts
from tqdm import tqdm

dataset = GoogleFonts(
    root="data/google_fonts",
    ref="main",
    download=True,
)

for i in tqdm(
    range(len(dataset)),
    desc="Iterating over dataset",
):
    sample = dataset[i]

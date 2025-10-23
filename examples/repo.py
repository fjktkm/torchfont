import logging

from torchfont.datasets import FontRepo

logging.getLogger("fontTools").setLevel(logging.ERROR)


dataset = FontRepo(
    root="data/source_han_sans",
    url="https://github.com/adobe-fonts/source-han-sans",
    ref="release",
    patterns=("Variable/TTF/*.ttf",),
    loader=lambda x, y, z: (x, y, z),
    download=True,
)

print(f"{len(dataset)=}")
print(f"{dataset.num_content_classes=}")
print(f"{dataset.num_style_classes=}")

for i in range(5):
    print(dataset[i])
